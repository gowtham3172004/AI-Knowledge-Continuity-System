"""
Pydantic schemas for the API.

Exports all schema models for use in route definitions.
"""

from .query import (
    KnowledgeType,
    QueryRole,
    QueryRequest,
    QueryResponse,
    QueryErrorResponse,
    SourceDocument,
    DecisionTrace,
    KnowledgeGapInfo,
)

from .knowledge_gap import (
    GapSeverity,
    GapCategory,
    KnowledgeGapDetail,
    KnowledgeGapReportResponse,
    GapAcknowledgeRequest,
    GapAcknowledgeResponse,
)

from .ingest import (
    IngestSource,
    DocumentMetadata,
    IngestRequest,
    IngestResponse,
    IngestDocumentResult,
    IngestStatusResponse,
)

from .health import (
    ComponentHealth,
    HealthResponse,
    ReadinessResponse,
    LivenessResponse,
    SystemInfoResponse,
)


__all__ = [
    # Query schemas
    "KnowledgeType",
    "QueryRole",
    "QueryRequest",
    "QueryResponse",
    "QueryErrorResponse",
    "SourceDocument",
    "DecisionTrace",
    "KnowledgeGapInfo",
    # Knowledge gap schemas
    "GapSeverity",
    "GapCategory",
    "KnowledgeGapDetail",
    "KnowledgeGapReportResponse",
    "GapAcknowledgeRequest",
    "GapAcknowledgeResponse",
    # Ingest schemas
    "IngestSource",
    "DocumentMetadata",
    "IngestRequest",
    "IngestResponse",
    "IngestDocumentResult",
    "IngestStatusResponse",
    # Health schemas
    "ComponentHealth",
    "HealthResponse",
    "ReadinessResponse",
    "LivenessResponse",
    "SystemInfoResponse",
]
