import inspect
import logging
from typing import Optional

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError

from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST


logger = logging.getLogger(__name__)


class AppExceptionCase(Exception):
    def __init__(self, status_code: int, context: Optional[dict]):
        super().__init__()

        self.exception_case = self.__class__.__name__
        self.status_code = status_code
        self.context = context

    def __str__(self):
        return (
            f"<AppException {self.exception_case} - "
            + f"status_code={self.status_code} - context={self.context}>"
        )


class RemoteServiceError(AppExceptionCase):
    def __init__(self, context: dict = None):
        """Remote service returned a 500 error to request."""
        status_code = 500
        AppExceptionCase.__init__(self, status_code, context)


class RequestError(AppExceptionCase):
    def __init__(self, context: dict = None):
        """Invalid request from user."""
        status_code = 400
        AppExceptionCase.__init__(self, status_code, context)


class AuthenticationError(AppExceptionCase):
    def __init__(self, context: dict = None):
        """Item is not public and requires auth."""
        status_code = 401
        AppExceptionCase.__init__(self, status_code, context)


class ResourceNotFoundError(AppExceptionCase):
    def __init__(self, context: dict = None):
        """The resource requested by the user does not exist."""
        status_code = 404
        AppExceptionCase.__init__(self, status_code, context)


class ResourceConflictError(AppExceptionCase):
    def __init__(self, context: dict = None):
        """The resource the user tried to create already exists."""
        status_code = 409
        AppExceptionCase.__init__(self, status_code, context)


def caller_info() -> str:
    info = inspect.getframeinfo(inspect.stack()[2][0])
    return f"{info.filename}:{info.function}:{info.lineno}"


# pylint: disable=unused-argument
async def app_exception_handler(request: Request, exc: AppExceptionCase):
    logger.error("%s | caller=%s", exc, caller_info())
    return JSONResponse(
        status_code=exc.status_code,
        content={"app_exception": exc.exception_case, "context": exc.context},
    )


# pylint: disable=unused-argument
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


# pylint: disable=unused-argument
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST, content={"detail": jsonable_encoder(exc.errors())}
    )
