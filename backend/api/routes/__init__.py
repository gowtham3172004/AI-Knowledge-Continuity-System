"""
API routes package.

Exports all route modules for registration with the main app.
"""

from .query import router as query_router
from .ingest import router as ingest_router
from .health import router as health_router


__all__ = [
    "query_router",
    "ingest_router",
    "health_router",
]
