"""
Pydantic schemas for query endpoints.

Defines request and response models for the /api/query endpoint.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class KnowledgeType(str, Enum):
    """Types of knowledge in the system."""
    TACIT = "tacit"
    EXPLICIT = "explicit"
    DECISION = "decision"
    UNKNOWN = "unknown"


class QueryRole(str, Enum):
    """User roles for contextual responses."""
    DEVELOPER = "developer"
    MANAGER = "manager"
    ANALYST = "analyst"
    EXECUTIVE = "executive"
    GENERAL = "general"


class QueryRequest(BaseModel):
    """
    Request model for query endpoint.
    
    Attributes:
        question: The user's question
        role: Optional user role for contextual responses
        department: Optional department context
        conversation_id: Optional ID for conversation continuity
        use_knowledge_features: Enable advanced knowledge features
    """
    
    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="The question to ask the knowledge system",
        examples=["What lessons were learned from the backend project?"]
    )
    
    role: Optional[QueryRole] = Field(
        default=QueryRole.GENERAL,
        description="User role for contextual responses"
    )
    
    department: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Department context",
        examples=["Engineering", "Product", "Operations"]
    )
    
    conversation_id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Conversation ID for multi-turn conversations"
    )
    
    use_knowledge_features: bool = Field(
        default=True,
        description="Enable tacit knowledge, decision traceability, and gap detection"
    )
    
    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Validate and clean the question."""
        v = v.strip()
        if not v:
            raise ValueError("Question cannot be empty")
        return v


class SourceDocument(BaseModel):
    """
    Source document used to generate the answer.
    
    Attributes:
        source: Document source path or name
        content_preview: Preview of document content
        knowledge_type: Type of knowledge (tacit, explicit, decision)
        relevance_score: Similarity score
    """
    
    source: str = Field(description="Document source path")
    content_preview: str = Field(description="Preview of document content")
    knowledge_type: KnowledgeType = Field(
        default=KnowledgeType.EXPLICIT,
        description="Type of knowledge"
    )
    relevance_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Relevance score (0-1)"
    )
    
    # Decision metadata (if applicable)
    decision_id: Optional[str] = Field(default=None, description="Decision ID (for ADRs)")
    decision_author: Optional[str] = Field(default=None, description="Decision author")
    decision_date: Optional[str] = Field(default=None, description="Decision date")


class DecisionTrace(BaseModel):
    """
    Decision traceability information.
    
    Captures the full context of a decision when decision
    documents are used in the response.
    """
    
    decision_id: Optional[str] = Field(default=None, description="Decision ID")
    title: Optional[str] = Field(default=None, description="Decision title")
    author: Optional[str] = Field(default=None, description="Decision author")
    date: Optional[str] = Field(default=None, description="Decision date")
    rationale: Optional[str] = Field(default=None, description="Decision rationale")
    alternatives: List[str] = Field(default_factory=list, description="Alternatives considered")
    tradeoffs: List[str] = Field(default_factory=list, description="Trade-offs accepted")


class KnowledgeGapInfo(BaseModel):
    """
    Knowledge gap detection information.
    
    Provides details when a knowledge gap is detected.
    """
    
    detected: bool = Field(description="Whether a knowledge gap was detected")
    severity: Optional[str] = Field(
        default=None,
        description="Gap severity (low, medium, high, critical)"
    )
    confidence_score: float = Field(
        ge=0.0,
        le=2.0,
        description="Confidence score for the answer"
    )
    reason: Optional[str] = Field(
        default=None,
        description="Reason for gap detection"
    )


class QueryResponse(BaseModel):
    """
    Response model for query endpoint.
    
    Provides comprehensive information about the query result,
    including all three knowledge features.
    """
    
    # Core response
    answer: str = Field(description="The generated answer")
    query: str = Field(description="The original query")
    
    # Sources
    sources: List[SourceDocument] = Field(
        default_factory=list,
        description="Source documents used"
    )
    
    # Knowledge features metadata
    query_type: str = Field(
        default="general",
        description="Detected query type (tacit, decision, general)"
    )
    knowledge_types_used: List[str] = Field(
        default_factory=list,
        description="Types of knowledge used in response"
    )
    
    # Feature 1: Tacit Knowledge
    tacit_knowledge_used: bool = Field(
        default=False,
        description="Whether tacit knowledge influenced the answer"
    )
    
    # Feature 2: Decision Traceability
    decision_trace: Optional[DecisionTrace] = Field(
        default=None,
        description="Decision traceability information"
    )
    
    # Feature 3: Knowledge Gap Detection
    knowledge_gap: KnowledgeGapInfo = Field(
        description="Knowledge gap detection information"
    )
    
    # Metadata
    warnings: List[str] = Field(
        default_factory=list,
        description="Any warnings about the response"
    )
    confidence: float = Field(
        ge=0.0,
        description="Overall confidence score"
    )
    processing_time_ms: float = Field(
        ge=0.0,
        description="Processing time in milliseconds"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Based on the backend team's retrospective...",
                "query": "What lessons were learned from the backend project?",
                "sources": [
                    {
                        "source": "data/lessons_learned.txt",
                        "content_preview": "Key lessons from Q4...",
                        "knowledge_type": "tacit",
                        "relevance_score": 0.89
                    }
                ],
                "query_type": "tacit",
                "knowledge_types_used": ["tacit", "decision"],
                "tacit_knowledge_used": True,
                "decision_trace": None,
                "knowledge_gap": {
                    "detected": False,
                    "severity": None,
                    "confidence_score": 0.89,
                    "reason": None
                },
                "warnings": [],
                "confidence": 0.89,
                "processing_time_ms": 1234.56,
                "timestamp": "2026-01-07T12:00:00Z"
            }
        }


class QueryErrorResponse(BaseModel):
    """Error response for query endpoint."""
    
    error: Dict[str, Any] = Field(description="Error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Question is required",
                    "details": {"field": "question"}
                }
            }
        }
