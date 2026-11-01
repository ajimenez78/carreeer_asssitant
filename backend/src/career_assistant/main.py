from contextlib import asynccontextmanager
from pathlib import Path
from secrets import token_urlsafe

from fastapi import FastAPI
from fastapi.responses import FileResponse
from sqlalchemy.orm import sessionmaker
from starlette.middleware.sessions import SessionMiddleware

from career_assistant.api.definitions import router as definitions_router
from career_assistant.api.health import router as health_router
from career_assistant.auth import SESSION_SECONDS
from career_assistant.auth import router as session_router
from career_assistant.boundary import RequestBoundary
from career_assistant.config import Settings
from career_assistant.database import database_engine, database_url
from career_assistant.documents import SourceProcessor
from career_assistant.errors import register_errors

INDEX_FILE = Path(__file__).parent / "static" / "index.html"


def create_app(
    settings: Settings | None = None,
    *,
    sessions=None,
    ai_client=None,
    store=None,
    processor=None,
) -> FastAPI:
    settings = settings if settings is not None else Settings()
    engine = database_engine(database_url(settings)) if sessions is None else None

    @asynccontextmanager
    async def lifespan(app):
        yield
        if engine is not None:
            engine.dispose()

    application = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    application.state.settings = settings
    application.state.sessions = (
        sessions
        if sessions is not None
        else sessionmaker(engine, expire_on_commit=False)
    )
    application.state.ai_client = ai_client
    application.state.store = store
    application.state.processor = processor or SourceProcessor()
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret.get_secret_value()
        if settings.session_secret
        and len(settings.session_secret.get_secret_value()) >= 32
        else token_urlsafe(32),
        session_cookie="career_session",
        max_age=SESSION_SECONDS,
        same_site="strict",
        https_only=settings.session_secure,
    )
    application.add_middleware(
        RequestBoundary, allowed_origins=settings.allowed_origins
    )
    register_errors(application)
    application.include_router(health_router)
    application.include_router(session_router)
    application.include_router(definitions_router)

    @application.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(INDEX_FILE)

    return application


app = create_app()
