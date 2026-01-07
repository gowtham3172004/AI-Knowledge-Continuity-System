"""
Ingestion Service - Adapter layer for document ingestion.

Provides async-safe access to the document ingestion pipeline,
including loading, chunking, classification, and vector store indexing.
"""

import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from backend.core.config import api_settings
from backend.core.exceptions import (
    RAGServiceError,
    TimeoutError,
    ValidationError,
)
from backend.core.logging import get_logger
from backend.schemas.ingest import (
    IngestRequest,
    IngestResponse,
    IngestDocumentResult,
    IngestSource,
)


logger = get_logger(__name__)


class IngestService:
    """
    Service adapter for document ingestion.
    
    Provides async-safe access to the document ingestion pipeline,
    coordinating document loading, chunking, classification, and indexing.
    
    Design Decisions:
    - Uses ThreadPoolExecutor for blocking I/O operations
    - Implements progress tracking for long-running ingestion
    - Maps ingestion exceptions to API exceptions
    - Supports multiple ingestion modes (directory, files, text)
    """
    
    def __init__(
        self,
        vector_store_manager: Any,
        executor: Optional[ThreadPoolExecutor] = None,
        max_workers: int = 2,
    ):
        """
        Initialize Ingestion Service.
        
        Args:
            vector_store_manager: Initialized VectorStoreManager instance
            executor: Optional thread pool executor
            max_workers: Max worker threads for blocking calls
        """
        self._vector_store = vector_store_manager
        self._executor = executor or ThreadPoolExecutor(max_workers=max_workers)
        self._ingest_timeout = api_settings.INGEST_TIMEOUT
        
        # Progress tracking
        self._is_indexing = False
        self._current_document: Optional[str] = None
        self._progress = 0.0
        self._documents_processed = 0
        self._documents_total = 0
        
        logger.info(
            "Ingest Service initialized",
            extra={"max_workers": max_workers, "timeout": self._ingest_timeout}
        )
    
    async def ingest(
        self,
        request: IngestRequest,
    ) -> IngestResponse:
        """
        Execute document ingestion.
        
        Args:
            request: Ingestion request with source and options
            
        Returns:
            IngestResponse with ingestion results
            
        Raises:
            TimeoutError: Ingestion exceeded timeout
            ValidationError: Invalid request parameters
            RAGServiceError: Underlying service error
        """
        start_time = time.perf_counter()
        
        logger.info(
            "Starting ingestion",
            extra={
                "source": request.source.value,
                "force_reindex": request.force_reindex,
            }
        )
        
        # Validate request
        self._validate_request(request)
        
        try:
            self._is_indexing = True
            
            # Run blocking ingestion in thread pool with timeout
            loop = asyncio.get_event_loop()
            
            results = await asyncio.wait_for(
                loop.run_in_executor(
                    self._executor,
                    self._execute_ingestion,
                    request,
                ),
                timeout=self._ingest_timeout,
            )
            
            # Calculate processing time
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            
            # Build response
            response = self._build_response(results, processing_time_ms)
            
            logger.info(
                "Ingestion completed",
                extra={
                    "total_documents": response.total_documents,
                    "successful": response.successful,
                    "failed": response.failed,
                    "total_chunks": response.total_chunks,
                    "processing_time_ms": processing_time_ms,
                }
            )
            
            return response
            
        except asyncio.TimeoutError:
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Ingestion timeout",
                extra={"timeout": self._ingest_timeout, "elapsed_ms": processing_time_ms}
            )
            raise TimeoutError(
                message=f"Ingestion timed out after {self._ingest_timeout}s",
                details={"timeout_seconds": self._ingest_timeout}
            )
        except ValidationError:
            raise
        except Exception as e:
            processing_time_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "Ingestion failed",
                extra={"error": str(e), "elapsed_ms": processing_time_ms}
            )
            raise RAGServiceError(
                message=f"Ingestion failed: {str(e)}",
                details={"original_error": str(e)}
            )
        finally:
            self._is_indexing = False
            self._current_document = None
            self._progress = 0.0
    
    def _validate_request(self, request: IngestRequest) -> None:
        """
        Validate ingestion request.
        
        Args:
            request: Ingestion request
            
        Raises:
            ValidationError: If request is invalid
        """
        if request.source == IngestSource.DIRECTORY_SCAN:
            if not request.directory_path:
                raise ValidationError(
                    message="directory_path is required for directory scan",
                    field="directory_path"
                )
            if not os.path.isdir(request.directory_path):
                raise ValidationError(
                    message=f"Directory not found: {request.directory_path}",
                    field="directory_path"
                )
        
        elif request.source == IngestSource.FILE_UPLOAD:
            if not request.file_paths:
                raise ValidationError(
                    message="file_paths is required for file upload",
                    field="file_paths"
                )
            for path in request.file_paths:
                if not os.path.isfile(path):
                    raise ValidationError(
                        message=f"File not found: {path}",
                        field="file_paths"
                    )
        
        elif request.source == IngestSource.TEXT:
            if not request.text_content:
                raise ValidationError(
                    message="text_content is required for text ingestion",
                    field="text_content"
                )
    
    def _execute_ingestion(
        self,
        request: IngestRequest,
    ) -> List[Dict[str, Any]]:
        """
        Execute ingestion synchronously (called in thread pool).
        
        Args:
            request: Ingestion request
            
        Returns:
            List of per-document results
        """
        from ingestion.load_documents import DocumentLoader
        from ingestion.chunk_documents import DocumentChunker
        
        results = []
        
        # Initialize components
        loader = DocumentLoader()
        chunker = DocumentChunker(
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )
        
        # Get documents based on source
        if request.source == IngestSource.DIRECTORY_SCAN:
            documents = loader.load_directory(request.directory_path)
        elif request.source == IngestSource.FILE_UPLOAD:
            documents = []
            for path in request.file_paths:
                docs = loader.load_file(path)
                documents.extend(docs)
        elif request.source == IngestSource.TEXT:
            from langchain_core.documents import Document
            documents = [Document(
                page_content=request.text_content,
                metadata={"source": "text_input", **(request.metadata.model_dump() if request.metadata else {})}
            )]
        else:
            documents = []
        
        self._documents_total = len(documents)
        
        # Process each document
        total_chunks = 0
        for i, doc in enumerate(documents):
            self._current_document = doc.metadata.get("source", f"document_{i}")
            self._documents_processed = i
            self._progress = (i / max(len(documents), 1)) * 100
            
            try:
                # Chunk document
                chunks = chunker.split_documents([doc])
                
                # Add to vector store
                if chunks:
                    self._vector_store.add_documents(chunks)
                
                results.append({
                    "source": doc.metadata.get("source", f"document_{i}"),
                    "status": "success",
                    "chunks_created": len(chunks),
                    "knowledge_type": doc.metadata.get("knowledge_type"),
                })
                total_chunks += len(chunks)
                
            except Exception as e:
                logger.warning(f"Failed to ingest document: {e}")
                results.append({
                    "source": doc.metadata.get("source", f"document_{i}"),
                    "status": "failed",
                    "chunks_created": 0,
                    "knowledge_type": None,
                    "error": str(e),
                })
        
        self._documents_processed = len(documents)
        self._progress = 100.0
        
        return results
    
    def _build_response(
        self,
        results: List[Dict[str, Any]],
        processing_time_ms: float,
    ) -> IngestResponse:
        """
        Build ingestion response from results.
        
        Args:
            results: Per-document results
            processing_time_ms: Total processing time
            
        Returns:
            Formatted IngestResponse
        """
        successful = sum(1 for r in results if r["status"] == "success")
        failed = sum(1 for r in results if r["status"] == "failed")
        skipped = sum(1 for r in results if r["status"] == "skipped")
        total_chunks = sum(r["chunks_created"] for r in results)
        
        # Build knowledge type summary
        knowledge_types: Dict[str, int] = {}
        for r in results:
            if r.get("knowledge_type"):
                kt = r["knowledge_type"]
                knowledge_types[kt] = knowledge_types.get(kt, 0) + 1
        
        # Build document results
        documents = [
            IngestDocumentResult(
                source=r["source"],
                status=r["status"],
                chunks_created=r["chunks_created"],
                knowledge_type=r.get("knowledge_type"),
                error=r.get("error"),
            )
            for r in results
        ]
        
        return IngestResponse(
            status="completed" if failed == 0 else "completed_with_errors",
            total_documents=len(results),
            successful=successful,
            failed=failed,
            skipped=skipped,
            total_chunks=total_chunks,
            documents=documents,
            knowledge_type_summary=knowledge_types,
            processing_time_ms=processing_time_ms,
        )
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current ingestion status.
        
        Returns:
            Status dictionary
        """
        return {
            "is_indexing": self._is_indexing,
            "current_document": self._current_document,
            "progress": self._progress,
            "documents_processed": self._documents_processed,
            "documents_total": self._documents_total,
        }
    
    def shutdown(self):
        """Clean up resources."""
        if self._executor:
            self._executor.shutdown(wait=False)
            logger.info("Ingest Service executor shut down")
