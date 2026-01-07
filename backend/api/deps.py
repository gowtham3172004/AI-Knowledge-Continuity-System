"""
Dependency injection for API routes.

Provides FastAPI dependencies for injecting services
and shared resources into route handlers.
"""

from typing import Generator, Optional

from fastapi import Depends, Header, HTTPException, Request, status

from backend.core.config import api_settings
from backend.core.exceptions import ServiceUnavailableError
from backend.services.rag_service import RAGService
from backend.services.ingest_service import IngestService
from backend.services.validation_service import ValidationService, get_validation_service


# Type aliases for cleaner annotations
ValidationServiceDep = ValidationService


async def get_app_state(request: Request):
    """
    Get application state from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        ApplicationState instance
        
    Raises:
        ServiceUnavailableError: If app state not initialized
    """
    state = request.app.state
    
    if not hasattr(state, "app_state") or not state.app_state.is_ready:
        raise ServiceUnavailableError(
            message="Service not ready",
            details={"reason": "Application state not initialized"}
        )
    
    return state.app_state


async def get_rag_service(request: Request) -> RAGService:
    """
    Get RAG service dependency.
    
    Args:
        request: FastAPI request object
        
    Returns:
        RAGService instance
        
    Raises:
        ServiceUnavailableError: If RAG service not available
    """
    app_state = await get_app_state(request)
    
    if not hasattr(app_state, "rag_service") or app_state.rag_service is None:
        raise ServiceUnavailableError(
            message="RAG service not available",
            details={"reason": "RAG chain not initialized"}
        )
    
    return app_state.rag_service


async def get_ingest_service(request: Request) -> IngestService:
    """
    Get Ingestion service dependency.
    
    Args:
        request: FastAPI request object
        
    Returns:
        IngestService instance
        
    Raises:
        ServiceUnavailableError: If Ingest service not available
    """
    app_state = await get_app_state(request)
    
    if not hasattr(app_state, "ingest_service") or app_state.ingest_service is None:
        raise ServiceUnavailableError(
            message="Ingest service not available",
            details={"reason": "Ingestion pipeline not initialized"}
        )
    
    return app_state.ingest_service


def get_validation() -> ValidationService:
    """
    Get validation service dependency.
    
    Returns:
        ValidationService instance
    """
    return get_validation_service()


async def verify_admin_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    validation: ValidationService = Depends(get_validation),
) -> bool:
    """
    Verify admin API key for protected routes.
    
    Args:
        x_api_key: API key from header
        validation: Validation service
        
    Returns:
        True if valid
        
    Raises:
        HTTPException: If API key invalid or missing
    """
    if not api_settings.REQUIRE_ADMIN_KEY:
        return True
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "API key required",
                }
            },
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if not validation.validate_api_key(x_api_key, required=False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "Invalid API key",
                }
            },
        )
    
    return True


async def optional_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    validation: ValidationService = Depends(get_validation),
) -> bool:
    """
    Optionally verify API key (doesn't require it).
    
    Args:
        x_api_key: API key from header
        validation: Validation service
        
    Returns:
        True if valid, False if not provided
    """
    if not x_api_key:
        return False
    
    return validation.validate_api_key(x_api_key, required=False)


# Common dependency type hints for route definitions
RAGServiceDep = RAGService
IngestServiceDep = IngestService
AdminKeyDep = bool
