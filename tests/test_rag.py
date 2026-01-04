"""
Tests for the RAG chain module.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

from rag.qa_chain import RAGChain, RAGResponse
from rag.prompt import PromptManager
from core.exceptions import LLMError


class TestRAGResponse:
    """Tests for RAGResponse dataclass."""
    
    def test_creation(self):
        """Test RAGResponse creation."""
        response = RAGResponse(
            answer="Test answer",
            source_documents=[],
            query="Test query",
        )
        
        assert response.answer == "Test answer"
        assert response.query == "Test query"
        assert response.source_documents == []
    
    def test_get_sources_summary(self):
        """Test source summary generation."""
        mock_doc = MagicMock()
        mock_doc.metadata = {"source": "test.txt"}
        mock_doc.page_content = "This is test content for the summary."
        
        response = RAGResponse(
            answer="Answer",
            source_documents=[mock_doc],
            query="Query",
        )
        
        summary = response.get_sources_summary()
        
        assert len(summary) == 1
        assert summary[0]["source"] == "test.txt"
        assert "content_preview" in summary[0]
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        response = RAGResponse(
            answer="Answer",
            source_documents=[],
            query="Query",
            processing_time=1.5,
        )
        
        result = response.to_dict()
        
        assert result["answer"] == "Answer"
        assert result["query"] == "Query"
        assert result["processing_time"] == 1.5
        assert "sources" in result


class TestPromptManager:
    """Tests for PromptManager class."""
    
    def test_init(self):
        """Test initialization."""
        manager = PromptManager()
        
        assert "qa" in manager._templates
        assert "condense" in manager._templates
    
    def test_get_qa_prompt(self):
        """Test getting QA prompt."""
        manager = PromptManager()
        prompt = manager.get_qa_prompt()
        
        assert "context" in prompt.input_variables
        assert "question" in prompt.input_variables
    
    def test_register_custom_template(self):
        """Test registering custom template."""
        manager = PromptManager()
        
        manager.register_template(
            name="custom",
            template="Hello {name}!",
            input_variables=["name"],
        )
        
        assert "custom" in manager.list_templates()
        assert manager.get_template("custom") is not None
    
    def test_format_prompt(self):
        """Test formatting a prompt."""
        manager = PromptManager()
        
        manager.register_template(
            name="test",
            template="Hello {name}, you asked: {question}",
            input_variables=["name", "question"],
        )
        
        result = manager.format_prompt(
            "test",
            name="Alice",
            question="What is AI?",
        )
        
        assert "Alice" in result
        assert "What is AI?" in result


class TestRAGChain:
    """Tests for RAGChain class."""
    
    @patch('rag.qa_chain.get_llm_manager')
    @patch('rag.qa_chain.VectorStoreManager')
    @patch('rag.qa_chain.get_memory_manager')
    def test_init(self, mock_memory, mock_vector, mock_llm):
        """Test RAGChain initialization."""
        mock_llm.return_value.get_llm.return_value = MagicMock()
        
        chain = RAGChain()
        
        assert chain.llm_manager is not None
        assert chain.prompt_manager is not None
    
    @patch('rag.qa_chain.get_llm_manager')
    @patch('rag.qa_chain.VectorStoreManager')
    @patch('rag.qa_chain.RetrieverManager')
    @patch('rag.qa_chain.get_memory_manager')
    def test_query_returns_response(
        self, mock_memory, mock_retriever, mock_vector, mock_llm
    ):
        """Test that query returns a RAGResponse."""
        # Setup mocks
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = MagicMock(content="Test answer")
        mock_llm.return_value.get_llm.return_value = mock_llm_instance
        mock_llm.return_value.provider_name = "gemini"
        
        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve.return_value = MagicMock(
            documents=[],
            num_results=0,
        )
        mock_retriever_instance.format_context.return_value = "No context"
        mock_retriever.return_value = mock_retriever_instance
        
        mock_memory.return_value.get_history.return_value = []
        
        chain = RAGChain()
        response = chain.query("Test question")
        
        assert isinstance(response, RAGResponse)
        assert response.query == "Test question"
    
    def test_format_chat_history(self):
        """Test chat history formatting."""
        with patch('rag.qa_chain.get_llm_manager'):
            with patch('rag.qa_chain.VectorStoreManager'):
                with patch('rag.qa_chain.get_memory_manager'):
                    chain = RAGChain()
                    
                    history = [
                        {"human": "Hello", "ai": "Hi there!"},
                        {"human": "How are you?", "ai": "I'm doing well!"},
                    ]
                    
                    formatted = chain._format_chat_history(history)
                    
                    assert "Human: Hello" in formatted
                    assert "Assistant: Hi there!" in formatted
