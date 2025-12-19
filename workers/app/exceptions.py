# app/exceptions.py
from google.genai.errors import APIError


class ImpossibleTaskError(Exception):
    """
    Custom exception raised when a task encounters an impossible state or
    a condition that prevents it from completing successfully, even after retries.
    """
    pass


class RetriableGoogleAPIError(APIError):
    """Base class for Google API retry errors."""
    pass


class NonRetriableGoogleAPIError(APIError):
    """Base class for Google API non-retry errors."""
    pass


class BadRequest(NonRetriableGoogleAPIError):
    """HTTP status code 400."""
    pass


class ResourceExhausted(RetriableGoogleAPIError):
    """ HTTP status code 429 - the rate limit is exceeded."""
    pass


class Internal(NonRetriableGoogleAPIError):
    """HTTP status code 500 - the input context is too long."""
    pass


class ServiceUnavailable(RetriableGoogleAPIError):
    """HTTP status code 503 - the service may be temporarily overloaded or down."""
    pass


class DeadlineExceeded(RetriableGoogleAPIError):
    """HTTP status code 504 - The service is unable to finish processing within the deadline.
      For example, a prompt ( or context) is too large to be processed in time."""
    pass


non_retriable_google_api_errors = {
    400: BadRequest,
    500: Internal,
}


retriable_google_api_errors = {
    429: ResourceExhausted,
    503: ServiceUnavailable,
    504: DeadlineExceeded,
}
