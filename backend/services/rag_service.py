"""
RAG Service - Adapter layer over RAGChain.

Provides async-safe access to the RAG system's query capabilities,
wrapping the synchronous LLM calls in thread pool executors.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from backend.core.config import api_settings
from backend.core.exceptions import (
    RAGServiceError,
    TimeoutError,
    KnowledgeGapError,
    ServiceUnavailableError,
)
from backend.core.logging import get_logger
from backend.schemas.query import (
    QueryRequest,
    QueryResponse,
    SourceDocument,
    DecisionTrace,
    KnowledgeGapInfo,
    KnowledgeType,
)


logger = get_logger(__name__)


class RAGService:
    """
    Service adapter for the RAGChain.
    
    Provides async-safe access to the synchronous RAG system,
    handling thread pool execution, timeouts, and error mapping.
    
    Design Decisions:
    - Uses ThreadPoolExecutor for blocking LLM calls
    - Implements timeout handling at service level
    - Maps RAG exceptions to API exceptions
    - Extracts and formats knowledge features from RAG response
    """
    
    def __init__(
        self,
        rag_chain: Any,
        executor: Optional[ThreadPoolExecutor] = None,
        max_workers: int = 4,
    ):
        """
        Initialize RAG Service.
        
        Args:
            rag_chain: Initialized RAGChain instance
            executor: Optional thread pool executor
            max_workers: Max worker threads for blocking calls
        """
        self._rag_chain = rag_chain
        self._executor = executor or ThreadPoolExecutor(max_workers=max_workers)
        self._query_timeout = api_settings.QUERY_TIMEOUT
        
        logger.info(
            "RAG Service initialized",
            extra={"max_workers": max_workers, "timeout": self._query_timeout}
        )
    
    async def query(
        self,
        request: QueryRequest,
        user_id: Optional[int] = None,
    ) -> QueryResponse:
        """
        Execute a query against the RAG system.
        
        Args:
            request: Query request with question and options
            
        Returns:
            QueryResponse with answer and knowledge features
            
        Raises:
            TimeoutError: Query exceeded timeout
            KnowledgeGapError: Knowledge gap detected (also returns response)
            RAGServiceError: Underlying RAG system error
        """
        start_time = time.perf_counter()
        
        logger.info(
            "Processing query",
            extra={
                "question_length": len(request.question),
                "role": request.role.value if request.role else None,
                "use_features": request.use_knowledge_features,
            }
        )
        
        try:
            # Run blocking RAG query in thread pool with timeout
            loop = asyncio.get_event_loop()
            
            raw_response = await asyncio.wait_for(
                loop.run_in_executor(
                    self._executor,
                    self._execute_query,
                    request,
                    user_id,
                ),
                timeout=self._query_timeout,
            )
            
            # Calculate processing time
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            
            # Transform RAG response to API response
            response = self._transform_response(
                raw_response,
                request,
                processing_time_ms,
            )
            
            logger.info(
                "Query completed",
                extra={
                    "processing_time_ms": processing_time_ms,
                    "gap_detected": response.knowledge_gap.detected,
                    "confidence": response.confidence,
                }
            )
            
            return response
            
        except asyncio.TimeoutError:
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Query timeout",
                extra={"timeout": self._query_timeout, "elapsed_ms": processing_time_ms}
            )
            raise TimeoutError(
                message=f"Query timed out after {self._query_timeout}s",
                details={"timeout_seconds": self._query_timeout}
            )
        except Exception as e:
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "Query failed",
                extra={"error": str(e), "elapsed_ms": processing_time_ms}
            )
            raise RAGServiceError(
                message=f"RAG query failed: {str(e)}",
                details={"original_error": str(e)}
            )
    
    def _execute_query(self, request: QueryRequest, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute query synchronously (called in thread pool).
        
        Args:
            request: Query request
            user_id: User ID for per-user retrieval
            
        Returns:
            Raw response dictionary from RAGChain
        """
        use_features = (
            request.use_knowledge_features and 
            api_settings.ENABLE_KNOWLEDGE_FEATURES
        )
        
        # Use the public query method with all parameters
        response = self._rag_chain.query(
            question=request.question,
            session_id=request.conversation_id or "default",
            k=None,  # Use default
            include_sources=True,
            use_memory=request.conversation_id is not None,
            use_knowledge_features=use_features,
            user_id=user_id,
        )
        
        # Convert RAGResponse dataclass to dict
        if hasattr(response, "to_dict"):
            result = response.to_dict()
        elif hasattr(response, "__dataclass_fields__"):
            result = asdict(response)
        else:
            result = response
        
        # Map RAGResponse fields to our expected format
        return {
            "answer": result.get("answer", ""),
            "source_documents": getattr(response, "source_documents", []),
            "query_type": result.get("query_type", "general"),
            "knowledge_types_used": result.get("knowledge_types_used", []),
            "tacit_knowledge_used": "tacit" in result.get("knowledge_types_used", []),
            "decision_trace": result.get("metadata", {}).get("decision_trace"),
            "gap_detected": result.get("knowledge_gap_detected", False),
            "gap_info": {
                "severity": result.get("gap_severity"),
                "reason": None,
            } if result.get("knowledge_gap_detected") else None,
            "confidence_score": result.get("confidence", 1.0),
            "warnings": result.get("validation_warnings", []),
        }
    
    def _transform_response(
        self,
        raw_response: Dict[str, Any],
        request: QueryRequest,
        processing_time_ms: float,
    ) -> QueryResponse:
        """
        Transform RAG response to API response schema.
        
        Args:
            raw_response: Raw response from RAGChain
            request: Original request
            processing_time_ms: Query processing time
            
        Returns:
            Formatted QueryResponse
        """
        # Extract source documents
        sources = self._extract_sources(raw_response.get("source_documents", []))
        
        # Extract decision trace if present
        decision_trace = self._extract_decision_trace(
            raw_response.get("decision_trace")
        )
        
        # Build knowledge gap info
        gap_info = raw_response.get("gap_info", {})
        confidence_score = raw_response.get("confidence_score", 1.0)
        
        knowledge_gap = KnowledgeGapInfo(
            detected=raw_response.get("gap_detected", False),
            severity=gap_info.get("severity") if gap_info else None,
            confidence_score=confidence_score,
            reason=gap_info.get("reason") if gap_info else None,
        )
        
        # Build response
        return QueryResponse(
            answer=raw_response.get("answer", ""),
            query=request.question,
            sources=sources,
            query_type=raw_response.get("query_type", "general"),
            knowledge_types_used=raw_response.get("knowledge_types_used", []),
            tacit_knowledge_used=raw_response.get("tacit_knowledge_used", False),
            decision_trace=decision_trace,
            knowledge_gap=knowledge_gap,
            warnings=raw_response.get("warnings", []),
            confidence=confidence_score,
            processing_time_ms=processing_time_ms,
        )
    
    def _extract_sources(
        self,
        source_documents: List[Any],
    ) -> List[SourceDocument]:
        """
        Extract and format source documents.
        
        Args:
            source_documents: Raw source documents from RAG
            
        Returns:
            List of formatted SourceDocument objects
        """
        sources = []
        
        for doc in source_documents[:10]:  # Limit to 10 sources
            try:
                # Handle LangChain Document objects
                if hasattr(doc, "page_content"):
                    content = doc.page_content
                    metadata = doc.metadata if hasattr(doc, "metadata") else {}
                elif isinstance(doc, dict):
                    content = doc.get("content", doc.get("page_content", ""))
                    metadata = doc.get("metadata", {})
                else:
                    content = str(doc)
                    metadata = {}
                
                # Detect knowledge type
                knowledge_type = self._detect_knowledge_type(metadata, content)
                
                sources.append(SourceDocument(
                    source=metadata.get("source", "unknown"),
                    content_preview=content[:300] + "..." if len(content) > 300 else content,
                    knowledge_type=knowledge_type,
                    relevance_score=metadata.get("score"),
                    decision_id=metadata.get("decision_id"),
                    decision_author=metadata.get("author"),
                    decision_date=metadata.get("date"),
                ))
            except Exception as e:
                logger.warning(f"Failed to extract source: {e}")
                continue
        
        return sources
    
    def _detect_knowledge_type(
        self,
        metadata: Dict[str, Any],
        content: str,
    ) -> KnowledgeType:
        """
        Detect knowledge type from metadata or content.
        
        Args:
            metadata: Document metadata
            content: Document content
            
        Returns:
            Detected KnowledgeType
        """
        # Check metadata first
        if "knowledge_type" in metadata:
            kt = metadata["knowledge_type"].lower()
            if kt == "tacit":
                return KnowledgeType.TACIT
            elif kt == "decision":
                return KnowledgeType.DECISION
            elif kt == "explicit":
                return KnowledgeType.EXPLICIT
        
        # Infer from source name
        source = metadata.get("source", "").lower()
        if "decision" in source or "adr" in source:
            return KnowledgeType.DECISION
        elif any(x in source for x in ["lesson", "retrospective", "exit", "handoff"]):
            return KnowledgeType.TACIT
        
        # Infer from content patterns
        content_lower = content.lower()
        if "lesson learned" in content_lower or "in my experience" in content_lower:
            return KnowledgeType.TACIT
        elif "decision:" in content_lower or "rationale:" in content_lower:
            return KnowledgeType.DECISION
        
        return KnowledgeType.EXPLICIT
    
    def _extract_decision_trace(
        self,
        decision_trace: Optional[Dict[str, Any]],
    ) -> Optional[DecisionTrace]:
        """
        Extract decision trace information.
        
        Args:
            decision_trace: Raw decision trace from RAG
            
        Returns:
            Formatted DecisionTrace or None
        """
        if not decision_trace:
            return None
        
        try:
            return DecisionTrace(
                decision_id=decision_trace.get("decision_id"),
                title=decision_trace.get("title"),
                author=decision_trace.get("author"),
                date=decision_trace.get("date"),
                rationale=decision_trace.get("rationale"),
                alternatives=decision_trace.get("alternatives", []),
                tradeoffs=decision_trace.get("tradeoffs", []),
            )
        except Exception as e:
            logger.warning(f"Failed to extract decision trace: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check RAG service health.
        
        Returns:
            Health check result dictionary
        """
        try:
            start = time.perf_counter()
            
            # Simple test query
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(
                    self._executor,
                    lambda: self._rag_chain.query("test"),
                ),
                timeout=10.0,
            )
            
            latency = (time.perf_counter() - start) * 1000
            
            return {
                "status": "healthy",
                "latency_ms": latency,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }
    
    def shutdown(self):
        """Clean up resources."""
        if self._executor:
            self._executor.shutdown(wait=False)
            logger.info("RAG Service executor shut down")
