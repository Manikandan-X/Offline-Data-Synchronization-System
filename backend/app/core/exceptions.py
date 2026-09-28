from typing import Any
from app.core.logging import get_logger
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = get_logger(__name__)


class AppException(Exception):
    """
    Base application exception.
    """

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        self.message = message
        self.status_code = status_code

        super().__init__(message)
        
class BadRequestException(AppException):
    """
    Raised when the request is valid in structure
    but cannot be processed because of invalid input
    or a business rule violation.
    """

    def __init__(
        self,
        message: str = "Bad request",
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class NotFoundException(AppException):
    """
    Raised when a requested resource does not exist.
    """

    def __init__(
        self,
        message: str = "Resource not found",
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class UnauthorizedException(AppException):
    """
    Raised when authentication is required or invalid.
    """

    def __init__(
        self,
        message: str = "Authentication required",
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class ForbiddenException(AppException):
    """
    Raised when the authenticated user does not
    have permission to perform an action.
    """

    def __init__(
        self,
        message: str = "Access forbidden",
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )
        
class ConflictException(AppException):
    """
    Raised when the requested operation conflicts
    with the current server state.
    """

    def __init__(
        self,
        message: str = "Resource conflict",
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
        )


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """
    Handle known application exceptions.
    """

    logger.warning(
        "Application exception: method=%s path=%s status=%s message=%s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.message,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle request validation errors.
    """

    logger.warning(
        "Request validation failed: method=%s path=%s",
        request.method,
        request.url.path,
    )

    errors: list[dict[str, Any]] = []

    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(
                    str(location)
                    for location in error["loc"]
                    if location != "body"
                ),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed",
            "errors": errors,
        },
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """
    Handle unexpected database errors.
    """

    logger.error(
        "Database error: method=%s path=%s error=%s",
        request.method,
        request.url.path,
        str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "A database error occurred",
        },
    )


async def general_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle unexpected application errors.
    """

    logger.error(
        "Unhandled application error: method=%s path=%s error=%s",
        request.method,
        request.url.path,
        str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred",
        },
    )

