import logging
from typing import Any, Callable

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, StarletteHTTPException, ValidationError
from fastapi.responses import JSONResponse

from financial.api.base import InternalServerError, ProbeError
from financial.apps.financial.schemas import StatsResponse


logger = logging.getLogger(__name__)


def error_response(status_code: int, response_model: Any, message: str) -> JSONResponse:
    content = response_model(info={"error": message})
    return JSONResponse(status_code=status_code, content=jsonable_encoder(content))


def default_error_handler_creator(resp_status: int) -> Callable:  # pylint: disable=unused-argument
    """
    Catches and formats all default errors.
    """

    async def default_error_handler(request: Request, exc: Exception) -> JSONResponse:
        if "route" in request.scope:
            response_model = request.scope["route"].response_model
        else:
            response_model = StatsResponse

        if isinstance(exc, (RequestValidationError, ValidationError)):
            message = "; ".join([f"{'.'.join(err['loc'])}: {err['msg']}" for err in exc.errors()])  # type: ignore
            return error_response(resp_status, response_model, message=message)

        if isinstance(exc, StarletteHTTPException):
            return error_response(exc.status_code, response_model, message=exc.detail)

        return error_response(resp_status, response_model, message=str(exc))

    return default_error_handler


def setup_exceptions(application: FastAPI) -> None:
    """
    Catches all exceptions from exc_pairs list to create standard response format.
    All new exceptions should be added here.
    """
    exc_pairs = [
        (InternalServerError, default_error_handler_creator(status.HTTP_500_INTERNAL_SERVER_ERROR)),
        (ProbeError, default_error_handler_creator(status.HTTP_503_SERVICE_UNAVAILABLE)),
        (RequestValidationError, default_error_handler_creator(status.HTTP_422_UNPROCESSABLE_ENTITY)),
        (ValidationError, default_error_handler_creator(status.HTTP_422_UNPROCESSABLE_ENTITY)),
        (StarletteHTTPException, default_error_handler_creator(status.HTTP_422_UNPROCESSABLE_ENTITY)),
    ]

    for err, handler in exc_pairs:
        application.add_exception_handler(err, handler)
