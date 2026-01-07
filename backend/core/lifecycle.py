"""
Application lifecycle management.

Handles startup and shutdown events for resource management.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from backend.core.logging import get_logger, setup_logging
from backend.core.config import get_api_settings

logger = get_logger(__name__)


class ApplicationState:
    """
    Application state container.
    
    Holds references to initialized services and resources
    that need to be shared across requests.
    """
    
    def __init__(self):
        self.rag_chain = None
        self.vector_store_manager = None
        self.rag_service = None
        self.ingest_service = None
        self.is_ready = False
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize application resources."""
        async with self._lock:
            if self.is_ready:
                return
            
            logger.info("Initializing application state...")
            
            try:
                # Import here to avoid circular imports
                from rag.qa_chain import RAGChain
                from vector_store.create_store import VectorStoreManager
                from backend.services.rag_service import RAGService
                from backend.services.ingest_service import IngestService
                
                # Initialize RAG chain (this may take a few seconds)
                logger.info("Initializing RAG chain...")
                self.rag_chain = RAGChain()
                
                # Initialize vector store manager
                logger.info("Initializing vector store manager...")
                self.vector_store_manager = VectorStoreManager()
                
                # Initialize service adapters
                logger.info("Initializing service adapters...")
                self.rag_service = RAGService(self.rag_chain)
                self.ingest_service = IngestService(self.vector_store_manager)
                
                self.is_ready = True
                logger.info("Application state initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize application state: {e}")
                raise
    
    async def shutdown(self) -> None:
        """Cleanup application resources."""
        logger.info("Shutting down application state...")
        
        # Shutdown services
        if self.rag_service:
            self.rag_service.shutdown()
        if self.ingest_service:
            self.ingest_service.shutdown()
        
        # Clear references
        self.rag_chain = None
        self.vector_store_manager = None
        self.rag_service = None
        self.ingest_service = None
        self.is_ready = False
        
        logger.info("Application state shutdown complete")


# Global application state (initialized in lifespan)
app_state = ApplicationState()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    
    Args:
        app: FastAPI application instance
        
    Yields:
        None during application lifetime
    """
    # Startup
    settings = get_api_settings()
    setup_logging("INFO")
    
    logger.info("="*60)
    logger.info(f"Starting {settings.API_TITLE} v{settings.API_VERSION}")
    logger.info("="*60)
    
    try:
        # Initialize application state
        await app_state.initialize()
        
        # Attach to app.state for dependency injection
        app.state.app_state = app_state
        
        logger.info(f"API ready at http://{settings.API_HOST}:{settings.API_PORT}")
        logger.info("Knowledge features enabled: " + str(settings.ENABLE_KNOWLEDGE_FEATURES))
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("="*60)
    logger.info("Shutting down API...")
    logger.info("="*60)
    
    await app_state.shutdown()
    
    logger.info("Shutdown complete")


def get_app_state() -> ApplicationState:
    """
    Get current application state.
    
    Returns:
        ApplicationState: Current application state
    """
    return app_state
