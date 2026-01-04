"""
Prompt Templates Module for AI Knowledge Continuity System.

This module provides carefully crafted prompt templates for
various RAG operations with support for customization.
"""

from typing import Dict, List, Optional
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.prompts.chat import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from core.logger import get_logger

logger = get_logger(__name__)


class PromptManager:
    """
    Manages prompt templates for the RAG system.
    
    Features:
    - Pre-defined templates for common use cases
    - Custom template support
    - Template validation
    - Variable injection
    
    Example:
        >>> manager = PromptManager()
        >>> prompt = manager.get_qa_prompt()
    """
    
    # System message for the AI assistant
    SYSTEM_MESSAGE = """You are an expert organizational knowledge assistant for the AI Knowledge Continuity System.

Your role is to help preserve and transfer organizational knowledge by providing accurate, 
well-sourced answers based on the company's internal documentation.

Guidelines:
1. Answer questions using ONLY the provided context from organizational documents
2. If the answer is not found in the context, clearly state: "I don't have sufficient information in the knowledge base to answer this question."
3. Always cite your sources by referencing document names or sections when possible
4. Provide clear, structured responses with reasoning when appropriate
5. If the context contains conflicting information, acknowledge it and present all perspectives
6. Preserve technical accuracy and domain-specific terminology
7. When explaining processes or decisions, include the "why" behind them when available"""

    # Main QA prompt template
    QA_TEMPLATE = """You are an expert organizational knowledge assistant.

Answer the question using ONLY the provided context from organizational documents.
If the answer is not found in the context, say: "I don't have sufficient information in the knowledge base to answer this question."

When answering:
- Be accurate and cite sources when possible
- Provide clear reasoning and explanations
- Include the "why" behind decisions when available
- Preserve technical terminology

Context from organizational knowledge base:
{context}

Question: {question}

Answer:"""

    # Condensed question template for conversation history
    CONDENSE_QUESTION_TEMPLATE = """Given the following conversation history and a follow-up question, 
rephrase the follow-up question to be a standalone question that captures all relevant context.

Chat History:
{chat_history}

Follow-up Question: {question}

Standalone Question:"""

    # Template for summarizing documents
    SUMMARIZE_TEMPLATE = """Summarize the following organizational document while preserving key information, 
decisions, and rationale. Focus on actionable knowledge and important context.

Document:
{document}

Summary:"""

    # Template for extracting key information
    EXTRACTION_TEMPLATE = """Extract the following information from the provided text:
- Key decisions made
- Reasons/rationale for decisions
- Action items or next steps
- Important dates or deadlines
- Stakeholders involved

Text:
{text}

Extracted Information:"""

    def __init__(self):
        """Initialize the prompt manager with default templates."""
        self._templates: Dict[str, PromptTemplate] = {}
        self._register_default_templates()
        
        logger.info("PromptManager initialized with default templates")
    
    def _register_default_templates(self) -> None:
        """Register all default prompt templates."""
        self._templates = {
            "qa": PromptTemplate(
                input_variables=["context", "question"],
                template=self.QA_TEMPLATE,
            ),
            "condense": PromptTemplate(
                input_variables=["chat_history", "question"],
                template=self.CONDENSE_QUESTION_TEMPLATE,
            ),
            "summarize": PromptTemplate(
                input_variables=["document"],
                template=self.SUMMARIZE_TEMPLATE,
            ),
            "extract": PromptTemplate(
                input_variables=["text"],
                template=self.EXTRACTION_TEMPLATE,
            ),
        }
    
    def get_qa_prompt(self) -> PromptTemplate:
        """Get the main QA prompt template."""
        return self._templates["qa"]
    
    def get_condense_prompt(self) -> PromptTemplate:
        """Get the conversation condensing prompt template."""
        return self._templates["condense"]
    
    def get_summarize_prompt(self) -> PromptTemplate:
        """Get the document summarization prompt template."""
        return self._templates["summarize"]
    
    def get_extraction_prompt(self) -> PromptTemplate:
        """Get the information extraction prompt template."""
        return self._templates["extract"]
    
    def get_chat_prompt(self) -> ChatPromptTemplate:
        """
        Get a chat-style prompt template for conversational LLMs.
        
        Returns:
            ChatPromptTemplate suitable for chat models.
        """
        return ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(self.SYSTEM_MESSAGE),
            HumanMessagePromptTemplate.from_template(
                "Context:\n{context}\n\nQuestion: {question}"
            ),
        ])
    
    def register_template(
        self,
        name: str,
        template: str,
        input_variables: List[str],
    ) -> None:
        """
        Register a custom prompt template.
        
        Args:
            name: Unique name for the template.
            template: Template string with placeholders.
            input_variables: List of variable names in the template.
        """
        self._templates[name] = PromptTemplate(
            input_variables=input_variables,
            template=template,
        )
        logger.info(f"Registered custom template: {name}")
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """
        Get a template by name.
        
        Args:
            name: Name of the template.
            
        Returns:
            PromptTemplate if found, None otherwise.
        """
        return self._templates.get(name)
    
    def list_templates(self) -> List[str]:
        """List all registered template names."""
        return list(self._templates.keys())
    
    def format_prompt(
        self,
        template_name: str,
        **kwargs,
    ) -> str:
        """
        Format a template with provided variables.
        
        Args:
            template_name: Name of the template to use.
            **kwargs: Variables to inject into the template.
            
        Returns:
            Formatted prompt string.
        """
        template = self._templates.get(template_name)
        if template is None:
            raise ValueError(f"Template not found: {template_name}")
        
        return template.format(**kwargs)


# Default RAG prompt for backward compatibility
RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=PromptManager.QA_TEMPLATE,
)


# Create global prompt manager instance
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
