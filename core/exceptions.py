"""
Custom exceptions for the AI Knowledge Continuity System.
Provides specific error types for different failure scenarios.
"""


class KnowledgeSystemError(Exception):
    """Base exception for all Knowledge System errors."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(KnowledgeSystemError):
    """Raised when there's a configuration issue."""
    pass


class DocumentLoadError(KnowledgeSystemError):
    """Raised when document loading fails."""
    pass


class ChunkingError(KnowledgeSystemError):
    """Raised when document chunking fails."""
    pass


class VectorStoreError(KnowledgeSystemError):
    """Raised when vector store operations fail."""
    pass


class EmbeddingError(KnowledgeSystemError):
    """Raised when embedding generation fails."""
    pass


class LLMError(KnowledgeSystemError):
    """Raised when LLM operations fail."""
    pass


class RetrievalError(KnowledgeSystemError):
    """Raised when document retrieval fails."""
    pass


class MemoryError(KnowledgeSystemError):
    """Raised when conversation memory operations fail."""
    pass
