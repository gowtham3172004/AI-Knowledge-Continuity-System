"""
Pydantic schemas for knowledge gap endpoints.

Defines response models for knowledge gap detection and reporting.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field


class GapSeverity(str, Enum):
    """Severity levels for knowledge gaps."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GapCategory(str, Enum):
    """Categories of knowledge gaps."""
    MISSING_DOCUMENTATION = "missing_documentation"
    OUTDATED_INFORMATION = "outdated_information"
    INCOMPLETE_DECISION = "incomplete_decision"
    NO_TACIT_KNOWLEDGE = "no_tacit_knowledge"
    CONFLICTING_SOURCES = "conflicting_sources"
    INSUFFICIENT_CONTEXT = "insufficient_context"


class KnowledgeGapDetail(BaseModel):
    """
    Detailed information about a detected knowledge gap.
    
    Provides actionable information for knowledge administrators.
    """
    
    id: str = Field(description="Unique gap identifier")
    category: GapCategory = Field(description="Category of knowledge gap")
    severity: GapSeverity = Field(description="Severity level")
    
    query: str = Field(description="Original query that triggered gap")
    expected_topic: str = Field(description="Topic expected to have coverage")
    
    confidence_score: float = Field(
        ge=0.0,
        le=2.0,
        description="Answer confidence score when gap was detected"
    )
    
    indicators: List[str] = Field(
        default_factory=list,
        description="Indicators that triggered gap detection"
    )
    
    recommendation: str = Field(
        description="Recommended action to fill the gap"
    )
    
    detected_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the gap was detected"
    )
    
    related_documents: List[str] = Field(
        default_factory=list,
        description="Related documents that partially cover this topic"
    )


class KnowledgeGapReportResponse(BaseModel):
    """
    Response for knowledge gap report endpoint.
    
    Provides a summary of all detected gaps.
    """
    
    total_gaps: int = Field(ge=0, description="Total number of gaps detected")
    
    gaps_by_severity: Dict[str, int] = Field(
        default_factory=dict,
        description="Gap count by severity level"
    )
    
    gaps_by_category: Dict[str, int] = Field(
        default_factory=dict,
        description="Gap count by category"
    )
    
    recent_gaps: List[KnowledgeGapDetail] = Field(
        default_factory=list,
        description="Most recent knowledge gaps"
    )
    
    critical_gaps: List[KnowledgeGapDetail] = Field(
        default_factory=list,
        description="Critical gaps requiring immediate attention"
    )
    
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Report generation timestamp"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_gaps": 5,
                "gaps_by_severity": {
                    "critical": 1,
                    "high": 2,
                    "medium": 2,
                    "low": 0
                },
                "gaps_by_category": {
                    "missing_documentation": 2,
                    "outdated_information": 1,
                    "incomplete_decision": 2
                },
                "recent_gaps": [],
                "critical_gaps": [],
                "generated_at": "2026-01-07T12:00:00Z"
            }
        }


class GapAcknowledgeRequest(BaseModel):
    """Request to acknowledge a knowledge gap."""
    
    gap_id: str = Field(description="Gap ID to acknowledge")
    acknowledged_by: str = Field(description="User acknowledging the gap")
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Notes about the gap"
    )
    planned_resolution: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Planned resolution"
    )


class GapAcknowledgeResponse(BaseModel):
    """Response for gap acknowledgment."""
    
    gap_id: str = Field(description="Gap ID acknowledged")
    acknowledged: bool = Field(description="Whether acknowledgment succeeded")
    message: str = Field(description="Acknowledgment message")
