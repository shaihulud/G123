from fastapi import FastAPI

from financial.api.base import router as base_router
from financial.apps.financial.api.views import router as financial_router
from financial.config import settings
from financial.exceptions import setup_exceptions
from financial.logging import configure_logging


def setup_routers(application: FastAPI) -> None:
    application.include_router(financial_router, prefix="/api", tags=["urls"])
    application.include_router(base_router, tags=["probe"])


def get_app(app_name: str) -> FastAPI:
    application = FastAPI(
        title=app_name,
        root_path=settings.ROOT_PATH,
        debug=settings.DEBUG,
    )

    configure_logging()
    setup_exceptions(application)
    setup_routers(application)
    return application


app = get_app(app_name=settings.SERVICE_NAME)
