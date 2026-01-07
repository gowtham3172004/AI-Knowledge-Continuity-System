"""
Configuration management for AI Knowledge Continuity System.
Uses Pydantic for validation and environment variable loading.
"""

import os
from functools import lru_cache
from typing import Literal, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    All settings can be overridden via environment variables or .env file.
    """

    # Application Settings
    APP_NAME: str = "AI Knowledge Continuity System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Data Paths
    DATA_DIR: str = Field(default="data", description="Directory containing organizational documents")
    VECTOR_STORE_PATH: str = Field(default="vector_store/faiss_index", description="Path to save/load vector store")

    # Embedding Configuration
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace embedding model name"
    )
    EMBEDDING_DEVICE: str = Field(default="cpu", description="Device for embeddings (cpu/cuda/mps)")

    # LLM Configuration
    LLM_PROVIDER: Literal["gemini", "local", "huggingface"] = Field(
        default="gemini",
        description="LLM provider to use"
    )
    
    # Gemini Configuration
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", description="Gemini model name")
    
    # Local LLM Configuration (for future use)
    LOCAL_LLM_MODEL: str = Field(
        default="mistralai/Mistral-7B-Instruct-v0.2",
        description="Local HuggingFace model for text generation"
    )
    LOCAL_LLM_DEVICE: str = Field(default="cpu", description="Device for local LLM")
    
    # HuggingFace Configuration
    HUGGINGFACE_API_KEY: Optional[str] = Field(default=None, description="HuggingFace API key")

    # Chunking Configuration
    CHUNK_SIZE: int = Field(default=1000, ge=100, le=4000, description="Size of text chunks")
    CHUNK_OVERLAP: int = Field(default=200, ge=0, le=500, description="Overlap between chunks")

    # Retrieval Configuration
    RETRIEVER_K: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    RETRIEVER_SCORE_THRESHOLD: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Minimum similarity score threshold"
    )
    
    # Knowledge Gap Detection Configuration
    KNOWLEDGE_GAP_THRESHOLD: float = Field(
        default=0.6, ge=0.0, le=1.0,
        description="Minimum confidence to proceed with answer generation"
    )
    KNOWLEDGE_GAP_MIN_DOCS: int = Field(
        default=2, ge=1, le=10,
        description="Minimum relevant documents required for confident answer"
    )
    ENABLE_GAP_DETECTION: bool = Field(
        default=True,
        description="Enable knowledge gap detection and safe responses"
    )
    
    # Knowledge Classification Configuration
    ENABLE_KNOWLEDGE_CLASSIFICATION: bool = Field(
        default=True,
        description="Enable automatic knowledge type classification"
    )
    TACIT_PRIORITY_BOOST: float = Field(
        default=1.3, ge=1.0, le=2.0,
        description="Score multiplier for tacit knowledge when query matches"
    )
    DECISION_PRIORITY_BOOST: float = Field(
        default=1.3, ge=1.0, le=2.0,
        description="Score multiplier for decision docs when query matches"
    )

    # LLM Generation Configuration
    MAX_NEW_TOKENS: int = Field(default=1024, ge=64, le=4096, description="Maximum tokens to generate")
    TEMPERATURE: float = Field(default=0.3, ge=0.0, le=2.0, description="Generation temperature")
    TOP_P: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling parameter")

    # Memory Configuration
    MAX_CONVERSATION_HISTORY: int = Field(default=10, ge=1, le=50, description="Max conversation turns to remember")

    # Streamlit UI Configuration
    UI_THEME: str = Field(default="light", description="UI theme (light/dark)")
    UI_PAGE_TITLE: str = Field(default="🧠 AI Knowledge Continuity System", description="Page title")

    @validator("GEMINI_API_KEY", pre=True, always=True)
    def validate_gemini_key(cls, v, values):
        """Validate Gemini API key when using Gemini provider."""
        if values.get("LLM_PROVIDER") == "gemini" and not v:
            # Allow None during initialization, will be checked at runtime
            pass
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()
