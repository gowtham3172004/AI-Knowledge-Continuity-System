"""
Pydantic schemas for ingestion endpoints.

Defines request and response models for document ingestion.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class IngestSource(str, Enum):
    """Sources for document ingestion."""
    FILE_UPLOAD = "file_upload"
    DIRECTORY_SCAN = "directory_scan"
    URL = "url"
    TEXT = "text"


class DocumentMetadata(BaseModel):
    """Metadata for a document being ingested."""
    
    title: Optional[str] = Field(default=None, max_length=200)
    author: Optional[str] = Field(default=None, max_length=100)
    department: Optional[str] = Field(default=None, max_length=100)
    knowledge_type: Optional[str] = Field(
        default=None,
        description="Override for knowledge type classification"
    )
    tags: List[str] = Field(default_factory=list, max_length=20)
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tags."""
        return [tag.strip().lower() for tag in v if tag.strip()]


class IngestRequest(BaseModel):
    """
    Request model for document ingestion.
    
    Supports multiple ingestion modes: directory scan, file paths, or text content.
    """
    
    source: IngestSource = Field(
        default=IngestSource.DIRECTORY_SCAN,
        description="Ingestion source type"
    )
    
    # For directory scan
    directory_path: Optional[str] = Field(
        default=None,
        description="Path to directory for scanning"
    )
    
    # For specific files
    file_paths: Optional[List[str]] = Field(
        default=None,
        description="Specific file paths to ingest"
    )
    
    # For text content
    text_content: Optional[str] = Field(
        default=None,
        max_length=100000,
        description="Raw text content to ingest"
    )
    
    # Options
    metadata: Optional[DocumentMetadata] = Field(
        default=None,
        description="Metadata to apply to ingested documents"
    )
    
    force_reindex: bool = Field(
        default=False,
        description="Force reindexing even if documents exist"
    )
    
    chunk_size: int = Field(
        default=500,
        ge=100,
        le=2000,
        description="Chunk size for document splitting"
    )
    
    chunk_overlap: int = Field(
        default=100,
        ge=0,
        le=500,
        description="Overlap between chunks"
    )


class IngestDocumentResult(BaseModel):
    """Result for a single document ingestion."""
    
    source: str = Field(description="Document source path")
    status: str = Field(description="Ingestion status (success, failed, skipped)")
    chunks_created: int = Field(ge=0, description="Number of chunks created")
    knowledge_type: Optional[str] = Field(
        default=None,
        description="Detected knowledge type"
    )
    error: Optional[str] = Field(default=None, description="Error message if failed")


class IngestResponse(BaseModel):
    """
    Response model for ingestion endpoint.
    
    Provides detailed results of the ingestion process.
    """
    
    status: str = Field(description="Overall ingestion status")
    
    total_documents: int = Field(ge=0, description="Total documents processed")
    successful: int = Field(ge=0, description="Successfully ingested")
    failed: int = Field(ge=0, description="Failed to ingest")
    skipped: int = Field(ge=0, description="Skipped (already indexed)")
    
    total_chunks: int = Field(ge=0, description="Total chunks created")
    
    documents: List[IngestDocumentResult] = Field(
        default_factory=list,
        description="Per-document results"
    )
    
    knowledge_type_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Summary of detected knowledge types"
    )
    
    processing_time_ms: float = Field(
        ge=0.0,
        description="Total processing time in milliseconds"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Ingestion timestamp"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "total_documents": 5,
                "successful": 4,
                "failed": 0,
                "skipped": 1,
                "total_chunks": 47,
                "documents": [
                    {
                        "source": "data/lessons_learned.txt",
                        "status": "success",
                        "chunks_created": 12,
                        "knowledge_type": "tacit"
                    }
                ],
                "knowledge_type_summary": {
                    "tacit": 2,
                    "explicit": 1,
                    "decision": 1
                },
                "processing_time_ms": 3456.78,
                "timestamp": "2026-01-07T12:00:00Z"
            }
        }


class IngestStatusResponse(BaseModel):
    """Response for checking ingestion status."""
    
    is_indexing: bool = Field(description="Whether indexing is in progress")
    current_document: Optional[str] = Field(
        default=None,
        description="Currently processing document"
    )
    progress: float = Field(
        ge=0.0,
        le=100.0,
        description="Progress percentage"
    )
    documents_processed: int = Field(ge=0, description="Documents processed")
    documents_total: int = Field(ge=0, description="Total documents")
