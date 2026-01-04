#!/usr/bin/env python3
"""
AI Knowledge Continuity System - Main Entry Point

A production-grade RAG system for preserving organizational knowledge
using LangChain and Large Language Models.

Usage:
    python main.py --ingest       # Ingest documents and create vector store
    python main.py --query "..."  # Query the knowledge base
    python main.py --ui           # Launch the Streamlit UI
    python main.py --status       # Check system status
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings, Settings
from core.logger import setup_logger, get_logger
from core.exceptions import KnowledgeSystemError


def setup_environment() -> Settings:
    """Initialize the application environment."""
    settings = get_settings()
    setup_logger(level=settings.LOG_LEVEL)
    return settings


def run_ingestion(settings: Settings) -> bool:
    """
    Run the document ingestion pipeline.
    
    Steps:
    1. Load documents from data directory
    2. Chunk documents into semantic units
    3. Create embeddings and store in vector database
    
    Returns:
        True if ingestion was successful, False otherwise.
    """
    logger = get_logger(__name__)
    logger.info("=" * 60)
    logger.info("Starting Document Ingestion Pipeline")
    logger.info("=" * 60)
    
    try:
        # Step 1: Load documents
        logger.info("Step 1/3: Loading documents...")
        from ingestion.load_documents import DocumentLoader
        
        loader = DocumentLoader(data_dir=settings.DATA_DIR)
        documents = loader.load()
        logger.info(f"✓ Loaded {len(documents)} documents")
        
        # Step 2: Chunk documents
        logger.info("Step 2/3: Chunking documents...")
        from ingestion.chunk_documents import DocumentChunker
        
        chunker = DocumentChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )
        chunks = chunker.chunk(documents)
        logger.info(f"✓ Created {len(chunks)} chunks")
        
        # Step 3: Create vector store
        logger.info("Step 3/3: Creating vector store...")
        from vector_store.create_store import VectorStoreManager
        
        manager = VectorStoreManager()
        manager.create(chunks)
        logger.info(f"✓ Vector store created at: {settings.VECTOR_STORE_PATH}")
        
        logger.info("=" * 60)
        logger.info("✅ Knowledge ingestion completed successfully!")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        return False


def run_query(query: str, settings: Settings) -> Optional[str]:
    """
    Run a single query against the knowledge base.
    
    Args:
        query: The question to ask.
        settings: Application settings.
        
    Returns:
        The answer string, or None if query failed.
    """
    logger = get_logger(__name__)
    logger.info(f"Query: {query}")
    
    try:
        from rag.qa_chain import RAGChain
        
        chain = RAGChain()
        response = chain.query(
            question=query,
            session_id="cli",
            use_memory=False,
        )
        
        print("\n" + "=" * 60)
        print("📝 ANSWER:")
        print("=" * 60)
        print(response.answer)
        
        if response.source_documents:
            print("\n" + "-" * 60)
            print(f"📚 SOURCES ({len(response.source_documents)}):")
            print("-" * 60)
            for i, doc in enumerate(response.source_documents[:3], 1):
                source = doc.metadata.get("source", "Unknown")
                print(f"{i}. {source}")
        
        print("\n" + "=" * 60)
        print(f"⏱️ Processed in {response.processing_time:.2f}s")
        
        return response.answer
        
    except Exception as e:
        logger.error(f"❌ Query failed: {e}")
        print(f"\n❌ Error: {e}")
        return None


def run_ui(settings: Settings):
    """Launch the Streamlit UI."""
    logger = get_logger(__name__)
    logger.info("Launching Streamlit UI...")
    
    import subprocess
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(PROJECT_ROOT / "ui" / "app.py"),
        "--server.headless", "true",
    ])


def check_status(settings: Settings):
    """Check and display system status."""
    logger = get_logger(__name__)
    
    print("\n" + "=" * 60)
    print("🧠 AI Knowledge Continuity System - Status")
    print("=" * 60)
    
    # Check configuration
    print("\n📋 Configuration:")
    print(f"  • Data Directory: {settings.DATA_DIR}")
    print(f"  • Vector Store: {settings.VECTOR_STORE_PATH}")
    print(f"  • LLM Provider: {settings.LLM_PROVIDER}")
    print(f"  • Embedding Model: {settings.EMBEDDING_MODEL}")
    
    # Check data directory
    print("\n📁 Data Directory:")
    data_path = Path(settings.DATA_DIR)
    if data_path.exists():
        file_count = sum(1 for _ in data_path.rglob("*") if _.is_file())
        print(f"  ✓ Exists ({file_count} files)")
    else:
        print("  ✗ Not found")
    
    # Check vector store
    print("\n🗄️ Vector Store:")
    store_path = Path(settings.VECTOR_STORE_PATH)
    if (store_path / "index.faiss").exists():
        print(f"  ✓ Exists at {store_path}")
        
        try:
            from vector_store.create_store import VectorStoreManager
            manager = VectorStoreManager()
            stats = manager.get_stats()
            print(f"  • Documents indexed: {stats.get('num_documents', 'Unknown')}")
        except Exception as e:
            print(f"  • Could not load stats: {e}")
    else:
        print("  ✗ Not created (run --ingest first)")
    
    # Check LLM availability
    print("\n🤖 LLM Provider:")
    if settings.LLM_PROVIDER == "gemini":
        if settings.GEMINI_API_KEY:
            print("  ✓ Gemini API key configured")
        else:
            print("  ✗ Gemini API key not set")
    elif settings.LLM_PROVIDER == "local":
        print("  • Local LLM selected (requires adequate hardware)")
    
    print("\n" + "=" * 60)


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="AI Knowledge Continuity System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --ingest              # Ingest documents
  python main.py --query "How to deploy?"  # Ask a question
  python main.py --ui                  # Launch web interface
  python main.py --status              # Check system status
        """
    )
    
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Ingest documents and create vector store"
    )
    
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Query the knowledge base"
    )
    
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Launch the Streamlit web interface"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check system status"
    )
    
    args = parser.parse_args()
    
    # Setup environment
    settings = setup_environment()
    logger = get_logger(__name__)
    
    # Handle commands
    if args.ingest:
        success = run_ingestion(settings)
        sys.exit(0 if success else 1)
    
    elif args.query:
        result = run_query(args.query, settings)
        sys.exit(0 if result else 1)
    
    elif args.ui:
        run_ui(settings)
    
    elif args.status:
        check_status(settings)
    
    else:
        # Default: show help
        parser.print_help()
        print("\n" + "-" * 40)
        print("Quick Start:")
        print("1. Add documents to the 'data/' directory")
        print("2. Run: python main.py --ingest")
        print("3. Run: python main.py --ui")


if __name__ == "__main__":
    main()
