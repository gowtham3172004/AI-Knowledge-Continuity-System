"""
Core module for FastAPI backend.

Provides configuration, logging, exceptions, and lifecycle management.
"""

from backend.core.config import APISettings, get_api_settings
from backend.core.logging import setup_logging, get_logger, APILogger
from backend.core.exceptions import (
    APIException,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    RateLimitError,
    ServiceUnavailableError,
    KnowledgeGapError,
    RAGServiceError,
    IngestionError,
    TimeoutError,
    ConfigurationError,
)
from backend.core.lifecycle import lifespan, get_app_state, ApplicationState

__all__ = [
    # Config
    "APISettings",
    "get_api_settings",
    # Logging
    "setup_logging",
    "get_logger",
    "APILogger",
    # Exceptions
    "APIException",
    "ValidationError",
    "NotFoundError",
    "UnauthorizedError",
    "ForbiddenError",
    "RateLimitError",
    "ServiceUnavailableError",
    "KnowledgeGapError",
    "RAGServiceError",
    "IngestionError",
    "TimeoutError",
    "ConfigurationError",
    # Lifecycle
    "lifespan",
    "get_app_state",
    "ApplicationState",
]
