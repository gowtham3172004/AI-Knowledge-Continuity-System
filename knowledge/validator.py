"""
Knowledge Validation Module for AI Knowledge Continuity System.

This module provides a validation layer that runs between retrieval
and generation to ensure response quality and safety. It integrates
gap detection, knowledge type analysis, and query-context matching.

The validator acts as a guardrail to:
1. Prevent hallucinations when knowledge is insufficient
2. Ensure tacit knowledge is surfaced for relevant queries
3. Verify decision context is available for decision queries
4. Provide explainable validation results
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from langchain_core.documents import Document

from core.logger import get_logger
from knowledge.knowledge_classifier import KnowledgeClassifier, KnowledgeType
from knowledge.gap_detector import KnowledgeGapDetector, GapDetectionResult, GapSeverity

logger = get_logger(__name__)


class ValidationStatus(str, Enum):
    """Status of knowledge validation."""
    PASSED = "passed"           # Sufficient knowledge, proceed with generation
    PASSED_WITH_WARNING = "passed_with_warning"  # Proceed but with caveats
    FAILED_GAP = "failed_gap"   # Knowledge gap detected
    FAILED_MISMATCH = "failed_mismatch"  # Knowledge type mismatch


@dataclass
class ValidationResult:
    """
    Result of knowledge validation before generation.
    
    This provides a comprehensive assessment of whether the retrieved
    knowledge is suitable for answering the query.
    """
    # Core status
    status: ValidationStatus
    can_proceed: bool
    
    # Confidence and scoring
    confidence_score: float  # 0.0 to 1.0
    relevance_score: float   # 0.0 to 1.0
    
    # Gap detection result (if applicable)
    gap_result: Optional[GapDetectionResult] = None
    
    # Query analysis
    query_type: str = "general"  # "tacit", "decision", "general"
    query_indicators: List[str] = field(default_factory=list)
    
    # Knowledge coverage
    knowledge_types_found: List[str] = field(default_factory=list)
    has_tacit_match: bool = False
    has_decision_match: bool = False
    
    # Response guidance
    response_guidance: str = ""
    warnings: List[str] = field(default_factory=list)
    safe_response: Optional[str] = None
    
    # Source attribution
    primary_sources: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "can_proceed": self.can_proceed,
            "confidence_score": self.confidence_score,
            "relevance_score": self.relevance_score,
            "query_type": self.query_type,
            "knowledge_types_found": self.knowledge_types_found,
            "has_tacit_match": self.has_tacit_match,
            "has_decision_match": self.has_decision_match,
            "response_guidance": self.response_guidance,
            "warnings": self.warnings,
            "primary_sources": self.primary_sources,
        }


class KnowledgeValidator:
    """
    Validates retrieved knowledge before LLM generation.
    
    This class serves as a critical guardrail between retrieval and
    generation, ensuring that:
    1. Sufficient knowledge exists to answer the query
    2. The right type of knowledge is being used
    3. Responses are explainable and source-attributed
    
    Example:
        >>> validator = KnowledgeValidator()
        >>> result = validator.validate(query, documents_with_scores)
        >>> if result.can_proceed:
        ...     # Generate response with guidance
        ...     pass
        >>> else:
        ...     return result.safe_response
    """
    
    def __init__(
        self,
        gap_detector: Optional[KnowledgeGapDetector] = None,
        classifier: Optional[KnowledgeClassifier] = None,
        strict_mode: bool = False,
    ):
        """
        Initialize the knowledge validator.
        
        Args:
            gap_detector: Gap detector instance.
            classifier: Knowledge classifier instance.
            strict_mode: If True, require exact knowledge type matches.
        """
        self.gap_detector = gap_detector or KnowledgeGapDetector()
        self.classifier = classifier or KnowledgeClassifier()
        self.strict_mode = strict_mode
        
        logger.info(f"KnowledgeValidator initialized (strict_mode={strict_mode})")
    
    def validate(
        self,
        query: str,
        documents_with_scores: List[Tuple[Document, float]],
        department: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validate retrieved knowledge for answering a query.
        
        This method performs comprehensive validation including:
        1. Gap detection (is there enough knowledge?)
        2. Query type analysis (what type of knowledge is needed?)
        3. Knowledge type matching (do we have the right type?)
        4. Response guidance generation
        
        Args:
            query: The user's question.
            documents_with_scores: Retrieved documents with scores.
            department: Optional department context.
            
        Returns:
            ValidationResult with detailed assessment.
        """
        # Step 1: Run gap detection
        gap_result = self.gap_detector.evaluate(
            query=query,
            documents_with_scores=documents_with_scores,
            department=department,
            log_gap=True,
        )
        
        # Step 2: Analyze query type
        query_type, query_indicators = self._analyze_query_type(query)
        
        # Step 3: Analyze knowledge coverage
        knowledge_types = self._get_knowledge_types(documents_with_scores)
        has_tacit = "tacit" in knowledge_types
        has_decision = "decision" in knowledge_types
        
        # Step 4: Check for knowledge type mismatch
        type_mismatch = self._check_type_mismatch(
            query_type=query_type,
            has_tacit=has_tacit,
            has_decision=has_decision,
        )
        
        # Step 5: Generate response guidance
        guidance = self._generate_guidance(
            query_type=query_type,
            knowledge_types=knowledge_types,
            gap_result=gap_result,
        )
        
        # Step 6: Collect warnings
        warnings = self._collect_warnings(
            query_type=query_type,
            has_tacit=has_tacit,
            has_decision=has_decision,
            gap_result=gap_result,
        )
        
        # Step 7: Get primary sources for attribution
        primary_sources = self._get_primary_sources(documents_with_scores)
        
        # Step 8: Determine final status
        if gap_result.gap_detected and gap_result.gap_severity in [GapSeverity.HIGH, GapSeverity.CRITICAL]:
            status = ValidationStatus.FAILED_GAP
            can_proceed = False
            safe_response = gap_result.safe_response
        elif type_mismatch and self.strict_mode:
            status = ValidationStatus.FAILED_MISMATCH
            can_proceed = False
            safe_response = self._generate_mismatch_response(query_type)
        elif warnings:
            status = ValidationStatus.PASSED_WITH_WARNING
            can_proceed = True
            safe_response = None
        else:
            status = ValidationStatus.PASSED
            can_proceed = True
            safe_response = None
        
        # Calculate relevance score
        relevance_score = self._calculate_relevance(
            query_type=query_type,
            has_tacit=has_tacit,
            has_decision=has_decision,
            gap_result=gap_result,
        )
        
        return ValidationResult(
            status=status,
            can_proceed=can_proceed,
            confidence_score=gap_result.confidence_score,
            relevance_score=relevance_score,
            gap_result=gap_result,
            query_type=query_type,
            query_indicators=query_indicators,
            knowledge_types_found=knowledge_types,
            has_tacit_match=has_tacit and query_type == "tacit",
            has_decision_match=has_decision and query_type == "decision",
            response_guidance=guidance,
            warnings=warnings,
            safe_response=safe_response,
            primary_sources=primary_sources,
        )
    
    def _analyze_query_type(self, query: str) -> Tuple[str, List[str]]:
        """
        Analyze the query to determine what type of knowledge is needed.
        
        Returns:
            Tuple of (query_type, matched_indicators).
        """
        # Check for tacit query
        is_tacit, tacit_indicators = self.classifier.is_tacit_query(query)
        
        # Check for decision query
        is_decision, decision_indicators = self.classifier.is_decision_query(query)
        
        # Determine primary query type
        if is_tacit and not is_decision:
            return "tacit", tacit_indicators
        elif is_decision and not is_tacit:
            return "decision", decision_indicators
        elif is_tacit and is_decision:
            # Both matched - prefer decision if it has more indicators
            if len(decision_indicators) >= len(tacit_indicators):
                return "decision", decision_indicators
            else:
                return "tacit", tacit_indicators
        else:
            return "general", []
    
    def _get_knowledge_types(
        self,
        documents_with_scores: List[Tuple[Document, float]],
    ) -> List[str]:
        """Get unique knowledge types from retrieved documents."""
        types = set()
        for doc, _ in documents_with_scores:
            kt = doc.metadata.get("knowledge_type", "explicit")
            types.add(kt)
        return list(types)
    
    def _check_type_mismatch(
        self,
        query_type: str,
        has_tacit: bool,
        has_decision: bool,
    ) -> bool:
        """Check if there's a mismatch between query and knowledge types."""
        if query_type == "tacit" and not has_tacit:
            return True
        if query_type == "decision" and not has_decision:
            return True
        return False
    
    def _generate_guidance(
        self,
        query_type: str,
        knowledge_types: List[str],
        gap_result: GapDetectionResult,
    ) -> str:
        """Generate guidance for the LLM response."""
        guidance_parts = []
        
        if query_type == "tacit":
            if "tacit" in knowledge_types:
                guidance_parts.append(
                    "Prioritize insights from lessons learned and experiential knowledge. "
                    "Emphasize practical recommendations and things to avoid."
                )
            else:
                guidance_parts.append(
                    "The user is asking for tacit knowledge, but only explicit documentation "
                    "was found. Acknowledge this limitation in your response."
                )
        
        elif query_type == "decision":
            if "decision" in knowledge_types:
                guidance_parts.append(
                    "Focus on explaining the rationale behind decisions. "
                    "Include who made the decision, when, what alternatives were considered, "
                    "and what trade-offs were accepted."
                )
            else:
                guidance_parts.append(
                    "The user is asking about decision rationale, but no decision records "
                    "were found. Indicate that the specific decision context is not documented."
                )
        
        if gap_result.confidence_score < 0.7:
            guidance_parts.append(
                "Retrieved knowledge has moderate confidence. "
                "Be explicit about what is known vs. uncertain."
            )
        
        return " ".join(guidance_parts) if guidance_parts else "Proceed with standard response."
    
    def _collect_warnings(
        self,
        query_type: str,
        has_tacit: bool,
        has_decision: bool,
        gap_result: GapDetectionResult,
    ) -> List[str]:
        """Collect warnings about the validation."""
        warnings = []
        
        if query_type == "tacit" and not has_tacit:
            warnings.append("No tacit knowledge sources found for experience-based query")
        
        if query_type == "decision" and not has_decision:
            warnings.append("No decision records found for rationale-based query")
        
        if gap_result.gap_detected and gap_result.gap_severity == GapSeverity.LOW:
            warnings.append("Partial knowledge coverage - some information may be missing")
        
        if gap_result.num_relevant_documents < 3:
            warnings.append(f"Limited sources: only {gap_result.num_relevant_documents} relevant documents")
        
        return warnings
    
    def _get_primary_sources(
        self,
        documents_with_scores: List[Tuple[Document, float]],
        limit: int = 3,
    ) -> List[str]:
        """Get primary source attributions from top documents."""
        sources = []
        for doc, score in documents_with_scores[:limit]:
            source = doc.metadata.get("source", doc.metadata.get("file_name", "Unknown"))
            if source not in sources:
                sources.append(source)
        return sources
    
    def _calculate_relevance(
        self,
        query_type: str,
        has_tacit: bool,
        has_decision: bool,
        gap_result: GapDetectionResult,
    ) -> float:
        """Calculate relevance score based on knowledge type match."""
        base_score = gap_result.confidence_score
        
        # Boost for matching knowledge type
        if query_type == "tacit" and has_tacit:
            base_score = min(1.0, base_score * 1.2)
        elif query_type == "decision" and has_decision:
            base_score = min(1.0, base_score * 1.2)
        
        # Penalty for mismatch
        if query_type == "tacit" and not has_tacit:
            base_score *= 0.8
        elif query_type == "decision" and not has_decision:
            base_score *= 0.8
        
        return round(base_score, 3)
    
    def _generate_mismatch_response(self, query_type: str) -> str:
        """Generate response for knowledge type mismatch."""
        if query_type == "tacit":
            return (
                "I found some documentation related to your question, but the "
                "organizational knowledge base doesn't contain lessons learned, "
                "best practices, or experiential insights on this topic. "
                "Consider reaching out to team members with direct experience."
            )
        elif query_type == "decision":
            return (
                "I couldn't find documented decision records or rationale for this topic. "
                "While some related documentation exists, the specific reasoning behind "
                "this decision is not captured in the knowledge base. "
                "Consider consulting with the original decision makers."
            )
        else:
            return "Knowledge type mismatch detected."
    
    def validate_for_generation(
        self,
        query: str,
        documents: List[Document],
        scores: List[float],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Simplified validation interface for RAG chain integration.
        
        Args:
            query: User query.
            documents: Retrieved documents.
            scores: Similarity scores.
            
        Returns:
            Tuple of (can_proceed, response_or_guidance, metadata).
        """
        # Combine documents and scores
        docs_with_scores = list(zip(documents, scores))
        
        # Run validation
        result = self.validate(query, docs_with_scores)
        
        if result.can_proceed:
            return True, result.response_guidance, result.to_dict()
        else:
            return False, result.safe_response or "", result.to_dict()
