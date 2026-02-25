"""
FastAPI Application Entry Point.

Production-grade FastAPI backend for the AI Knowledge Continuity System.
Provides REST API access to the RAG-based knowledge management system.
"""

import sys
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend import __version__
from backend.core.config import api_settings
from backend.core.logging import setup_logging, get_logger, APILogger
from backend.core.exceptions import (
    APIException,
    ValidationError,
    KnowledgeGapError,
    RAGServiceError,
    TimeoutError,
    ServiceUnavailableError,
)
from backend.core.lifecycle import ApplicationState, lifespan
from backend.api.routes import query_router, ingest_router, health_router
from backend.api.routes.documents import router as documents_router
from backend.api.routes.dashboard import router as dashboard_router
from backend.api.routes.conversations import router as conversations_router
from backend.api.routes.health import set_startup_time
from backend.db import init_db


# Setup logging
setup_logging()
logger = get_logger(__name__)
api_logger = APILogger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    
    app = FastAPI(
        title="AI Knowledge Continuity System API",
        description="""
        ## Enterprise Knowledge Management API
        
        A RAG-based system for preserving and accessing organizational knowledge.
        
        ### Features
        
        - **Tacit Knowledge Extraction**: Surfaces experiential knowledge from 
          lessons learned, retrospectives, and exit interviews.
        
        - **Decision Traceability**: Provides full context for decisions including 
          rationale, alternatives, and trade-offs.
        
        - **Knowledge Gap Detection**: Automatically identifies gaps in the 
          knowledge base and flags low-confidence responses.
        
        ### Authentication
        
        Admin endpoints (ingestion) require an API key passed via the 
        `X-API-Key` header.
        
        ### Rate Limiting
        
        Default rate limit: 100 requests per minute per IP.
        """,
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # Configure CORS — allow all origins.
    # Auth uses Bearer tokens (not cookies), so allow_credentials is not needed.
    # This ensures CORS headers are present on ALL responses, including 500 errors.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    
    # Initialize database
    init_db()
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Register routes
    app.include_router(documents_router, prefix="/api")
    app.include_router(dashboard_router, prefix="/api")
    app.include_router(conversations_router, prefix="/api")
    app.include_router(query_router, prefix="/api")
    app.include_router(ingest_router, prefix="/api")
    app.include_router(health_router, prefix="/api")
    
    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "AI Knowledge Continuity System API",
            "version": __version__,
            "docs": "/docs",
            "health": "/api/health",
        }
    
    logger.info(
        "FastAPI application created",
        extra={
            "version": __version__,
            "cors_origins": api_settings.CORS_ORIGINS,
        }
    )
    
    return app


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register custom exception handlers.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(APIException)
    async def api_exception_handler(
        request: Request,
        exc: APIException,
    ) -> JSONResponse:
        """Handle custom API exceptions."""
        api_logger.error(exc, request_id=getattr(request.state, "request_id", None))
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )
    
    @app.exception_handler(ValidationError)
    async def validation_error_handler(
        request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        """Handle validation errors."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )
    
    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {"errors": errors},
                }
            },
        )
    
    @app.exception_handler(KnowledgeGapError)
    async def knowledge_gap_handler(
        request: Request,
        exc: KnowledgeGapError,
    ) -> JSONResponse:
        """Handle knowledge gap errors (returns 200 with gap info)."""
        api_logger.knowledge_gap(
            query=exc.details.get("query", "unknown"),
            confidence_score=exc.details.get("confidence_score", 0.0),
            severity=exc.details.get("severity"),
        )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "answer": exc.details.get("partial_answer", ""),
                "knowledge_gap": {
                    "detected": True,
                    "severity": exc.details.get("severity"),
                    "confidence_score": exc.details.get("confidence_score", 0.0),
                    "reason": exc.message,
                },
                "warnings": [exc.message],
            },
        )
    
    @app.exception_handler(TimeoutError)
    async def timeout_handler(
        request: Request,
        exc: TimeoutError,
    ) -> JSONResponse:
        """Handle timeout errors."""
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )
    
    @app.exception_handler(ServiceUnavailableError)
    async def service_unavailable_handler(
        request: Request,
        exc: ServiceUnavailableError,
    ) -> JSONResponse:
        """Handle service unavailable errors."""
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
            headers={"Retry-After": "30"},
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle unexpected exceptions with CORS safety net."""
        logger.exception(f"Unhandled exception: {exc}")
        
        # Always include CORS headers as a safety net for error responses
        headers = {"Access-Control-Allow-Origin": "*"}
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {"type": type(exc).__name__, "message": str(exc)[:200]},
                }
            },
            headers=headers,
        )


# Create application instance
app = create_app()


def main():
    """Run the application with uvicorn."""
    import uvicorn
    
    set_startup_time()
    
    uvicorn.run(
        "backend.main:app",
        host=api_settings.API_HOST,
        port=api_settings.API_PORT,
        reload=api_settings.DEBUG,
        log_level="info" if api_settings.DEBUG else "warning",
        access_log=api_settings.DEBUG,
    )


if __name__ == "__main__":
    main()
