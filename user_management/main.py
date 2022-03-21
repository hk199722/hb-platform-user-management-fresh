import logging.config

from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException

from user_management.core.config.logging import logging_config
from user_management.core.config.settings import get_settings
from user_management.core.firebase import init_identity_platform_app
from user_management.routers.capability import router as capabilities_router
from user_management.routers.client import router as clients_router
from user_management.routers.gcp_user import router as gcp_user_router


# Configuring Python logging.
logging.config.dictConfig(logging_config)


def create_app() -> FastAPI:
    """App factory function. Returns a FastAPI app ready to be served.

    Usage with Uvicorn:

        uvicorn --factory user_management.main:create_app --reload
    """
    settings = get_settings()

    init_identity_platform_app()

    # Initialize FastAPI app.
    app = FastAPI(title="Users Management")

    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=settings.cors_allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    from user_management.core.exceptions import (
        app_exception_handler,
        AppExceptionCase,
        http_exception_handler,
        request_validation_exception_handler,
    )

    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request, e):
        return await http_exception_handler(request, e)

    @app.exception_handler(RequestValidationError)
    async def custom_validation_exception_handler(request, e):
        return await request_validation_exception_handler(request, e)

    @app.exception_handler(AppExceptionCase)
    async def custom_app_exception_handler(request, e):
        return await app_exception_handler(request, e)

    api_router = APIRouter()
    api_router.include_router(clients_router, prefix="/clients", tags=["Clients"])
    api_router.include_router(gcp_user_router, prefix="/users", tags=["Users"])
    api_router.include_router(capabilities_router, prefix="/capabilities", tags=["Capabilities"])

    app.include_router(api_router, prefix="/api/v1")

    return app
