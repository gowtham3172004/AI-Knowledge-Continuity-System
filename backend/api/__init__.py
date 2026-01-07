"""
API package.

Exports dependencies and route registration utilities.
"""

from .deps import (
    get_rag_service,
    get_ingest_service,
    get_validation,
    verify_admin_api_key,
    optional_api_key,
)

from .routes import (
    query_router,
    ingest_router,
    health_router,
)


__all__ = [
    # Dependencies
    "get_rag_service",
    "get_ingest_service",
    "get_validation",
    "verify_admin_api_key",
    "optional_api_key",
    # Routers
    "query_router",
    "ingest_router",
    "health_router",
]
