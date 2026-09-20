from enum import Enum
from enum import StrEnum


class ErrorCode(StrEnum):
    UNAUTHORIZED = "UNAUTHORIZED"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    HTTP_ERROR = "HTTP_ERROR"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"


class AuthProvider(Enum):
    google = "google"
    github = "github"
