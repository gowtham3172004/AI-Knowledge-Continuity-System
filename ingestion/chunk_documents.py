"""
Document Chunking Module for AI Knowledge Continuity System.

This module provides intelligent text chunking with support for
multiple strategies, metadata preservation, and semantic coherence.
"""

from typing import List, Optional, Literal
from dataclasses import dataclass

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter,
)
from langchain_core.documents import Document
from tqdm import tqdm

from config.settings import get_settings
from core.logger import get_logger
from core.exceptions import ChunkingError

logger = get_logger(__name__)


ChunkingStrategy = Literal["recursive", "character", "token"]


@dataclass
class ChunkMetrics:
    """Metrics about the chunking operation."""
    total_documents: int
    total_chunks: int
    avg_chunk_size: float
    min_chunk_size: int
    max_chunk_size: int
    
    def __str__(self) -> str:
        return (
            f"ChunkMetrics(docs={self.total_documents}, chunks={self.total_chunks}, "
            f"avg_size={self.avg_chunk_size:.1f}, min={self.min_chunk_size}, max={self.max_chunk_size})"
        )


class DocumentChunker:
    """
    Production-grade document chunker with multiple strategies.
    
    Features:
    - Multiple chunking strategies (recursive, character, token-based)
    - Metadata preservation and enrichment
    - Configurable chunk sizes and overlaps
    - Semantic separators for better coherence
    - Chunk deduplication option
    - Progress tracking
    
    Example:
        >>> chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
        >>> chunks = chunker.chunk(documents)
        >>> print(f"Created {len(chunks)} chunks")
    """
    
    # Semantic separators ordered by priority (most important first)
    SEMANTIC_SEPARATORS = [
        "\n\n\n",      # Multiple blank lines (major sections)
        "\n\n",        # Paragraph breaks
        "\n",          # Line breaks
        ". ",          # Sentence endings
        "? ",          # Question endings
        "! ",          # Exclamation endings
        "; ",          # Semicolon breaks
        ", ",          # Comma breaks
        " ",           # Word breaks
        "",            # Character level (last resort)
    ]
    
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        strategy: ChunkingStrategy = "recursive",
        show_progress: bool = True,
        deduplicate: bool = False,
    ):
        """
        Initialize the document chunker.
        
        Args:
            chunk_size: Maximum size of each chunk. Defaults to config setting.
            chunk_overlap: Overlap between consecutive chunks. Defaults to config setting.
            strategy: Chunking strategy to use ('recursive', 'character', 'token').
            show_progress: Whether to show progress bar during chunking.
            deduplicate: Whether to remove duplicate chunks.
        """
        self.settings = get_settings()
        self.chunk_size = chunk_size or self.settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or self.settings.CHUNK_OVERLAP
        self.strategy = strategy
        self.show_progress = show_progress
        self.deduplicate = deduplicate
        
        # Validate parameters
        if self.chunk_overlap >= self.chunk_size:
            raise ChunkingError(
                "chunk_overlap must be less than chunk_size",
                details={
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap
                }
            )
        
        # Initialize the appropriate splitter
        self.splitter = self._create_splitter()
        
        logger.info(
            f"DocumentChunker initialized: strategy={strategy}, "
            f"chunk_size={self.chunk_size}, overlap={self.chunk_overlap}"
        )
    
    def _create_splitter(self):
        """Create the appropriate text splitter based on strategy."""
        if self.strategy == "recursive":
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=self.SEMANTIC_SEPARATORS,
                length_function=len,
                is_separator_regex=False,
            )
        elif self.strategy == "character":
            return CharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separator="\n\n",
                length_function=len,
            )
        elif self.strategy == "token":
            return TokenTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
        else:
            raise ChunkingError(
                f"Unknown chunking strategy: {self.strategy}",
                details={"valid_strategies": ["recursive", "character", "token"]}
            )
    
    def _enrich_chunk_metadata(
        self,
        chunk: Document,
        chunk_index: int,
        total_chunks_for_doc: int,
        parent_doc_id: int,
    ) -> Document:
        """
        Enrich chunk metadata with additional information.
        
        Args:
            chunk: The chunk to enrich.
            chunk_index: Index of this chunk within its parent document.
            total_chunks_for_doc: Total chunks created from parent document.
            parent_doc_id: ID of the parent document.
            
        Returns:
            Chunk with enriched metadata.
        """
        chunk.metadata.update({
            "chunk_index": chunk_index,
            "total_chunks_in_doc": total_chunks_for_doc,
            "parent_doc_id": parent_doc_id,
            "chunk_size": len(chunk.page_content),
            "is_first_chunk": chunk_index == 0,
            "is_last_chunk": chunk_index == total_chunks_for_doc - 1,
        })
        
        return chunk
    
    def chunk(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into semantically meaningful chunks.
        
        Args:
            documents: List of documents to chunk.
            
        Returns:
            List of chunked documents with enriched metadata.
            
        Raises:
            ChunkingError: If chunking fails.
        """
        if not documents:
            raise ChunkingError("No documents provided for chunking")
        
        logger.info(f"Starting chunking of {len(documents)} documents")
        
        all_chunks: List[Document] = []
        global_chunk_id = 0
        
        # Process documents with progress tracking
        doc_iterator = tqdm(
            enumerate(documents),
            total=len(documents),
            desc="Chunking documents",
            disable=not self.show_progress
        )
        
        for doc_id, doc in doc_iterator:
            try:
                # Split the document
                doc_chunks = self.splitter.split_documents([doc])
                
                # Enrich metadata for each chunk
                for i, chunk in enumerate(doc_chunks):
                    chunk = self._enrich_chunk_metadata(
                        chunk=chunk,
                        chunk_index=i,
                        total_chunks_for_doc=len(doc_chunks),
                        parent_doc_id=doc_id,
                    )
                    chunk.metadata["global_chunk_id"] = global_chunk_id
                    global_chunk_id += 1
                
                all_chunks.extend(doc_chunks)
                
            except Exception as e:
                logger.warning(
                    f"Failed to chunk document {doc_id}: {e}. Skipping."
                )
                continue
        
        # Deduplicate if requested
        if self.deduplicate:
            original_count = len(all_chunks)
            all_chunks = self._deduplicate_chunks(all_chunks)
            logger.info(
                f"Deduplication: {original_count} -> {len(all_chunks)} chunks"
            )
        
        # Calculate and log metrics
        metrics = self._calculate_metrics(documents, all_chunks)
        logger.info(f"Chunking complete: {metrics}")
        
        return all_chunks
    
    def _deduplicate_chunks(self, chunks: List[Document]) -> List[Document]:
        """Remove duplicate chunks based on content."""
        seen_content = set()
        unique_chunks = []
        
        for chunk in chunks:
            # Normalize content for comparison
            normalized = chunk.page_content.strip().lower()
            content_hash = hash(normalized)
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_chunks.append(chunk)
        
        return unique_chunks
    
    def _calculate_metrics(
        self,
        original_docs: List[Document],
        chunks: List[Document]
    ) -> ChunkMetrics:
        """Calculate metrics about the chunking operation."""
        if not chunks:
            return ChunkMetrics(
                total_documents=len(original_docs),
                total_chunks=0,
                avg_chunk_size=0,
                min_chunk_size=0,
                max_chunk_size=0,
            )
        
        chunk_sizes = [len(c.page_content) for c in chunks]
        
        return ChunkMetrics(
            total_documents=len(original_docs),
            total_chunks=len(chunks),
            avg_chunk_size=sum(chunk_sizes) / len(chunk_sizes),
            min_chunk_size=min(chunk_sizes),
            max_chunk_size=max(chunk_sizes),
        )
    
    def get_chunk_preview(
        self,
        chunks: List[Document],
        num_samples: int = 3,
        max_length: int = 200
    ) -> List[str]:
        """
        Get a preview of chunks for inspection.
        
        Args:
            chunks: List of chunks to preview.
            num_samples: Number of samples to return.
            max_length: Maximum length of each preview.
            
        Returns:
            List of chunk previews.
        """
        samples = chunks[:num_samples]
        previews = []
        
        for i, chunk in enumerate(samples):
            content = chunk.page_content[:max_length]
            if len(chunk.page_content) > max_length:
                content += "..."
            previews.append(f"[Chunk {i}] {content}")
        
        return previews


# Convenience function for backward compatibility
def chunk_documents(
    documents: List[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[Document]:
    """
    Split documents into semantically meaningful chunks.
    
    This is a convenience function for backward compatibility.
    For production use, prefer the DocumentChunker class.
    
    Args:
        documents: List of documents to chunk.
        chunk_size: Maximum size of each chunk.
        chunk_overlap: Overlap between chunks.
        
    Returns:
        List of chunked documents.
    """
    chunker = DocumentChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return chunker.chunk(documents)
