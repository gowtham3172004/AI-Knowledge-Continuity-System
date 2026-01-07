"""
Knowledge-Aware Retriever for AI Knowledge Continuity System.

This module extends the base retriever with knowledge-type-aware retrieval
capabilities to support:
- Feature 1: Tacit Knowledge Prioritization
- Feature 2: Decision-Aware Retrieval

The retriever can boost scores for tacit or decision documents based on
query intent, ensuring the right type of knowledge surfaces for each query.
"""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from langchain_core.documents import Document

from config.settings import get_settings
from core.logger import get_logger
from core.exceptions import RetrievalError
from rag.retriever import RetrieverManager, RetrievalResult
from vector_store.create_store import VectorStoreManager

# Import knowledge components
try:
    from knowledge.knowledge_classifier import KnowledgeClassifier, KnowledgeType
    from knowledge.gap_detector import KnowledgeGapDetector, GapDetectionResult
    from knowledge.validator import KnowledgeValidator, ValidationResult
    KNOWLEDGE_FEATURES_AVAILABLE = True
except ImportError:
    KNOWLEDGE_FEATURES_AVAILABLE = False

logger = get_logger(__name__)


@dataclass
class KnowledgeAwareRetrievalResult(RetrievalResult):
    """
    Extended retrieval result with knowledge-awareness information.
    
    Includes additional metadata about knowledge types, query intent,
    and any score adjustments applied during retrieval.
    """
    # Knowledge type analysis
    query_type: str = "general"  # "tacit", "decision", "general"
    query_intent_confidence: float = 0.0
    
    # Score adjustments
    scores_adjusted: bool = False
    adjustment_reason: str = ""
    
    # Knowledge distribution in results
    tacit_count: int = 0
    decision_count: int = 0
    explicit_count: int = 0
    
    # Gap detection (if enabled)
    gap_result: Optional[Any] = None  # GapDetectionResult
    
    # Validation (if enabled)
    validation_result: Optional[Any] = None  # ValidationResult
    
    def get_knowledge_distribution(self) -> Dict[str, int]:
        """Get distribution of knowledge types in results."""
        return {
            "tacit": self.tacit_count,
            "decision": self.decision_count,
            "explicit": self.explicit_count,
        }


