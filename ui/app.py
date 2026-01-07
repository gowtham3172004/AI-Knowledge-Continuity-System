"""
Streamlit UI for AI Knowledge Continuity System.

This module provides a production-grade web interface for the
knowledge continuity system with chat functionality.

Extended to display:
- Feature 1: Tacit knowledge indicators
- Feature 2: Decision traceability metadata
- Feature 3: Knowledge gap warnings and confidence scores
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


def render_chat_message(role: str, content: str, sources: List[Dict] = None, response_metadata: Dict = None):
    """
    Render a single chat message with knowledge-aware indicators.
    
    Args:
        role: Message role ('user' or 'assistant').
        content: Message content.
        sources: Source documents list.
        response_metadata: Knowledge metadata (query_type, confidence, warnings).
    """
    with st.chat_message(role):
        st.markdown(content)
        
        # === KNOWLEDGE-AWARE INDICATORS (Features 1, 2, 3) ===
        if response_metadata and role == "assistant":
            _render_knowledge_indicators(response_metadata)
        
        # Show sources if available and enabled
        if sources and st.session_state.show_sources:
            _render_sources(sources)


def _render_knowledge_indicators(metadata: Dict):
    """Render knowledge type indicators and warnings."""
    # Query type indicator (Features 1 & 2)
    query_type = metadata.get("query_type", "general")
    confidence = metadata.get("confidence")
    gap_detected = metadata.get("knowledge_gap_detected", False)
    gap_severity = metadata.get("gap_severity")
    warnings = metadata.get("validation_warnings", [])
    knowledge_types = metadata.get("knowledge_types_used", [])
    
    # Knowledge type badge
    type_badges = {
        "tacit": ("📚 Tacit Knowledge", "Insights from lessons learned and experience"),
        "decision": ("📋 Decision Record", "Based on documented decisions and rationale"),
        "general": ("📄 Documentation", "Based on standard documentation"),
    }
    
    badge_text, badge_tooltip = type_badges.get(query_type, type_badges["general"])
    
    # Create columns for indicators
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        st.caption(f"🏷️ **{badge_text}**")
    
    with col2:
        if confidence is not None:
            confidence_pct = int(confidence * 100)
            if confidence_pct >= 70:
                st.caption(f"✅ Confidence: {confidence_pct}%")
            elif confidence_pct >= 50:
                st.caption(f"⚠️ Confidence: {confidence_pct}%")
            else:
                st.caption(f"🔴 Confidence: {confidence_pct}%")
    
    with col3:
        if knowledge_types:
            types_str = ", ".join(knowledge_types)
            st.caption(f"📁 Sources: {types_str}")
    
    # Knowledge gap warning (Feature 3)
    if gap_detected:
        severity_colors = {
            "low": "warning",
            "medium": "warning", 
            "high": "error",
            "critical": "error",
        }
        severity_icons = {
            "low": "⚠️",
            "medium": "⚠️",
            "high": "🚨",
            "critical": "🚨",
        }
        
        color = severity_colors.get(gap_severity, "warning")
        icon = severity_icons.get(gap_severity, "⚠️")
        
        if color == "error":
            st.error(f"{icon} **Knowledge Gap Detected** ({gap_severity})")
        else:
            st.warning(f"{icon} **Partial Knowledge Coverage** ({gap_severity})")
    
    # Validation warnings
    if warnings and not gap_detected:
        with st.expander("ℹ️ Notes"):
            for warning in warnings:
                st.caption(f"• {warning}")


def _render_sources(sources: List[Dict]):
    """Render source documents with knowledge type indicators."""
    with st.expander(f"📚 Sources ({len(sources)})"):
        for i, source in enumerate(sources, 1):
            # Knowledge type indicator
            kt = source.get("knowledge_type", "explicit")
            kt_icon = {
                "tacit": "📚",
                "decision": "📋",
                "explicit": "📄",
            }.get(kt, "📄")
            
            st.markdown(f"**{kt_icon} Source {i}:** {source.get('source', 'Unknown')}")
            
            # Decision metadata (Feature 2)
            if kt == "decision":
                decision_info = []
                if source.get("decision_author"):
                    decision_info.append(f"Author: {source['decision_author']}")
                if source.get("decision_date"):
                    decision_info.append(f"Date: {source['decision_date']}")
                if decision_info:
                    st.caption(" | ".join(decision_info))
            
            st.text(source.get('content_preview', '')[:300] + "...")
            st.divider()


def render_chat_history():
    """Render the chat history with knowledge indicators."""
    for message in st.session_state.chat_history:
        render_chat_message(
            role=message["role"],
            content=message["content"],
            sources=message.get("sources"),
            response_metadata=message.get("response_metadata"),
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
    """Render the chat input and handle submissions with knowledge features."""
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
            
            # === PREPARE KNOWLEDGE METADATA (Features 1, 2, 3) ===
            response_metadata = {
                "query_type": getattr(response, 'query_type', 'general'),
                "confidence": response.confidence,
                "knowledge_gap_detected": getattr(response, 'knowledge_gap_detected', False),
                "gap_severity": getattr(response, 'gap_severity', None),
                "validation_warnings": getattr(response, 'validation_warnings', []),
                "knowledge_types_used": getattr(response, 'knowledge_types_used', []),
            }
            
            # Add assistant message to history
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response.answer,
                "sources": sources,
                "response_metadata": response_metadata,
            })
            
            # Display response
            st.markdown(response.answer)
            
            # === DISPLAY KNOWLEDGE INDICATORS ===
            _render_knowledge_indicators(response_metadata)
            
            # Show sources if enabled
            if sources and st.session_state.show_sources:
                _render_sources(sources)
            
            # Show processing time and additional metadata
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"⏱️ Processed in {response.processing_time:.2f}s")
            with col2:
                if response.metadata.get("knowledge_features_used"):
                    tacit = response.metadata.get("tacit_docs", 0)
                    decision = response.metadata.get("decision_docs", 0)
                    explicit = response.metadata.get("explicit_docs", 0)
                    st.caption(f"📊 Tacit: {tacit} | Decision: {decision} | Explicit: {explicit}")


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
    """Render welcome message for new sessions with knowledge feature highlights."""
    if not st.session_state.chat_history:
        st.markdown("""
        ### 👋 Welcome to the AI Knowledge Continuity System!
        
        I'm here to help you access and understand your organization's collective knowledge.
        
        **🧠 Intelligent Features:**
        - **📚 Tacit Knowledge**: I prioritize lessons learned and best practices for experience-based questions
        - **📋 Decision Tracing**: I explain the rationale, alternatives, and trade-offs behind decisions
        - **🛡️ Gap Detection**: I'll tell you honestly when information isn't available, rather than guessing
        
        **Try asking me:**
        - 💡 "What mistakes should I avoid when using Redis?"
        - 📋 "Why did we choose Redis instead of RabbitMQ?"
        - 📚 "What are the best practices for caching?"
        - ❓ "What decisions were made about the architecture?"
        
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
            
            # === KNOWLEDGE FEATURES STATUS ===
            st.markdown("### 🧠 Knowledge Features")
            st.success("✅ Tacit Knowledge")
            st.success("✅ Decision Tracing")  
            st.success("✅ Gap Detection")
            
            # Quick actions
            st.markdown("### 🚀 Quick Actions")
            
            example_questions = [
                ("📚 Lessons", "What lessons were learned from the backend team?"),
                ("📋 Decision", "Why was Redis chosen over RabbitMQ?"),
                ("⚠️ Pitfalls", "What common mistakes should I avoid?"),
            ]
            
            for label, question in example_questions:
                if st.button(f"{label}", key=f"example_{hash(question)}", use_container_width=True):
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
