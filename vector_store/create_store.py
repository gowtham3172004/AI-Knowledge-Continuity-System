"""
Vector Store Management Module for AI Knowledge Continuity System.

This module provides production-grade vector store operations including
creation, loading, updating, and searching with FAISS.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

from config.settings import get_settings
from core.logger import get_logger
from core.exceptions import VectorStoreError, EmbeddingError

logger = get_logger(__name__)


class EmbeddingManager:
    """
    Manages embedding model initialization and operations.
    
    Provides a singleton-like pattern for embedding model reuse
    to avoid repeated model loading.
    """
    
    _instance: Optional['EmbeddingManager'] = None
    _embeddings: Optional[HuggingFaceEmbeddings] = None
    
    def __new__(cls) -> 'EmbeddingManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.settings = get_settings()
    
    def get_embeddings(self) -> HuggingFaceEmbeddings:
        """
        Get or create the embedding model instance.
        
        Returns:
            Initialized HuggingFace embeddings model.
            
        Raises:
            EmbeddingError: If model initialization fails.
        """
        if self._embeddings is None:
            try:
                logger.info(f"Loading embedding model: {self.settings.EMBEDDING_MODEL}")
                
                self._embeddings = HuggingFaceEmbeddings(
                    model_name=self.settings.EMBEDDING_MODEL,
                    model_kwargs={"device": self.settings.EMBEDDING_DEVICE},
                    encode_kwargs={
                        "normalize_embeddings": True,  # For cosine similarity
                        "batch_size": 32,
                    },
                )
                
                logger.info("Embedding model loaded successfully")
                
            except Exception as e:
                raise EmbeddingError(
                    f"Failed to initialize embedding model: {e}",
                    details={"model": self.settings.EMBEDDING_MODEL}
                )
        
        return self._embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text."""
        embeddings = self.get_embeddings()
        return embeddings.embed_query(text)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents."""
        embeddings = self.get_embeddings()
        return embeddings.embed_documents(texts)


class VectorStoreManager:
    """
    Production-grade vector store manager for FAISS.
    
    Features:
    - Create, load, and update vector stores
    - Automatic backup on updates
    - Similarity search with score thresholds
    - Metadata filtering
    - Batch operations for large datasets
    
    Example:
        >>> manager = VectorStoreManager()
        >>> manager.create(chunks)
        >>> results = manager.search("How do I deploy?", k=5)
    """
    
    def __init__(
        self,
        store_path: Optional[str] = None,
        embedding_manager: Optional[EmbeddingManager] = None,
    ):
        """
        Initialize the vector store manager.
        
        Args:
            store_path: Path to save/load the vector store. Defaults to config.
            embedding_manager: Custom embedding manager instance.
        """
        self.settings = get_settings()
        self.store_path = Path(store_path or self.settings.VECTOR_STORE_PATH)
        self.embedding_manager = embedding_manager or EmbeddingManager()
        
        self._vectorstore: Optional[FAISS] = None
        
        # Ensure parent directory exists
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"VectorStoreManager initialized with path: {self.store_path}")
    
    @property
    def vectorstore(self) -> Optional[FAISS]:
        """Get the current vector store instance."""
        return self._vectorstore
    
    @property
    def is_loaded(self) -> bool:
        """Check if a vector store is currently loaded."""
        return self._vectorstore is not None
    
    @property
    def exists(self) -> bool:
        """Check if a vector store exists on disk."""
        index_file = self.store_path / "index.faiss"
        return index_file.exists()
    
    def create(
        self,
        documents: List[Document],
        batch_size: int = 500,
        show_progress: bool = True,
    ) -> FAISS:
        """
        Create a new vector store from documents.
        
        Args:
            documents: List of documents to index.
            batch_size: Number of documents to process per batch.
            show_progress: Whether to show progress during creation.
            
        Returns:
            Created FAISS vector store.
            
        Raises:
            VectorStoreError: If creation fails.
        """
        if not documents:
            raise VectorStoreError("No documents provided for vector store creation")
        
        logger.info(f"Creating vector store with {len(documents)} documents")
        
        try:
            embeddings = self.embedding_manager.get_embeddings()
            
            # Create vector store in batches for large datasets
            if len(documents) <= batch_size:
                self._vectorstore = FAISS.from_documents(
                    documents=documents,
                    embedding=embeddings,
                )
            else:
                logger.info(f"Processing in batches of {batch_size}")
                
                # Create initial store with first batch
                self._vectorstore = FAISS.from_documents(
                    documents=documents[:batch_size],
                    embedding=embeddings,
                )
                
                # Add remaining documents in batches
                for i in range(batch_size, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    self._vectorstore.add_documents(batch)
                    
                    if show_progress:
                        progress = min(i + batch_size, len(documents))
                        logger.info(f"Processed {progress}/{len(documents)} documents")
            
            # Save to disk
            self.save()
            
            logger.info(f"Vector store created successfully with {len(documents)} documents")
            return self._vectorstore
            
        except Exception as e:
            raise VectorStoreError(
                f"Failed to create vector store: {e}",
                details={"num_documents": len(documents)}
            )
    
    def load(self) -> FAISS:
        """
        Load an existing vector store from disk.
        
        Returns:
            Loaded FAISS vector store.
            
        Raises:
            VectorStoreError: If loading fails or store doesn't exist.
        """
        if not self.exists:
            raise VectorStoreError(
                "Vector store not found",
                details={"path": str(self.store_path)}
            )
        
        try:
            logger.info(f"Loading vector store from: {self.store_path}")
            
            embeddings = self.embedding_manager.get_embeddings()
            
            self._vectorstore = FAISS.load_local(
                str(self.store_path),
                embeddings,
                allow_dangerous_deserialization=True,
            )
            
            logger.info("Vector store loaded successfully")
            return self._vectorstore
            
        except Exception as e:
            raise VectorStoreError(
                f"Failed to load vector store: {e}",
                details={"path": str(self.store_path)}
            )
    
    def save(self, backup: bool = False) -> None:
        """
        Save the current vector store to disk.
        
        Args:
            backup: Whether to create a backup before saving.
        """
        if self._vectorstore is None:
            raise VectorStoreError("No vector store to save")
        
        if backup and self.exists:
            self._create_backup()
        
        try:
            self._vectorstore.save_local(str(self.store_path))
            logger.info(f"Vector store saved to: {self.store_path}")
            
        except Exception as e:
            raise VectorStoreError(
                f"Failed to save vector store: {e}",
                details={"path": str(self.store_path)}
            )
    
    def _create_backup(self) -> None:
        """Create a backup of the existing vector store."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.store_path.parent / f"{self.store_path.name}_backup_{timestamp}"
        
        try:
            shutil.copytree(self.store_path, backup_path)
            logger.info(f"Backup created at: {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
    
    def add_documents(
        self,
        documents: List[Document],
        save_after: bool = True,
    ) -> None:
        """
        Add new documents to an existing vector store.
        
        Args:
            documents: Documents to add.
            save_after: Whether to save after adding.
        """
        if self._vectorstore is None:
            if self.exists:
                self.load()
            else:
                raise VectorStoreError("No vector store exists. Create one first.")
        
        try:
            self._vectorstore.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to vector store")
            
            if save_after:
                self.save(backup=True)
                
        except Exception as e:
            raise VectorStoreError(
                f"Failed to add documents: {e}",
                details={"num_documents": len(documents)}
            )
    
    def search(
        self,
        query: str,
        k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[Document, float]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query.
            k: Number of results to return. Defaults to config.
            score_threshold: Minimum similarity score. Defaults to config.
            filter_metadata: Metadata filters to apply.
            
        Returns:
            List of (document, score) tuples.
        """
        if self._vectorstore is None:
            self.load()
        
        k = k or self.settings.RETRIEVER_K
        score_threshold = score_threshold or self.settings.RETRIEVER_SCORE_THRESHOLD
        
        try:
            # Search with scores
            results = self._vectorstore.similarity_search_with_score(
                query=query,
                k=k,
            )
            
            # Filter by score threshold
            filtered_results = [
                (doc, score) for doc, score in results
                if score >= score_threshold
            ]
            
            # Apply metadata filter if provided
            if filter_metadata:
                filtered_results = [
                    (doc, score) for doc, score in filtered_results
                    if all(
                        doc.metadata.get(key) == value
                        for key, value in filter_metadata.items()
                    )
                ]
            
            logger.debug(f"Search returned {len(filtered_results)} results for: {query[:50]}...")
            return filtered_results
            
        except Exception as e:
            raise VectorStoreError(
                f"Search failed: {e}",
                details={"query": query}
            )
    
    def get_retriever(
        self,
        search_type: str = "similarity",
        k: Optional[int] = None,
        **kwargs,
    ):
        """
        Get a LangChain retriever from the vector store.
        
        Args:
            search_type: Type of search ('similarity', 'mmr').
            k: Number of documents to retrieve.
            **kwargs: Additional retriever arguments.
            
        Returns:
            LangChain retriever instance.
        """
        if self._vectorstore is None:
            self.load()
        
        k = k or self.settings.RETRIEVER_K
        
        return self._vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k, **kwargs},
        )
    
    def delete(self, confirm: bool = False) -> None:
        """
        Delete the vector store from disk.
        
        Args:
            confirm: Must be True to actually delete.
        """
        if not confirm:
            logger.warning("Delete called without confirmation. Ignoring.")
            return
        
        if self.exists:
            shutil.rmtree(self.store_path)
            self._vectorstore = None
            logger.info(f"Vector store deleted: {self.store_path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        if self._vectorstore is None:
            if self.exists:
                self.load()
            else:
                return {"status": "not_created"}
        
        return {
            "status": "loaded",
            "path": str(self.store_path),
            "num_documents": len(self._vectorstore.docstore._dict),
            "embedding_model": self.settings.EMBEDDING_MODEL,
        }


# Convenience functions for backward compatibility
def create_vector_store(chunks: List[Document]) -> FAISS:
    """
    Create or update FAISS vector store.
    
    This is a convenience function for backward compatibility.
    For production use, prefer the VectorStoreManager class.
    """
    manager = VectorStoreManager()
    return manager.create(chunks)


def load_vector_store() -> FAISS:
    """
    Load existing FAISS store.
    
    This is a convenience function for backward compatibility.
    For production use, prefer the VectorStoreManager class.
    """
    manager = VectorStoreManager()
    return manager.load()
