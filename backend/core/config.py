"""
Core configuration for FastAPI backend.

Extends the existing config.settings with API-specific settings.
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class APISettings(BaseSettings):
    """
    API-specific settings.
    
    Inherits environment variables and adds API-layer configuration.
    """
    
    # API Configuration
    API_TITLE: str = "AI Knowledge Continuity System API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "Production-grade RAG API with Tacit Knowledge, Decision Traceability, and Knowledge Gap Detection"
    
    # Server Configuration
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8000, description="API port")
    API_WORKERS: int = Field(default=1, description="Number of workers")
    API_RELOAD: bool = Field(default=False, description="Auto-reload for development")
    DEBUG: bool = Field(default=True, description="Debug mode")
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8501",
            "https://*.vercel.app",  # Allow all Vercel preview deployments
            "https://*.railway.app",  # Allow all Railway deployments
        ],
        description="Allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Requests per minute")
    
    # Admin API Key (placeholder auth)
    ADMIN_API_KEY: Optional[str] = Field(
        default="admin-secret-key-change-in-production",
        description="Admin API key for protected endpoints"
    )
    REQUIRE_ADMIN_KEY: bool = Field(default=False, description="Require admin key for protected endpoints")
    
    # Timeouts (aliased for service compatibility)
    QUERY_TIMEOUT_SECONDS: int = Field(default=60, description="Query timeout")
    INGEST_TIMEOUT_SECONDS: int = Field(default=300, description="Ingestion timeout")
    
    @property
    def QUERY_TIMEOUT(self) -> int:
        """Alias for QUERY_TIMEOUT_SECONDS."""
        return self.QUERY_TIMEOUT_SECONDS
    
    @property
    def INGEST_TIMEOUT(self) -> int:
        """Alias for INGEST_TIMEOUT_SECONDS."""
        return self.INGEST_TIMEOUT_SECONDS
    
    # Data directory
    DATA_DIR: str = Field(
        default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data"),
        description="Data directory path"
    )
    
    # Feature Flags
    ENABLE_KNOWLEDGE_FEATURES: bool = Field(
        default=True,
        description="Enable tacit knowledge, decision traceability, and gap detection"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_api_settings() -> APISettings:
    """
    Get cached API settings instance.
    
    Returns:
        APISettings: Singleton settings instance.
    """
    return APISettings()


# Global instance for convenience
api_settings = get_api_settings()
