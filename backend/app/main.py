from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.router import api_router
from app.core.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(title=settings.app_name, version="0.1.0")
    register_exception_handlers(application)
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
