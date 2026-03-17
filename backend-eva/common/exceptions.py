"""Domain exception classes for the EVA platform."""


class DomainError(Exception):
    """Base domain error. All domain exceptions inherit from this."""

    status_code: int = 400
    code: str = "domain_error"

    def __init__(self, detail: str = "A domain error occurred", **kwargs):
        self.detail = detail
        self.errors: list[dict] = kwargs.get("errors", [])
        super().__init__(detail)


class DuplicateEmailError(DomainError):
    status_code = 409
    code = "duplicate_email"

    def __init__(self, detail: str = "A user with this email already exists"):
        super().__init__(detail)


class InvalidCredentialsError(DomainError):
    status_code = 401
    code = "invalid_credentials"

    def __init__(self, detail: str = "Invalid email or password"):
        super().__init__(detail)


class InsufficientRoleError(DomainError):
    status_code = 403
    code = "insufficient_role"

    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(detail)


class NotEnrolledError(DomainError):
    status_code = 403
    code = "not_enrolled"

    def __init__(self, detail: str = "You are not enrolled in this course"):
        super().__init__(detail)


class CourseNotPublishedError(DomainError):
    status_code = 400
    code = "course_not_published"

    def __init__(self, detail: str = "This course is not published"):
        super().__init__(detail)


class PublishValidationError(DomainError):
    status_code = 422
    code = "publish_validation_failed"

    def __init__(self, detail: str = "Course failed publish validation", **kwargs):
        super().__init__(detail, **kwargs)


class RateLimitExceededError(DomainError):
    status_code = 429
    code = "rate_limit_exceeded"

    def __init__(self, detail: str = "Too many requests", retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(detail)


class FileTooLargeError(DomainError):
    status_code = 413
    code = "file_too_large"

    def __init__(self, detail: str = "File exceeds the maximum allowed size"):
        super().__init__(detail)


class TooManyFilesError(DomainError):
    status_code = 400
    code = "too_many_files"

    def __init__(self, detail: str = "Too many files uploaded"):
        super().__init__(detail)
