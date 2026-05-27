"""
Custom exception classes for better error handling and debugging.
"""
from typing import Optional


class TicketRouterException(Exception):
    """Base exception for Ticket Router"""
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        retryable: bool = False,
        details: Optional[dict] = None
    ):
        self.message = message
        self.error_code = error_code
        self.retryable = retryable
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert exception to dict for API response"""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


class HuggingFaceAPIError(TicketRouterException):
    """Error from Hugging Face API"""
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        retryable: bool = False,
        details: Optional[dict] = None
    ):
        self.status_code = status_code
        error_code = self._determine_error_code(status_code)
        super().__init__(
            message=message,
            error_code=error_code,
            retryable=retryable,
            details=details or {}
        )

    @staticmethod
    def _determine_error_code(status_code: Optional[int]) -> str:
        """Determine error code from HTTP status"""
        if status_code == 401:
            return "HF_UNAUTHORIZED"
        elif status_code == 429:
            return "HF_RATE_LIMITED"
        elif status_code == 500:
            return "HF_SERVER_ERROR"
        elif status_code == 503:
            return "HF_SERVICE_UNAVAILABLE"
        elif status_code and 500 <= status_code < 600:
            return "HF_SERVER_ERROR"
        return "HF_API_ERROR"


class APITimeoutError(TicketRouterException):
    """Timeout when calling external API"""
    def __init__(self, message: str = "API request timed out", details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="API_TIMEOUT",
            retryable=True,
            details=details
        )


class APIConnectionError(TicketRouterException):
    """Connection error when calling external API"""
    def __init__(self, message: str = "Failed to connect to API", details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="API_CONNECTION_ERROR",
            retryable=True,
            details=details
        )


class InvalidInputError(TicketRouterException):
    """Invalid input provided"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="INVALID_INPUT",
            retryable=False,
            details=details
        )


class ProcessingError(TicketRouterException):
    """Error during ticket processing"""
    def __init__(
        self,
        message: str,
        retryable: bool = False,
        details: Optional[dict] = None
    ):
        super().__init__(
            message=message,
            error_code="PROCESSING_ERROR",
            retryable=retryable,
            details=details
        )
