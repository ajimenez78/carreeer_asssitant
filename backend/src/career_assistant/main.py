from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from career_assistant.api.health import router as health_router
from career_assistant.config import Settings

INDEX_FILE = Path(__file__).parent / "static" / "index.html"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else Settings()
    application = FastAPI(title=settings.app_name, version="0.1.0")
    application.include_router(health_router)

    @application.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(INDEX_FILE)

    return application


app = create_app()
