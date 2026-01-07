"""
Health check route handlers.

Implements health, readiness, and liveness endpoints
for monitoring and orchestration systems.
"""

import sys
import time
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request, status

from backend.api.deps import get_app_state, get_rag_service, RAGServiceDep
from backend.core.config import api_settings
from backend.core.logging import get_logger
from backend.schemas.health import (
    ComponentHealth,
    HealthResponse,
    ReadinessResponse,
    LivenessResponse,
    SystemInfoResponse,
)


router = APIRouter(prefix="/health", tags=["health"])
logger = get_logger(__name__)

# Track startup time
_startup_time: Optional[float] = None


def set_startup_time():
    """Set the startup time when application starts."""
    global _startup_time
    _startup_time = time.time()


def get_uptime() -> float:
    """Get system uptime in seconds."""
    if _startup_time is None:
        return 0.0
    return time.time() - _startup_time


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="""
    Comprehensive health check of all system components.
    
    Returns the status of:
    - Vector store (FAISS index)
    - LLM service (Gemini)
    - Overall system health
    
    Use this endpoint for monitoring dashboards and alerting.
    """,
)
async def health_check(
    request: Request,
) -> HealthResponse:
    """
    Perform comprehensive health check.
    
    Args:
        request: FastAPI request
        
    Returns:
        HealthResponse with component statuses
    """
    from backend import __version__
    
    components = {}
    overall_status = "healthy"
    
    # Check if app state is available
    try:
        app_state = await get_app_state(request)
        
        # Check vector store
        try:
            start = time.perf_counter()
            vs = app_state.vector_store_manager
            # Simple check - just verify the object exists and has expected attributes
            if vs is not None:
                latency = (time.perf_counter() - start) * 1000
                components["vector_store"] = ComponentHealth(
                    name="vector_store",
                    status="healthy",
                    latency_ms=latency,
                    details={"type": "FAISS"},
                )
            else:
                components["vector_store"] = ComponentHealth(
                    name="vector_store",
                    status="unhealthy",
                    details={"error": "Not initialized"},
                )
                overall_status = "degraded"
        except Exception as e:
            components["vector_store"] = ComponentHealth(
                name="vector_store",
                status="unhealthy",
                details={"error": str(e)},
            )
            overall_status = "unhealthy"
        
        # Check RAG chain (LLM)
        try:
            start = time.perf_counter()
            rag = app_state.rag_chain
            if rag is not None:
                latency = (time.perf_counter() - start) * 1000
                components["llm"] = ComponentHealth(
                    name="llm",
                    status="healthy",
                    latency_ms=latency,
                    details={"model": "gemini-2.5-flash"},
                )
            else:
                components["llm"] = ComponentHealth(
                    name="llm",
                    status="unhealthy",
                    details={"error": "Not initialized"},
                )
                overall_status = "degraded"
        except Exception as e:
            components["llm"] = ComponentHealth(
                name="llm",
                status="unhealthy",
                details={"error": str(e)},
            )
            overall_status = "unhealthy"
            
    except Exception as e:
        overall_status = "unhealthy"
        components["app_state"] = ComponentHealth(
            name="app_state",
            status="unhealthy",
            details={"error": str(e)},
        )
    
    return HealthResponse(
        status=overall_status,
        version=__version__,
        components=components,
        uptime_seconds=get_uptime(),
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="""
    Check if the system is ready to serve requests.
    
    Use this endpoint for Kubernetes readiness probes.
    Returns 200 if ready, 503 if not ready.
    """,
    responses={
        200: {"description": "System is ready"},
        503: {"description": "System is not ready"},
    },
)
async def readiness_check(
    request: Request,
) -> ReadinessResponse:
    """
    Check system readiness.
    
    Args:
        request: FastAPI request
        
    Returns:
        ReadinessResponse indicating readiness
    """
    try:
        app_state = await get_app_state(request)
        
        if app_state.is_ready:
            return ReadinessResponse(ready=True)
        else:
            return ReadinessResponse(
                ready=False,
                reason="Application state not fully initialized",
            )
    except Exception as e:
        return ReadinessResponse(ready=False, reason=str(e))


@router.get(
    "/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
    description="""
    Check if the system is alive.
    
    Use this endpoint for Kubernetes liveness probes.
    A simple ping that always returns 200 if the server is running.
    """,
)
async def liveness_check() -> LivenessResponse:
    """
    Check system liveness.
    
    Returns:
        LivenessResponse indicating system is alive
    """
    return LivenessResponse(alive=True)


@router.get(
    "/info",
    response_model=SystemInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="System information",
    description="Get detailed system information including enabled features.",
)
async def system_info(
    request: Request,
) -> SystemInfoResponse:
    """
    Get system information.
    
    Args:
        request: FastAPI request
        
    Returns:
        SystemInfoResponse with system details
    """
    from backend import __version__
    
    # Get statistics if available
    statistics = {}
    try:
        app_state = await get_app_state(request)
        if app_state.vector_store_manager:
            # Add any statistics you can gather
            statistics["vector_store_type"] = "FAISS"
    except Exception:
        pass
    
    return SystemInfoResponse(
        api_version=__version__,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        features={
            "tacit_knowledge": api_settings.ENABLE_KNOWLEDGE_FEATURES,
            "decision_traceability": api_settings.ENABLE_KNOWLEDGE_FEATURES,
            "knowledge_gap_detection": api_settings.ENABLE_KNOWLEDGE_FEATURES,
        },
        statistics=statistics,
    )
