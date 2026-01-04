"""
Retriever Module for AI Knowledge Continuity System.

This module provides advanced retrieval strategies including
multi-query retrieval, contextual compression, and hybrid search.
"""

from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from config.settings import get_settings
from core.logger import get_logger
from core.exceptions import RetrievalError
from vector_store.create_store import VectorStoreManager, EmbeddingManager

logger = get_logger(__name__)


@dataclass
class RetrievalResult:
    """Container for retrieval results with metadata."""
    documents: List[Document]
    query: str
    retriever_type: str
    num_results: int
    
    def __repr__(self) -> str:
        return f"RetrievalResult(query='{self.query[:50]}...', num_results={self.num_results})"


class RetrieverManager:
    """
    Advanced retriever manager with multiple retrieval strategies.
    
    Features:
    - Basic similarity search
    - MMR (Maximal Marginal Relevance) for diversity
    - Multi-query retrieval for better recall
    - Contextual compression for relevance
    - Configurable filters and thresholds
    
    Example:
        >>> manager = RetrieverManager()
        >>> results = manager.retrieve("How do I deploy the application?")
        >>> for doc in results.documents:
        ...     print(doc.page_content[:100])
    """
    
    def __init__(
        self,
        vector_store_manager: Optional[VectorStoreManager] = None,
        llm=None,
    ):
        """
        Initialize the retriever manager.
        
        Args:
            vector_store_manager: Vector store manager instance.
            llm: LLM for advanced retrieval strategies (multi-query, compression).
        """
        self.settings = get_settings()
        self.vector_store_manager = vector_store_manager or VectorStoreManager()
        self.embedding_manager = EmbeddingManager()
        self._llm = llm
        
        self._retrievers: Dict[str, BaseRetriever] = {}
        
        logger.info("RetrieverManager initialized")
    
    def set_llm(self, llm) -> None:
        """Set the LLM for advanced retrieval strategies."""
        self._llm = llm
        # Clear cached retrievers that depend on LLM
        self._retrievers.pop("multi_query", None)
        self._retrievers.pop("compression", None)
    
    def get_base_retriever(
        self,
        search_type: str = "similarity",
        k: Optional[int] = None,
        **kwargs,
    ) -> BaseRetriever:
        """
        Get a basic retriever from the vector store.
        
        Args:
            search_type: Type of search ('similarity', 'mmr').
            k: Number of documents to retrieve.
            **kwargs: Additional search parameters.
            
        Returns:
            Configured retriever instance.
        """
        k = k or self.settings.RETRIEVER_K
        cache_key = f"base_{search_type}_{k}"
        
        if cache_key not in self._retrievers:
            self._retrievers[cache_key] = self.vector_store_manager.get_retriever(
                search_type=search_type,
                k=k,
                **kwargs,
            )
        
        return self._retrievers[cache_key]
    
    def get_mmr_retriever(
        self,
        k: Optional[int] = None,
        fetch_k: int = 20,
        lambda_mult: float = 0.5,
    ) -> BaseRetriever:
        """
        Get an MMR (Maximal Marginal Relevance) retriever.
        
        MMR balances relevance and diversity in results.
        
        Args:
            k: Number of documents to return.
            fetch_k: Number of documents to fetch before MMR reranking.
            lambda_mult: Balance between relevance (1) and diversity (0).
            
        Returns:
            MMR retriever instance.
        """
        k = k or self.settings.RETRIEVER_K
        
        return self.vector_store_manager.get_retriever(
            search_type="mmr",
            k=k,
            fetch_k=fetch_k,
            lambda_mult=lambda_mult,
        )
    
    # Advanced retrieval strategies commented out due to package availability
    # Uncomment when langchain-retrievers-multi-query and langchain-retrievers-contextual-compression are available
    
    # def get_multi_query_retriever(
    #     self,
    #     k: Optional[int] = None,
    # ) -> MultiQueryRetriever:
    #     """
    #     Get a multi-query retriever for improved recall.
    #     
    #     Generates multiple query variations to retrieve more relevant documents.
    #     Requires an LLM to be set.
    #     
    #     Args:
    #         k: Number of documents per query.
    #         
    #     Returns:
    #         Multi-query retriever instance.
    #     """
    #     if self._llm is None:
    #         raise RetrievalError(
    #             "LLM required for multi-query retriever",
    #             details={"suggestion": "Call set_llm() first"}
    #         )
    #     
    #     cache_key = "multi_query"
    #     
    #     if cache_key not in self._retrievers:
    #         base_retriever = self.get_base_retriever(k=k)
    #         
    #         self._retrievers[cache_key] = MultiQueryRetriever.from_llm(
    #             retriever=base_retriever,
    #             llm=self._llm,
    #         )
    #     
    #     return self._retrievers[cache_key]
    
    # def get_compression_retriever(
    #     self,
    #     k: Optional[int] = None,
    #     similarity_threshold: float = 0.7,
    # ) -> ContextualCompressionRetriever:
    #     """
    #     Get a contextual compression retriever.
    #     
    #     Compresses documents to only include relevant content.
    #     
    #     Args:
    #         k: Number of documents to retrieve.
    #         similarity_threshold: Minimum similarity for filtering.
    #         
    #     Returns:
    #         Compression retriever instance.
    #     """
    #     base_retriever = self.get_base_retriever(k=k)
    #     embeddings = self.embedding_manager.get_embeddings()
    #     
    #     # Create embeddings filter
    #     embeddings_filter = EmbeddingsFilter(
    #         embeddings=embeddings,
    #         similarity_threshold=similarity_threshold,
    #     )
    #     
    #     # Create compressor pipeline
    #     compressor = DocumentCompressorPipeline(
    #         transformers=[embeddings_filter]
    #     )
    #     
    #     return ContextualCompressionRetriever(
    #         base_compressor=compressor,
    #         base_retriever=base_retriever,
    #     )
    
    def retrieve(
        self,
        query: str,
        strategy: str = "similarity",
        k: Optional[int] = None,
        **kwargs,
    ) -> RetrievalResult:
        """
        Retrieve documents using the specified strategy.
        
        Args:
            query: Search query.
            strategy: Retrieval strategy ('similarity', 'mmr').
            k: Number of documents to retrieve.
            **kwargs: Additional strategy-specific parameters.
            
        Returns:
            RetrievalResult containing documents and metadata.
        """
        logger.info(f"Retrieving with strategy '{strategy}': {query[:50]}...")
        
        try:
            # Select retriever based on strategy
            if strategy == "similarity":
                retriever = self.get_base_retriever(k=k, **kwargs)
            elif strategy == "mmr":
                retriever = self.get_mmr_retriever(k=k, **kwargs)
            elif strategy in ["multi_query", "compression"]:
                # These strategies require additional packages not currently available
                # Fall back to similarity search
                logger.warning(f"Strategy '{strategy}' not available, using 'similarity' instead")
                retriever = self.get_base_retriever(k=k, **kwargs)
                strategy = "similarity"
            else:
                raise RetrievalError(
                    f"Unknown retrieval strategy: {strategy}",
                    details={"valid": ["similarity", "mmr"]}
                )
            
            # Retrieve documents
            documents = retriever.invoke(query)
            
            result = RetrievalResult(
                documents=documents,
                query=query,
                retriever_type=strategy,
                num_results=len(documents),
            )
            
            logger.info(f"Retrieved {result.num_results} documents")
            return result
            
        except Exception as e:
            raise RetrievalError(
                f"Retrieval failed: {e}",
                details={"query": query, "strategy": strategy}
            )
    
    def retrieve_with_scores(
        self,
        query: str,
        k: Optional[int] = None,
        score_threshold: Optional[float] = None,
    ) -> List[tuple]:
        """
        Retrieve documents with similarity scores.
        
        Args:
            query: Search query.
            k: Number of documents to retrieve.
            score_threshold: Minimum similarity score.
            
        Returns:
            List of (document, score) tuples.
        """
        return self.vector_store_manager.search(
            query=query,
            k=k,
            score_threshold=score_threshold,
        )
    
    def get_relevant_documents(
        self,
        query: str,
        k: Optional[int] = None,
    ) -> List[Document]:
        """
        Simple interface to get relevant documents.
        
        Args:
            query: Search query.
            k: Number of documents to retrieve.
            
        Returns:
            List of relevant documents.
        """
        result = self.retrieve(query, strategy="similarity", k=k)
        return result.documents
    
    def format_context(
        self,
        documents: List[Document],
        max_length: Optional[int] = None,
        include_metadata: bool = True,
    ) -> str:
        """
        Format retrieved documents into a context string.
        
        Args:
            documents: List of documents to format.
            max_length: Maximum context length (optional).
            include_metadata: Whether to include source metadata.
            
        Returns:
            Formatted context string.
        """
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            # Build document section
            section = f"[Document {i}]"
            
            if include_metadata:
                source = doc.metadata.get("source", "Unknown")
                section += f"\nSource: {source}"
            
            section += f"\n{doc.page_content}"
            context_parts.append(section)
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Truncate if needed
        if max_length and len(context) > max_length:
            context = context[:max_length] + "\n\n[Context truncated...]"
        
        return context
