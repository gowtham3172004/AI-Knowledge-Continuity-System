"""
Pydantic schemas for health check endpoints.

Defines response models for system health and readiness checks.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ComponentHealth(BaseModel):
    """Health status of a single component."""
    
    name: str = Field(description="Component name")
    status: str = Field(description="Status (healthy, degraded, unhealthy)")
    latency_ms: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Response latency in milliseconds"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional details"
    )


class HealthResponse(BaseModel):
    """
    Response for health check endpoint.
    
    Provides comprehensive system health information.
    """
    
    status: str = Field(
        description="Overall status (healthy, degraded, unhealthy)"
    )
    
    version: str = Field(description="API version")
    
    components: Dict[str, ComponentHealth] = Field(
        default_factory=dict,
        description="Health of individual components"
    )
    
    uptime_seconds: float = Field(ge=0.0, description="System uptime")
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "components": {
                    "vector_store": {
                        "name": "vector_store",
                        "status": "healthy",
                        "latency_ms": 12.5,
                        "details": {"index_size": 150}
                    },
                    "llm": {
                        "name": "llm",
                        "status": "healthy",
                        "latency_ms": 250.0,
                        "details": {"model": "gemini-2.5-flash"}
                    }
                },
                "uptime_seconds": 3600.0,
                "timestamp": "2026-01-07T12:00:00Z"
            }
        }


class ReadinessResponse(BaseModel):
    """Response for readiness check endpoint."""
    
    ready: bool = Field(description="Whether system is ready to serve requests")
    reason: Optional[str] = Field(
        default=None,
        description="Reason if not ready"
    )


class LivenessResponse(BaseModel):
    """Response for liveness check endpoint."""
    
    alive: bool = Field(default=True, description="Whether system is alive")


class SystemInfoResponse(BaseModel):
    """Response for system information endpoint."""
    
    api_version: str = Field(description="API version")
    python_version: str = Field(description="Python version")
    
    features: Dict[str, bool] = Field(
        default_factory=dict,
        description="Enabled features"
    )
    
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="System statistics"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "api_version": "1.0.0",
                "python_version": "3.12.0",
                "features": {
                    "tacit_knowledge": True,
                    "decision_traceability": True,
                    "knowledge_gap_detection": True
                },
                "statistics": {
                    "total_documents": 5,
                    "total_chunks": 150,
                    "queries_served": 1234
                }
            }
        }