class KnowledgeAwareRetriever:
    """
    Knowledge-aware retriever with tacit and decision prioritization.
    
    This retriever analyzes queries to determine intent and adjusts
    retrieval scores accordingly:
    - Tacit queries: Boost lessons learned, best practices, pitfalls
    - Decision queries: Boost ADRs, rationale, trade-off discussions
    
    It also integrates gap detection to identify when knowledge is
    insufficient to answer a query confidently.
    
    Example:
        >>> retriever = KnowledgeAwareRetriever()
        >>> result = retriever.retrieve("What mistakes should I avoid?")
        >>> print(result.tacit_count)  # High for tacit queries
        >>> print(result.query_type)   # "tacit"
    """
    
    def __init__(
        self,
        vector_store_manager: Optional[VectorStoreManager] = None,
        base_retriever_manager: Optional[RetrieverManager] = None,
        enable_gap_detection: bool = True,
        enable_validation: bool = True,
    ):
        """
        Initialize the knowledge-aware retriever.
        
        Args:
            vector_store_manager: Vector store manager instance.
            base_retriever_manager: Base retriever manager.
            enable_gap_detection: Whether to detect knowledge gaps.
            enable_validation: Whether to validate knowledge before return.
        """
        self.settings = get_settings()
        
        # Initialize base retriever
        self.vector_store_manager = vector_store_manager or VectorStoreManager()
        self.base_retriever = base_retriever_manager or RetrieverManager(
            vector_store_manager=self.vector_store_manager
        )
        
        # Feature flags
        self.enable_gap_detection = (
            enable_gap_detection and 
            KNOWLEDGE_FEATURES_AVAILABLE and
            getattr(self.settings, 'ENABLE_GAP_DETECTION', True)
        )
        self.enable_validation = enable_validation and KNOWLEDGE_FEATURES_AVAILABLE
        
        # Initialize knowledge components
        if KNOWLEDGE_FEATURES_AVAILABLE:
            self._classifier = KnowledgeClassifier()
            self._gap_detector = KnowledgeGapDetector() if self.enable_gap_detection else None
            self._validator = KnowledgeValidator() if self.enable_validation else None
        else:
            self._classifier = None
            self._gap_detector = None
            self._validator = None
            logger.warning("Knowledge features not available - using basic retrieval")
        
        # Score boost factors from settings
        self.tacit_boost = getattr(self.settings, 'TACIT_PRIORITY_BOOST', 1.3)
        self.decision_boost = getattr(self.settings, 'DECISION_PRIORITY_BOOST', 1.3)
        
        logger.info(
            f"KnowledgeAwareRetriever initialized: "
            f"gap_detection={self.enable_gap_detection}, "
            f"validation={self.enable_validation}"
        )
    
    def retrieve(
        self,
        query: str,
        k: Optional[int] = None,
        strategy: str = "similarity",
        apply_knowledge_boost: bool = True,
        department: Optional[str] = None,
        **kwargs,
    ) -> KnowledgeAwareRetrievalResult:
        """
        Retrieve documents with knowledge-type awareness.
        
        This method:
        1. Analyzes the query to determine intent (tacit/decision/general)
        2. Retrieves documents with similarity scores
        3. Adjusts scores based on query intent and document knowledge type
        4. Optionally detects knowledge gaps
        5. Returns enriched retrieval results
        
        Args:
            query: The search query.
            k: Number of documents to retrieve.
            strategy: Base retrieval strategy.
            apply_knowledge_boost: Whether to adjust scores by knowledge type.
            department: Optional department context for gap logging.
            **kwargs: Additional arguments for base retriever.
            
        Returns:
            KnowledgeAwareRetrievalResult with documents and metadata.
        """
        k = k or self.settings.RETRIEVER_K
        
        logger.info(f"Knowledge-aware retrieval: '{query[:50]}...'")
        
        try:
            # Step 1: Analyze query intent
            query_type, query_confidence = self._analyze_query_intent(query)
            
            # Step 2: Retrieve with scores
            docs_with_scores = self.vector_store_manager.search(
                query=query,
                k=k * 2,  # Fetch more to allow for filtering
                score_threshold=0.0,  # Don't filter yet, we'll re-rank
            )
            
            if not docs_with_scores:
                return self._create_empty_result(query, query_type, query_confidence)
            
            # Step 3: Apply knowledge-type score adjustments
            if apply_knowledge_boost and self._classifier:
                docs_with_scores, adjustment_reason = self._apply_knowledge_boost(
                    docs_with_scores=docs_with_scores,
                    query_type=query_type,
                )
                scores_adjusted = bool(adjustment_reason)
            else:
                scores_adjusted = False
                adjustment_reason = ""
            
            # Step 4: Re-sort by adjusted scores and limit
            docs_with_scores.sort(key=lambda x: x[1], reverse=True)
            docs_with_scores = docs_with_scores[:k]
            
            # Step 5: Count knowledge types in results
            tacit_count, decision_count, explicit_count = self._count_knowledge_types(
                docs_with_scores
            )
            
            # Step 6: Extract documents (without scores)
            documents = [doc for doc, _ in docs_with_scores]
            
            # Step 7: Gap detection (if enabled)
            gap_result = None
            if self._gap_detector:
                gap_result = self._gap_detector.evaluate(
                    query=query,
                    documents_with_scores=docs_with_scores,
                    department=department,
                    log_gap=True,
                )
            
            # Step 8: Validation (if enabled)
            validation_result = None
            if self._validator:
                validation_result = self._validator.validate(
                    query=query,
                    documents_with_scores=docs_with_scores,
                    department=department,
                )
            
            result = KnowledgeAwareRetrievalResult(
                documents=documents,
                query=query,
                retriever_type=f"knowledge_aware_{strategy}",
                num_results=len(documents),
                query_type=query_type,
                query_intent_confidence=query_confidence,
                scores_adjusted=scores_adjusted,
                adjustment_reason=adjustment_reason,
                tacit_count=tacit_count,
                decision_count=decision_count,
                explicit_count=explicit_count,
                gap_result=gap_result,
                validation_result=validation_result,
            )
            
            logger.info(
                f"Retrieved {len(documents)} docs: "
                f"query_type={query_type}, "
                f"tacit={tacit_count}, decision={decision_count}, explicit={explicit_count}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Knowledge-aware retrieval failed: {e}")
            raise RetrievalError(
                f"Knowledge-aware retrieval failed: {e}",
                details={"query": query}
            )
    
    def retrieve_with_scores(
        self,
        query: str,
        k: Optional[int] = None,
        apply_knowledge_boost: bool = True,
    ) -> List[Tuple[Document, float]]:
        """
        Retrieve documents with their similarity scores.
        
        Args:
            query: The search query.
            k: Number of documents to retrieve.
            apply_knowledge_boost: Whether to adjust scores by knowledge type.
            
        Returns:
            List of (document, score) tuples.
        """
        k = k or self.settings.RETRIEVER_K
        
        # Analyze query intent
        query_type, _ = self._analyze_query_intent(query)
        
        # Get base results with scores
        docs_with_scores = self.vector_store_manager.search(
            query=query,
            k=k * 2,
            score_threshold=0.0,
        )
        
        # Apply knowledge boost if enabled
        if apply_knowledge_boost and self._classifier:
            docs_with_scores, _ = self._apply_knowledge_boost(
                docs_with_scores=docs_with_scores,
                query_type=query_type,
            )
        
        # Sort and limit
        docs_with_scores.sort(key=lambda x: x[1], reverse=True)
        return docs_with_scores[:k]
    
    def _analyze_query_intent(self, query: str) -> Tuple[str, float]:
        """
        Analyze query to determine knowledge type intent.
        
        Returns:
            Tuple of (query_type, confidence).
        """
        if not self._classifier:
            return "general", 0.0
        
        # Check for tacit query indicators
        is_tacit, tacit_indicators = self._classifier.is_tacit_query(query)
        
        # Check for decision query indicators
        is_decision, decision_indicators = self._classifier.is_decision_query(query)
        
        # Determine intent
        tacit_strength = len(tacit_indicators)
        decision_strength = len(decision_indicators)
        
        if tacit_strength > 0 and tacit_strength >= decision_strength:
            return "tacit", min(1.0, tacit_strength / 3)
        elif decision_strength > 0:
            return "decision", min(1.0, decision_strength / 3)
        else:
            return "general", 1.0
    
    def _apply_knowledge_boost(
        self,
        docs_with_scores: List[Tuple[Document, float]],
        query_type: str,
    ) -> Tuple[List[Tuple[Document, float]], str]:
        """
        Apply score adjustments based on query type and document knowledge type.
        
        For tacit queries: Boost tacit documents
        For decision queries: Boost decision documents
        
        Args:
            docs_with_scores: Documents with original scores.
            query_type: Detected query intent type.
            
        Returns:
            Tuple of (adjusted documents with scores, adjustment reason).
        """
        if query_type == "general":
            return docs_with_scores, ""
        
        adjusted_results = []
        adjustment_reason = ""
        
        for doc, score in docs_with_scores:
            doc_knowledge_type = doc.metadata.get("knowledge_type", "explicit")
            adjusted_score = score
            
            if query_type == "tacit" and doc_knowledge_type == "tacit":
                adjusted_score = min(1.0, score * self.tacit_boost)
                if not adjustment_reason:
                    adjustment_reason = f"Boosted tacit knowledge by {self.tacit_boost}x"
                    
            elif query_type == "decision" and doc_knowledge_type == "decision":
                adjusted_score = min(1.0, score * self.decision_boost)
                if not adjustment_reason:
                    adjustment_reason = f"Boosted decision knowledge by {self.decision_boost}x"
            
            adjusted_results.append((doc, adjusted_score))
        
        return adjusted_results, adjustment_reason
    
    def _count_knowledge_types(
        self,
        docs_with_scores: List[Tuple[Document, float]],
    ) -> Tuple[int, int, int]:
        """Count documents by knowledge type."""
        tacit_count = 0
        decision_count = 0
        explicit_count = 0
        
        for doc, _ in docs_with_scores:
            kt = doc.metadata.get("knowledge_type", "explicit")
            if kt == "tacit":
                tacit_count += 1
            elif kt == "decision":
                decision_count += 1
            else:
                explicit_count += 1
        
        return tacit_count, decision_count, explicit_count
    
    def _create_empty_result(
        self,
        query: str,
        query_type: str,
        query_confidence: float,
    ) -> KnowledgeAwareRetrievalResult:
        """Create result for empty retrieval."""
        # Create gap result for empty retrieval
        gap_result = None
        if self._gap_detector:
            gap_result = self._gap_detector.evaluate(
                query=query,
                documents_with_scores=[],
                log_gap=True,
            )
        
        return KnowledgeAwareRetrievalResult(
            documents=[],
            query=query,
            retriever_type="knowledge_aware_similarity",
            num_results=0,
            query_type=query_type,
            query_intent_confidence=query_confidence,
            scores_adjusted=False,
            adjustment_reason="",
            tacit_count=0,
            decision_count=0,
            explicit_count=0,
            gap_result=gap_result,
        )
    
    def format_context(
        self,
        documents: List[Document],
        max_length: Optional[int] = None,
        include_metadata: bool = True,
        emphasize_knowledge_type: bool = True,
    ) -> str:
        """
        Format retrieved documents into context string with knowledge indicators.
        
        Args:
            documents: Documents to format.
            max_length: Maximum context length.
            include_metadata: Whether to include source metadata.
            emphasize_knowledge_type: Whether to add knowledge type indicators.
            
        Returns:
            Formatted context string.
        """
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            # Build document section
            section = f"[Document {i}]"
            
            # Add knowledge type indicator if enabled
            if emphasize_knowledge_type:
                kt = doc.metadata.get("knowledge_type", "explicit")
                kt_indicator = {
                    "tacit": "📚 LESSONS LEARNED",
                    "decision": "📋 DECISION RECORD",
                    "explicit": "📄 DOCUMENTATION",
                }.get(kt, "📄 DOCUMENTATION")
                section += f" {kt_indicator}"
            
            if include_metadata:
                source = doc.metadata.get("source", doc.metadata.get("file_name", "Unknown"))
                section += f"\nSource: {source}"
                
                # Add decision metadata if available
                if doc.metadata.get("knowledge_type") == "decision":
                    if doc.metadata.get("decision_author"):
                        section += f"\nAuthor: {doc.metadata.get('decision_author')}"
                    if doc.metadata.get("decision_date"):
                        section += f"\nDate: {doc.metadata.get('decision_date')}"
            
            section += f"\n{doc.page_content}"
            context_parts.append(section)
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Truncate if needed
        if max_length and len(context) > max_length:
            context = context[:max_length] + "\n\n[Context truncated...]"
        
        return context


# Factory function for easy instantiation
def get_knowledge_aware_retriever(
    enable_gap_detection: bool = True,
    enable_validation: bool = True,
) -> KnowledgeAwareRetriever:
    """
    Get a configured knowledge-aware retriever instance.
    
    Args:
        enable_gap_detection: Whether to enable gap detection.
        enable_validation: Whether to enable validation.
        
    Returns:
        Configured KnowledgeAwareRetriever instance.
    """
    return KnowledgeAwareRetriever(
        enable_gap_detection=enable_gap_detection,
        enable_validation=enable_validation,
    )
