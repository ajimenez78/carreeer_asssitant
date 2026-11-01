"""Public, content-free API diagnostics."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException

from career_assistant.ai import AIError


class AppError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, fields=None):
        super().__init__(message)
        self.code, self.status, self.fields = code, status, fields or {}


def error_response(code, message, status, fields=None):
    return JSONResponse(
        {"error": {"code": code, "message": message, "fields": fields or {}}},
        status_code=status,
    )


def register_errors(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    @app.exception_handler(AIError)
    async def application_error(request: Request, error):
        return error_response(
            error.code, str(error), error.status, getattr(error, "fields", None)
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error):
        # Pydantic's input/context may contain passwords or entire documents.
        fields = {
            ".".join(map(str, item["loc"])): item["type"] for item in error.errors()
        }
        return error_response(
            "validation_error", "Check the indicated fields.", 422, fields
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, error):
        return error_response(
            "http_error", "The request could not be processed.", error.status_code
        )

    @app.exception_handler(LookupError)
    async def missing(request: Request, error):
        return error_response(
            "not_found", "Save a definition first, or check the requested record.", 404
        )

    @app.exception_handler(IntegrityError)
    async def conflict(request: Request, error):
        return error_response(
            "write_conflict",
            "The data changed or violates a constraint. Reload and retry.",
            409,
        )

    @app.exception_handler(SQLAlchemyError)
    async def unavailable(request: Request, error):
        return error_response(
            "database_unavailable",
            "Database operation failed. Reload to check saved state, then retry.",
            503,
        )
