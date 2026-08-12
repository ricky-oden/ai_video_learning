import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.schemas import ApiErrorBody, ApiErrorResponse, ApiFieldError

logger = logging.getLogger(__name__)


def _response(status_code: int, body: ApiErrorBody) -> JSONResponse:
    payload = ApiErrorResponse(error=body)
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


async def validation_exception_handler(
    _request: Request, exception: RequestValidationError
) -> JSONResponse:
    field_errors = [
        ApiFieldError(
            field=".".join(str(part) for part in error["loc"]),
            message=error["msg"],
            type=error["type"],
        )
        for error in exception.errors()
    ]
    return _response(
        HTTPStatus.UNPROCESSABLE_ENTITY,
        ApiErrorBody(
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            field_errors=field_errors,
        ),
    )


async def http_exception_handler(
    _request: Request, exception: StarletteHTTPException
) -> JSONResponse:
    status_code = exception.status_code
    if status_code == HTTPStatus.NOT_FOUND:
        code = "NOT_FOUND"
        message = "Resource not found."
    else:
        code = f"HTTP_{status_code}"
        message = (
            HTTPStatus(status_code).phrase
            if status_code in HTTPStatus._value2member_map_
            else "Request failed."
        )
    return _response(status_code, ApiErrorBody(code=code, message=message))


async def database_exception_handler(request: Request, exception: SQLAlchemyError) -> JSONResponse:
    logger.exception(
        "Database operation failed for %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exception), exception, exception.__traceback__),
    )
    return _response(
        HTTPStatus.SERVICE_UNAVAILABLE,
        ApiErrorBody(code="DATABASE_UNAVAILABLE", message="Database is unavailable."),
    )


async def unexpected_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled exception for %s %s",
        request.method,
        request.url.path,
        exc_info=(type(exception), exception, exception.__traceback__),
    )
    return _response(
        HTTPStatus.INTERNAL_SERVER_ERROR,
        ApiErrorBody(code="INTERNAL_SERVER_ERROR", message="An unexpected error occurred."),
    )


def register_exception_handlers(application: FastAPI) -> None:
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.add_exception_handler(StarletteHTTPException, http_exception_handler)
    application.add_exception_handler(SQLAlchemyError, database_exception_handler)
    application.add_exception_handler(Exception, unexpected_exception_handler)
