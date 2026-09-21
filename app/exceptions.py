from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StareletteHttpException
from app.schemas.error import ErrorDetail, ErrorResponse
from app.utils.types import ErrorCode
import logging

logger = logging.getLogger(__name__)


async def fhttp_exception_handler(_: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        code = exc.detail.get("code", ErrorCode.HTTP_ERROR)
        message = exc.detail.get("message", str(exc.detail))
    else:
        code = ErrorCode.HTTP_ERROR
        message = str(exc.detail)
    response = ErrorResponse(error=ErrorDetail(code=code, message=message))
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(), headers=exc.headers
    )


async def shttp_exception_handler(_: Request, exc: StareletteHttpException):
    if exc.status_code == 404:
        code = ErrorCode.NOT_FOUND
    elif exc.status_code == 405:
        code = ErrorCode.METHOD_NOT_ALLOWED
    else:
        code = ErrorCode.HTTP_ERROR
    response = ErrorResponse(error=ErrorDetail(code=code, message=str(exc.detail)))
    return JSONResponse(
        status_code=exc.status_code, content=response.model_dump(), headers=exc.headers
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError):
    errors_dict={}
    for error in exc.errors():
        loc=error["loc"]
        errors_dict[str(loc[-1])] = error["msg"]
    
    response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCode.VALIDATION_ERROR,
            message="Request Validation Failed",
            details=errors_dict,
        )
    )
    return JSONResponse(
        status_code=422,
        content=response.model_dump(),
    )


async def internal_server_error_handler(
    _: Request,
    exc: Exception,
):
    logger.exception("Unhandled exception", exc_info=exc)
    response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            message="An unexpected error occurred",
        )
    )

    return JSONResponse(
        status_code=500,
        content=response.model_dump(),
    )
