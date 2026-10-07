"""Centralized domain exceptions and error handling schemas."""

from typing import Any, Optional


class AppException(Exception):
    """Base application exception for all domain errors."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
        details: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class NotFoundError(AppException):
    def __init__(
        self,
        message: str = "Resource not found",
        code: str = "NOT_FOUND",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=404, details=details)


class AuthenticationError(AppException):
    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "UNAUTHORIZED",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=401, details=details)


class ForbiddenError(AppException):
    def __init__(
        self,
        message: str = "Permission denied",
        code: str = "FORBIDDEN",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=403, details=details)


class ConflictError(AppException):
    def __init__(
        self,
        message: str = "Resource conflict",
        code: str = "CONFLICT",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=409, details=details)


class BadRequestError(AppException):
    def __init__(
        self,
        message: str = "Invalid request",
        code: str = "BAD_REQUEST",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=400, details=details)


class ValidationError(AppException):
    def __init__(
        self,
        message: str = "Validation failed",
        code: str = "VALIDATION_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=422, details=details)


class ServiceUnavailableError(AppException):
    def __init__(
        self,
        message: str = "Service unavailable",
        code: str = "SERVICE_UNAVAILABLE",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=503, details=details)


class AIProcessingError(AppException):
    def __init__(
        self,
        message: str = "AI service error",
        code: str = "AI_SERVICE_ERROR",
        details: Optional[Any] = None,
    ):
        super().__init__(message=message, code=code, status_code=502, details=details)
