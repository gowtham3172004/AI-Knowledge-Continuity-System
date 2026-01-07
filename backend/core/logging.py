"""
Logging configuration for FastAPI backend.

Sets up structured logging for API requests and responses.
"""

import logging
import sys
from typing import Optional

import structlog
from structlog.typing import Processor


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure structured logging for the API.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure standard logging
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=getattr(logging, log_level.upper()),
        stream=sys.stdout,
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


class APILogger:
    """
    Structured logger for API operations.
    
    Provides consistent logging format for requests, responses, and errors.
    """
    
    def __init__(self, name: str):
        self._logger = logging.getLogger(name)
    
    def request(
        self,
        method: str,
        path: str,
        request_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log incoming request."""
        self._logger.info(
            f"REQUEST | {method} {path} | request_id={request_id}",
            extra={"request_id": request_id, **kwargs}
        )
    
    def response(
        self,
        status_code: int,
        request_id: Optional[str] = None,
        method: Optional[str] = None,
        path: Optional[str] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ) -> None:
        """Log outgoing response."""
        duration_str = f" | duration={duration_ms:.2f}ms" if duration_ms else ""
        path_str = f" {method} {path} |" if method and path else ""
        self._logger.info(
            f"RESPONSE |{path_str} status={status_code}{duration_str}",
            extra={"request_id": request_id, "status_code": status_code, **kwargs}
        )
    
    def error(
        self,
        error: Exception,
        request_id: Optional[str] = None,
        message: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log error."""
        msg = message or str(error)
        self._logger.error(
            f"ERROR | {msg} | error={error}",
            extra={"request_id": request_id, "error": str(error), **kwargs},
            exc_info=error is not None
        )
    
    def knowledge_gap(
        self,
        query: str,
        confidence_score: float,
        severity: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> None:
        """Log knowledge gap detection."""
        self._logger.warning(
            f"KNOWLEDGE_GAP | confidence={confidence_score:.2f} | severity={severity} | query={query[:50]}...",
            extra={
                "request_id": request_id,
                "confidence": confidence_score,
                "severity": severity,
                "query": query
            }
        )
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._logger.warning(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._logger.debug(message, extra=kwargs)
