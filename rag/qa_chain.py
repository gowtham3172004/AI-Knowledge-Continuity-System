"""
RAG Chain Module for AI Knowledge Continuity System.

This module provides the main RAG (Retrieval-Augmented Generation) pipeline
that combines retrieval, context formatting, and LLM generation.

Extended to support:
- Feature 1: Tacit Knowledge Extraction (prioritize lessons learned)
- Feature 2: Decision Traceability (explain rationale with context)
- Feature 3: Knowledge Gap Detection (prevent hallucinations)
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from langchain_core.documents import Document

from config.settings import get_settings
from core.logger import get_logger
from core.exceptions import LLMError, RetrievalError, KnowledgeGapError
from rag.prompt import PromptManager, get_prompt_manager
from rag.llm import LLMManager, get_llm_manager
from rag.retriever import RetrieverManager
from vector_store.create_store import VectorStoreManager
from memory.conversation_memory import ConversationMemoryManager, get_memory_manager

# Import knowledge-aware components
try:
    from rag.knowledge_retriever import KnowledgeAwareRetriever, KnowledgeAwareRetrievalResult
    from knowledge.validator import KnowledgeValidator, ValidationResult, ValidationStatus
    from knowledge.gap_detector import GapDetectionResult, GapSeverity
    KNOWLEDGE_FEATURES_AVAILABLE = True
except ImportError:
    KNOWLEDGE_FEATURES_AVAILABLE = False

logger = get_logger(__name__)


@dataclass
class RAGResponse:
    """
    Container for RAG response with all relevant information.
    
    Attributes:
        answer: The generated answer.
        source_documents: Documents used to generate the answer.
        query: The original query.
        confidence: Optional confidence score.
        processing_time: Time taken to process the query.
        metadata: Additional metadata about the response.
    """
    answer: str
    source_documents: List[Document]
    query: str
    confidence: Optional[float] = None
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Knowledge-aware fields (Features 1, 2, 3)
    query_type: str = "general"  # "tacit", "decision", "general"
    knowledge_gap_detected: bool = False
    gap_severity: Optional[str] = None
    validation_warnings: List[str] = field(default_factory=list)
    knowledge_types_used: List[str] = field(default_factory=list)
    
    def get_sources_summary(self) -> List[Dict[str, str]]:
        """Get a summary of source documents."""
        sources = []
        for doc in self.source_documents:
            source_info = {
                "source": doc.metadata.get("source", "Unknown"),
                "content_preview": doc.page_content[:200] + "...",
                "knowledge_type": doc.metadata.get("knowledge_type", "explicit"),
            }
            
            # Add decision metadata if available
            if doc.metadata.get("knowledge_type") == "decision":
                source_info["decision_author"] = doc.metadata.get("decision_author")
                source_info["decision_date"] = doc.metadata.get("decision_date")
            
            sources.append(source_info)
        return sources
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "answer": self.answer,
            "query": self.query,
            "sources": self.get_sources_summary(),
            "num_sources": len(self.source_documents),
            "confidence": self.confidence,
            "processing_time": self.processing_time,
            "metadata": self.metadata,
            # Knowledge-aware fields
            "query_type": self.query_type,
            "knowledge_gap_detected": self.knowledge_gap_detected,
            "gap_severity": self.gap_severity,
            "validation_warnings": self.validation_warnings,
            "knowledge_types_used": self.knowledge_types_used,
        }
    
    def has_warnings(self) -> bool:
        """Check if response has any warnings."""
        return bool(self.validation_warnings) or self.knowledge_gap_detected


class RAGChain:
    """
    Production-grade RAG Chain for question answering.
    
    This class orchestrates the complete RAG pipeline:
    1. Query processing
    2. Document retrieval
    3. Context formatting
    4. LLM generation
    5. Response formatting with sources
    
    Features:
    - Multiple retrieval strategies
    - Conversation memory support
    - Source attribution
    - Error handling and logging
    - Performance tracking
    
    Example:
        >>> chain = RAGChain()
        >>> response = chain.query("How do I deploy the application?")
        >>> print(response.answer)
        >>> print(response.get_sources_summary())
    """
    
    def __init__(
        self,
        llm_manager: Optional[LLMManager] = None,
        retriever_manager: Optional[RetrieverManager] = None,
        memory_manager: Optional[ConversationMemoryManager] = None,
        prompt_manager: Optional[PromptManager] = None,
        enable_knowledge_features: bool = True,
    ):
        """
        Initialize the RAG chain.
        
        Args:
            llm_manager: LLM manager instance.
            retriever_manager: Retriever manager instance.
            memory_manager: Conversation memory manager.
            prompt_manager: Prompt template manager.
            enable_knowledge_features: Enable tacit/decision/gap detection features.
        """
        self.settings = get_settings()
        
        # Initialize components
        self.llm_manager = llm_manager or get_llm_manager()
        self.prompt_manager = prompt_manager or get_prompt_manager()
        self.memory_manager = memory_manager or get_memory_manager()
        
        # Initialize vector store and retriever
        self.vector_store_manager = VectorStoreManager()
        self.retriever_manager = retriever_manager or RetrieverManager(
            vector_store_manager=self.vector_store_manager
        )
        
        # Set LLM on retriever for advanced strategies
        try:
            llm = self.llm_manager.get_llm()
            self.retriever_manager.set_llm(llm)
        except Exception as e:
            logger.warning(f"Could not set LLM on retriever: {e}")
        
        # === KNOWLEDGE-AWARE FEATURES (Features 1, 2, 3) ===
        self.enable_knowledge_features = (
            enable_knowledge_features and KNOWLEDGE_FEATURES_AVAILABLE
        )
        
        if self.enable_knowledge_features:
            self.knowledge_retriever = KnowledgeAwareRetriever(
                vector_store_manager=self.vector_store_manager,
                enable_gap_detection=True,
                enable_validation=True,
            )
            logger.info("Knowledge-aware features enabled (tacit, decision, gap detection)")
        else:
            self.knowledge_retriever = None
            logger.info("Using standard RAG without knowledge-aware features")
        
        logger.info("RAGChain initialized successfully")
    
    def query(
        self,
        question: str,
        session_id: str = "default",
        retrieval_strategy: str = "similarity",
        k: Optional[int] = None,
        include_sources: bool = True,
        use_memory: bool = True,
        use_knowledge_features: bool = True,
    ) -> RAGResponse:
        """
        Process a question through the RAG pipeline.
        
        This method now supports knowledge-aware features:
        - Tacit knowledge prioritization for experience-based queries
        - Decision traceability for rationale queries
        - Knowledge gap detection to prevent hallucinations
        
        Args:
            question: The question to answer.
            session_id: Session ID for conversation memory.
            retrieval_strategy: Strategy for document retrieval.
            k: Number of documents to retrieve.
            include_sources: Whether to include source documents.
            use_memory: Whether to use conversation memory.
            use_knowledge_features: Whether to use tacit/decision/gap features.
            
        Returns:
            RAGResponse with answer, sources, and knowledge metadata.
        """
        start_time = datetime.now()
        logger.info(f"Processing query: {question[:100]}...")
        
        try:
            # Step 1: Get conversation history if using memory
            chat_history = ""
            if use_memory:
                history = self.memory_manager.get_history(session_id)
                if history:
                    chat_history = self._format_chat_history(history)
            
            # === KNOWLEDGE-AWARE RETRIEVAL (Features 1, 2, 3) ===
            if use_knowledge_features and self.enable_knowledge_features and self.knowledge_retriever:
                return self._query_with_knowledge_features(
                    question=question,
                    session_id=session_id,
                    k=k,
                    include_sources=include_sources,
                    chat_history=chat_history,
                    start_time=start_time,
                )
            
            # === STANDARD RETRIEVAL (backward compatibility) ===
            # Step 2: Retrieve relevant documents
            retrieval_result = self.retriever_manager.retrieve(
                query=question,
                strategy=retrieval_strategy,
                k=k,
            )
            
            # Step 3: Format context
            context = self.retriever_manager.format_context(
                documents=retrieval_result.documents,
                include_metadata=True,
            )
            
            # Step 4: Generate answer using LLM
            llm = self.llm_manager.get_llm()
            prompt = self.prompt_manager.get_qa_prompt()
            
            # Format the prompt
            formatted_prompt = prompt.format(
                context=context,
                question=question,
            )
            
            # If we have chat history, prepend it
            if chat_history:
                formatted_prompt = f"Previous conversation:\n{chat_history}\n\n{formatted_prompt}"
            
            # Get LLM response
            response = llm.invoke(formatted_prompt)
            
            # Extract answer text
            if hasattr(response, 'content'):
                answer = response.content
            else:
                answer = str(response)
            
            # Step 5: Update conversation memory
            if use_memory:
                self.memory_manager.add_exchange(
                    session_id=session_id,
                    human_message=question,
                    ai_message=answer,
                )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create response object
            rag_response = RAGResponse(
                answer=answer,
                source_documents=retrieval_result.documents if include_sources else [],
                query=question,
                processing_time=processing_time,
                metadata={
                    "retrieval_strategy": retrieval_strategy,
                    "num_retrieved": retrieval_result.num_results,
                    "session_id": session_id,
                    "llm_provider": self.llm_manager.provider_name,
                },
            )
            
            logger.info(f"Query processed in {processing_time:.2f}s")
            return rag_response
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            raise LLMError(
                f"Failed to process query: {e}",
                details={"query": question}
            )
    
    def _query_with_knowledge_features(
        self,
        question: str,
        session_id: str,
        k: Optional[int],
        include_sources: bool,
        chat_history: str,
        start_time: datetime,
    ) -> RAGResponse:
        """
        Process query with knowledge-aware features.
        
        This internal method handles:
        - Feature 1: Tacit knowledge prioritization
        - Feature 2: Decision traceability
        - Feature 3: Knowledge gap detection
        
        Args:
            question: The question to answer.
            session_id: Session ID for memory.
            k: Number of documents to retrieve.
            include_sources: Whether to include sources.
            chat_history: Formatted chat history.
            start_time: Query start time.
            
        Returns:
            RAGResponse with knowledge-aware metadata.
        """
        # Step 1: Knowledge-aware retrieval
        retrieval_result: KnowledgeAwareRetrievalResult = self.knowledge_retriever.retrieve(
            query=question,
            k=k,
            apply_knowledge_boost=True,
        )
        
        # Step 2: Extract knowledge metadata
        query_type = retrieval_result.query_type
        gap_result = retrieval_result.gap_result
        validation_result = retrieval_result.validation_result
        
        # Step 3: Check for knowledge gap (Feature 3)
        knowledge_gap_detected = False
        gap_severity = None
        validation_warnings = []
        
        if gap_result and gap_result.gap_detected:
            knowledge_gap_detected = True
            gap_severity = gap_result.gap_severity.value if gap_result.gap_severity else None
            
            # For high/critical gaps, return safe response without LLM generation
            if gap_result.gap_severity in [GapSeverity.HIGH, GapSeverity.CRITICAL]:
                processing_time = (datetime.now() - start_time).total_seconds()
                
                return RAGResponse(
                    answer=gap_result.safe_response,
                    source_documents=[],
                    query=question,
                    confidence=gap_result.confidence_score,
                    processing_time=processing_time,
                    metadata={
                        "retrieval_strategy": "knowledge_aware",
                        "num_retrieved": 0,
                        "session_id": session_id,
                        "knowledge_features_used": True,
                    },
                    query_type=query_type,
                    knowledge_gap_detected=True,
                    gap_severity=gap_severity,
                    validation_warnings=["Knowledge gap detected - safe response returned"],
                    knowledge_types_used=[],
                )
        
        # Step 4: Collect validation warnings
        if validation_result:
            validation_warnings = validation_result.warnings
            if validation_result.response_guidance:
                validation_warnings.append(f"Guidance: {validation_result.response_guidance}")
        
        # Step 5: Format context with knowledge indicators
        context = self.knowledge_retriever.format_context(
            documents=retrieval_result.documents,
            include_metadata=True,
            emphasize_knowledge_type=True,
        )
        
        # Step 6: Select appropriate prompt based on query type
        prompt = self.prompt_manager.get_prompt_for_query_type(
            query_type=query_type,
            has_gap_warning=knowledge_gap_detected,
        )
        
        # Step 7: Format prompt
        if query_type == "tacit":
            formatted_prompt = prompt.format(
                context=context,
                question=question,
            )
        elif query_type == "decision":
            formatted_prompt = prompt.format(
                context=context,
                question=question,
            )
        elif knowledge_gap_detected:
            # Use gap-aware prompt with additional guidance
            additional_guidance = (
                "WARNING: Limited knowledge coverage detected. "
                "Be especially conservative and acknowledge gaps."
            )
            formatted_prompt = prompt.format(
                context=context,
                question=question,
                additional_guidance=additional_guidance,
            )
        else:
            formatted_prompt = prompt.format(
                context=context,
                question=question,
            )
        
        # Add chat history if available
        if chat_history:
            formatted_prompt = f"Previous conversation:\n{chat_history}\n\n{formatted_prompt}"
        
        # Step 8: Generate answer
        llm = self.llm_manager.get_llm()
        response = llm.invoke(formatted_prompt)
        
        if hasattr(response, 'content'):
            answer = response.content
        else:
            answer = str(response)
        
        # Step 9: Update conversation memory
        self.memory_manager.add_exchange(
            session_id=session_id,
            human_message=question,
            ai_message=answer,
        )
        
        # Step 10: Calculate processing time and confidence
        processing_time = (datetime.now() - start_time).total_seconds()
        confidence = gap_result.confidence_score if gap_result else None
        
        # Step 11: Collect knowledge types used
        knowledge_types_used = list(set(
            doc.metadata.get("knowledge_type", "explicit")
            for doc in retrieval_result.documents
        ))
        
        # Step 12: Build response
        rag_response = RAGResponse(
            answer=answer,
            source_documents=retrieval_result.documents if include_sources else [],
            query=question,
            confidence=confidence,
            processing_time=processing_time,
            metadata={
                "retrieval_strategy": "knowledge_aware",
                "num_retrieved": retrieval_result.num_results,
                "session_id": session_id,
                "llm_provider": self.llm_manager.provider_name,
                "knowledge_features_used": True,
                "tacit_docs": retrieval_result.tacit_count,
                "decision_docs": retrieval_result.decision_count,
                "explicit_docs": retrieval_result.explicit_count,
                "scores_adjusted": retrieval_result.scores_adjusted,
                "adjustment_reason": retrieval_result.adjustment_reason,
            },
            query_type=query_type,
            knowledge_gap_detected=knowledge_gap_detected,
            gap_severity=gap_severity,
            validation_warnings=validation_warnings,
            knowledge_types_used=knowledge_types_used,
        )
        
        logger.info(
            f"Query processed in {processing_time:.2f}s with knowledge features: "
            f"type={query_type}, gap={knowledge_gap_detected}, "
            f"tacit={retrieval_result.tacit_count}, decision={retrieval_result.decision_count}"
        )
        
        return rag_response
    
    def _format_chat_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for context."""
        formatted = []
        for exchange in history[-5:]:  # Last 5 exchanges
            formatted.append(f"Human: {exchange.get('human', '')}")
            formatted.append(f"Assistant: {exchange.get('ai', '')}")
        return "\n".join(formatted)
    
    def batch_query(
        self,
        questions: List[str],
        session_id: str = "default",
        **kwargs,
    ) -> List[RAGResponse]:
        """
        Process multiple questions.
        
        Args:
            questions: List of questions to process.
            session_id: Session ID for conversation memory.
            **kwargs: Additional arguments passed to query().
            
        Returns:
            List of RAGResponse objects.
        """
        responses = []
        for question in questions:
            try:
                response = self.query(question, session_id=session_id, **kwargs)
                responses.append(response)
            except Exception as e:
                logger.error(f"Failed to process question '{question}': {e}")
                responses.append(RAGResponse(
                    answer=f"Error processing query: {e}",
                    source_documents=[],
                    query=question,
                ))
        return responses
    
    def get_similar_documents(
        self,
        query: str,
        k: int = 5,
    ) -> List[Tuple[Document, float]]:
        """
        Get similar documents with scores without generating an answer.
        
        Args:
            query: Search query.
            k: Number of documents to retrieve.
            
        Returns:
            List of (document, score) tuples.
        """
        return self.retriever_manager.retrieve_with_scores(query, k=k)
    
    def clear_session_memory(self, session_id: str = "default") -> None:
        """Clear conversation memory for a session."""
        self.memory_manager.clear_history(session_id)
        logger.info(f"Cleared memory for session: {session_id}")
    
    def get_session_history(self, session_id: str = "default") -> List[Dict[str, str]]:
        """Get conversation history for a session."""
        return self.memory_manager.get_history(session_id)


# Global RAG chain instance
_rag_chain: Optional[RAGChain] = None


def get_rag_chain() -> RAGChain:
    """Get the global RAG chain instance."""
    global _rag_chain
    if _rag_chain is None:
        _rag_chain = RAGChain()
    return _rag_chain


def build_qa_chain() -> RAGChain:
    """
    Build and return a QA chain.
    
    This is a convenience function for backward compatibility.
    For production use, prefer the RAGChain class directly.
    
    Returns:
        Configured RAGChain instance.
    """
    return get_rag_chain()

