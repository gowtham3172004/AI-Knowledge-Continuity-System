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


class KnowledgeGapError(KnowledgeSystemError):
    """
    Raised when a knowledge gap is detected and the system cannot
    provide a confident answer. This is used to prevent hallucinations.
    """
    def __init__(
        self,
        message: str,
        gap_severity: str = "medium",
        confidence_score: float = 0.0,
        safe_response: str = None,
        details: dict = None,
    ):
        super().__init__(message, details)
        self.gap_severity = gap_severity
        self.confidence_score = confidence_score
        self.safe_response = safe_response or (
            "I don't have sufficient information in the knowledge base "
            "to answer this question confidently."
        )


class KnowledgeClassificationError(KnowledgeSystemError):
    """Raised when knowledge classification fails."""
    pass


class DecisionParsingError(KnowledgeSystemError):
    """Raised when decision metadata extraction fails."""
    pass


class ValidationError(KnowledgeSystemError):
    """Raised when knowledge validation fails."""
    pass
