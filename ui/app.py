"""
Streamlit UI for AI Knowledge Continuity System.

This module provides a production-grade web interface for the
knowledge continuity system with chat functionality.
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from pathlib import Path

# Import system components
from config.settings import get_settings
from core.logger import get_logger
from core.exceptions import KnowledgeSystemError
from rag.qa_chain import RAGChain, get_rag_chain, RAGResponse
from evaluation.metrics import RAGEvaluator

logger = get_logger(__name__)


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "rag_chain" not in st.session_state:
        st.session_state.rag_chain = None
    
    if "is_initialized" not in st.session_state:
        st.session_state.is_initialized = False
    
    if "error_message" not in st.session_state:
        st.session_state.error_message = None
    
    if "show_sources" not in st.session_state:
        st.session_state.show_sources = True


def load_rag_chain() -> Optional[RAGChain]:
    """Load and cache the RAG chain."""
    try:
        if st.session_state.rag_chain is None:
            with st.spinner("🔄 Loading AI Knowledge System..."):
                st.session_state.rag_chain = get_rag_chain()
                st.session_state.is_initialized = True
                logger.info("RAG chain loaded successfully")
        return st.session_state.rag_chain
    except Exception as e:
        st.session_state.error_message = str(e)
        logger.error(f"Failed to load RAG chain: {e}")
        return None


def render_header():
    """Render the application header."""
    # Get logo path
    logo_path = Path(__file__).parent / "assets" / "logo.png"
    
    # Set page config with logo
    st.set_page_config(
        page_title="AI Knowledge Continuity System",
        page_icon=str(logo_path) if logo_path.exists() else "🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Display logo and title in header
    col1, col2 = st.columns([1, 5])
    
    with col1:
        if logo_path.exists():
            st.image(str(logo_path), width=100)
        else:
            st.markdown("## 🧠")
    
    with col2:
        st.title("AI Knowledge Continuity System")
        st.markdown(
            "*Preserving organizational knowledge through intelligent retrieval*"
        )
    
    st.divider()


def render_sidebar():
    """Render the sidebar with settings and info."""
    settings = get_settings()
    logo_path = Path(__file__).parent / "assets" / "logo.png"
    
    with st.sidebar:
        # Display logo at top of sidebar
        if logo_path.exists():
            st.image(str(logo_path), width=150)
        else:
            st.markdown("# 🧠")
        
        st.markdown("---")
        
        st.header("⚙️ Settings")
        
        # Session info
        st.subheader("Session Info")
        st.text(f"Session ID: {st.session_state.session_id}")
        st.text(f"Messages: {len(st.session_state.chat_history)}")
        
        st.divider()
        
        # Display options
        st.subheader("Display Options")
        st.session_state.show_sources = st.checkbox(
            "Show source documents",
            value=st.session_state.show_sources,
        )
        
        # Retrieval settings
        st.subheader("Retrieval Settings")
        retrieval_k = st.slider(
            "Number of documents to retrieve",
            min_value=1,
            max_value=10,
            value=settings.RETRIEVER_K,
            key="retrieval_k",
        )
        
        retrieval_strategy = st.selectbox(
            "Retrieval strategy",
            options=["similarity", "mmr"],
            index=0,
            key="retrieval_strategy",
        )
        
        st.divider()
        
        # Actions
        st.subheader("Actions")
        
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.chat_history = []
            if st.session_state.rag_chain:
                st.session_state.rag_chain.clear_session_memory(
                    st.session_state.session_id
                )
            st.rerun()
        
        if st.button("🔄 New Session", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())[:8]
            st.session_state.chat_history = []
            st.rerun()
        
        st.divider()
        
        # System info
        st.subheader("System Info")
        st.text(f"LLM Provider: {settings.LLM_PROVIDER}")
        st.text(f"Embedding Model: {settings.EMBEDDING_MODEL.split('/')[-1]}")
        
        # Status indicator
        if st.session_state.is_initialized:
            st.success("✅ System Ready")
        else:
            st.warning("⏳ System Loading...")


def render_chat_message(role: str, content: str, sources: List[Dict] = None):
    """Render a single chat message."""
    with st.chat_message(role):
        st.markdown(content)
        
        # Show sources if available and enabled
        if sources and st.session_state.show_sources:
            with st.expander(f"📚 Sources ({len(sources)})"):
                for i, source in enumerate(sources, 1):
                    st.markdown(f"**Source {i}:** {source.get('source', 'Unknown')}")
                    st.text(source.get('content_preview', '')[:300] + "...")
                    st.divider()


def render_chat_history():
    """Render the chat history."""
    for message in st.session_state.chat_history:
        render_chat_message(
            role=message["role"],
            content=message["content"],
            sources=message.get("sources"),
        )


def process_query(query: str, rag_chain: RAGChain) -> Optional[RAGResponse]:
    """Process a user query through the RAG pipeline."""
    try:
        # Get settings from sidebar
        retrieval_k = st.session_state.get("retrieval_k", 5)
        retrieval_strategy = st.session_state.get("retrieval_strategy", "similarity")
        
        response = rag_chain.query(
            question=query,
            session_id=st.session_state.session_id,
            retrieval_strategy=retrieval_strategy,
            k=retrieval_k,
            include_sources=True,
            use_memory=True,
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        st.error(f"❌ Error processing query: {str(e)}")
        return None


def render_chat_input(rag_chain: RAGChain):
    """Render the chat input and handle submissions."""
    if prompt := st.chat_input("Ask a question about your organizational knowledge..."):
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": prompt,
        })
        
        # Display user message
        render_chat_message("user", prompt)
        
        # Process query
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                response = process_query(prompt, rag_chain)
        
        if response:
            # Prepare sources summary
            sources = response.get_sources_summary() if response.source_documents else []
            
            # Add assistant message to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response.answer,
                "sources": sources,
            })
            
            # Display response
            st.markdown(response.answer)
            
            # Show sources if enabled
            if sources and st.session_state.show_sources:
                with st.expander(f"📚 Sources ({len(sources)})"):
                    for i, source in enumerate(sources, 1):
                        st.markdown(f"**Source {i}:** {source.get('source', 'Unknown')}")
                        st.text(source.get('content_preview', '')[:300] + "...")
                        st.divider()
            
            # Show processing time
            st.caption(f"⏱️ Processed in {response.processing_time:.2f}s")


def render_error_state():
    """Render error state when system fails to initialize."""
    st.error("❌ Failed to initialize the AI Knowledge System")
    
    if st.session_state.error_message:
        with st.expander("Error Details"):
            st.code(st.session_state.error_message)
    
    st.markdown("""
    ### Troubleshooting Steps:
    
    1. **Check your `.env` file** - Ensure `GEMINI_API_KEY` is set correctly
    2. **Verify vector store exists** - Run the ingestion pipeline first
    3. **Check data directory** - Ensure documents are in the `data/` folder
    
    Run the ingestion script:
    ```bash
    python main.py --ingest
    ```
    """)
    
    if st.button("🔄 Retry"):
        st.session_state.rag_chain = None
        st.session_state.is_initialized = False
        st.session_state.error_message = None
        st.rerun()


def render_welcome_message():
    """Render welcome message for new sessions."""
    if not st.session_state.chat_history:
        st.markdown("""
        ### 👋 Welcome to the AI Knowledge Continuity System!
        
        I'm here to help you access and understand your organization's collective knowledge.
        
        **Try asking me:**
        - "What is our deployment process?"
        - "How do we handle customer escalations?"
        - "What decisions were made about the architecture?"
        - "Who should I contact about the billing system?"
        
        Just type your question below to get started!
        """)


def create_app():
    """Create and configure the Streamlit application."""
    # Initialize session state
    initialize_session_state()
    
    # Render UI components
    render_header()
    render_sidebar()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Load RAG chain
        rag_chain = load_rag_chain()
        
        if rag_chain is None:
            render_error_state()
        else:
            # Render welcome message for new sessions
            render_welcome_message()
            
            # Render chat history
            render_chat_history()
            
            # Render chat input
            render_chat_input(rag_chain)
    
    with col2:
        if st.session_state.is_initialized:
            # Quick stats
            st.markdown("### 📊 Quick Stats")
            st.metric("Questions Asked", len([m for m in st.session_state.chat_history if m["role"] == "user"]))
            
            # Quick actions
            st.markdown("### 🚀 Quick Actions")
            
            example_questions = [
                "What are the main project guidelines?",
                "How do I get started?",
                "What are the best practices?",
            ]
            
            for question in example_questions:
                if st.button(f"💡 {question[:30]}...", key=f"example_{hash(question)}"):
                    # This is a simplified version - in production, 
                    # you'd want to properly handle this
                    st.session_state.chat_history.append({
                        "role": "user",
                        "content": question,
                    })
                    st.rerun()


def run_app():
    """Run the Streamlit application."""
    create_app()


# Main entry point for Streamlit
if __name__ == "__main__":
    run_app()
