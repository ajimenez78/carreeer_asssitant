"""Starlette signed cookies with revocable, expiring PostgreSQL sessions."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from pwdlib import PasswordHash
from pydantic import BaseModel, ConfigDict, Field, SecretStr
from sqlalchemy import delete, select

from career_assistant.errors import AppError
from career_assistant.models import Owner, OwnerSession

PASSWORDS = PasswordHash.recommended()
SESSION_SECONDS = 12 * 60 * 60
router = APIRouter(prefix="/api/session", tags=["Session"])


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=100)
    password: SecretStr = Field(min_length=1, max_length=1024)


def sessions(request: Request):
    return request.app.state.sessions


def require_owner(request: Request) -> None:
    identity = request.session.get("id")
    try:
        identity = UUID(identity) if isinstance(identity, str) else None
    except ValueError:
        identity = None
    if identity is not None:
        with sessions(request)() as session:
            active = session.get(OwnerSession, identity)
            if active is not None and active.expires_at > datetime.now(UTC):
                return
    request.session.clear()
    raise AppError("unauthenticated", "Sign in to access your definition.", 401)


@router.post("")
def login(data: Login, request: Request):
    secret = request.app.state.settings.session_secret
    if secret is None or len(secret.get_secret_value()) < 32:
        raise AppError(
            "login_not_configured",
            "Configure a backend session secret of at least 32 characters.",
            503,
        )
    now = datetime.now(UTC)
    with sessions(request).begin() as session:
        owner = session.scalar(select(Owner).where(Owner.id == 1).with_for_update())
        if owner is None or owner.password_hash is None:
            raise AppError(
                "login_not_configured",
                "Configure the owner using the owner command.",
                503,
            )
        if owner.locked_until is not None and owner.locked_until > now:
            raise AppError(
                "login_throttled",
                "Too many login attempts. Try again in 15 minutes.",
                429,
            )
        # Verify even when the username is incorrect, avoiding a timing oracle.
        valid = PASSWORDS.verify(data.password.get_secret_value(), owner.password_hash)
        valid = valid and data.username == owner.username
        if not valid:
            owner.failed_logins += 1
            if owner.failed_logins >= 5:
                owner.locked_until = now + timedelta(minutes=15)
                owner.failed_logins = 0
        else:
            owner.failed_logins = 0
            owner.locked_until = None
            session.execute(delete(OwnerSession).where(OwnerSession.expires_at <= now))
            previous = request.session.get("id")
            if previous:
                session.execute(
                    delete(OwnerSession).where(OwnerSession.id == UUID(previous))
                )
            active = OwnerSession(
                owner_id=1, expires_at=now + timedelta(seconds=SESSION_SECONDS)
            )
            session.add(active)
            session.flush()
            identity = str(active.id)
    if not valid:
        raise AppError(
            "invalid_credentials", "The username or password is incorrect.", 401
        )
    request.session.clear()
    request.session["id"] = identity
    return {"username": owner.username}


@router.get("", dependencies=[Depends(require_owner)])
def current_session():
    return {"authenticated": True}


@router.delete("", status_code=204, dependencies=[Depends(require_owner)])
def logout(request: Request):
    with sessions(request).begin() as session:
        session.execute(
            delete(OwnerSession).where(OwnerSession.id == UUID(request.session["id"]))
        )
    request.session.clear()
    return Response(status_code=204)
