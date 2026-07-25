class AppException(Exception):
    def __init__(self, message, status_code=500, errors=None, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors or {}
        self.details = details


class ValidationError(AppException):
    def __init__(self, message='Validation failed', errors=None, details=None):
        super().__init__(message, 400, errors, details)


class AuthenticationError(AppException):
    def __init__(self, message='Authentication failed', errors=None):
        super().__init__(message, 401, errors)


class AuthorizationError(AppException):
    def __init__(self, message='Insufficient permissions', errors=None):
        super().__init__(message, 403, errors)


class NotFoundError(AppException):
    def __init__(self, message='Resource not found', errors=None):
        super().__init__(message, 404, errors)


class ConflictError(AppException):
    def __init__(self, message='Resource conflict', errors=None):
        super().__init__(message, 409, errors)


class RateLimitError(AppException):
    def __init__(self, message='Rate limit exceeded', errors=None):
        super().__init__(message, 429, errors)


class InternalError(AppException):
    def __init__(self, message='Internal server error', errors=None):
        super().__init__(message, 500, errors)