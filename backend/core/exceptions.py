"""
Custom exceptions for FastAPI backend.

Provides typed exceptions that map to HTTP status codes.
"""

from typing import Any, Dict, Optional


class APIException(Exception):
    """
    Base exception for API errors.
    
    All API exceptions inherit from this class and define
    their HTTP status code and error code.
    """
    
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.details = details or {}
        if status_code:
            self.status_code = status_code
        if error_code:
            self.error_code = error_code
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to API response dict."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details
            }
        }


class ValidationError(APIException):
    """Request validation failed."""
    status_code = 422
    error_code = "VALIDATION_ERROR"


class NotFoundError(APIException):
    """Requested resource not found."""
    status_code = 404
    error_code = "NOT_FOUND"


class UnauthorizedError(APIException):
    """Authentication required or failed."""
    status_code = 401
    error_code = "UNAUTHORIZED"


class ForbiddenError(APIException):
    """Access denied."""
    status_code = 403
    error_code = "FORBIDDEN"


class RateLimitError(APIException):
    """Rate limit exceeded."""
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"


class ServiceUnavailableError(APIException):
    """Service temporarily unavailable."""
    status_code = 503
    error_code = "SERVICE_UNAVAILABLE"


class KnowledgeGapError(APIException):
    """
    Knowledge gap detected - insufficient information to answer.
    
    This is a special case where we return 200 OK but with
    gap_detected=True in the response body.
    """
    status_code = 200  # Not an error, but a valid response state
    error_code = "KNOWLEDGE_GAP_DETECTED"
    
    def __init__(
        self,
        message: str,
        confidence: float,
        severity: str,
        safe_response: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details)
        self.confidence = confidence
        self.severity = severity
        self.safe_response = safe_response


class RAGServiceError(APIException):
    """Error in RAG service layer."""
    status_code = 500
    error_code = "RAG_SERVICE_ERROR"


class IngestionError(APIException):
    """Error during document ingestion."""
    status_code = 500
    error_code = "INGESTION_ERROR"


class TimeoutError(APIException):
    """Operation timed out."""
    status_code = 504
    error_code = "TIMEOUT"


class ConfigurationError(APIException):
    """Configuration error."""
    status_code = 500
    error_code = "CONFIGURATION_ERROR"
