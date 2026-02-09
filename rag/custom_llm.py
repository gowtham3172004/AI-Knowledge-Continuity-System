"""
Custom LLM Provider for OpenAI-Compatible API.

This module provides support for local LLM servers that expose
an OpenAI-compatible API endpoint (like vLLM, LocalAI, Ollama, etc.).
"""

from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.language_models.base import BaseLanguageModel

from config.settings import get_settings
from core.logger import get_logger
from core.exceptions import LLMError, ConfigurationError

logger = get_logger(__name__)


class CustomLLMProvider:
    """
    Custom LLM Provider for OpenAI-compatible API endpoints.
    
    This provider works with any LLM server that implements the OpenAI API format,
    including:
    - vLLM
    - LocalAI
    - Ollama (with OpenAI compatibility)
    - LM Studio
    - Text Generation WebUI (with OpenAI extension)
    
    Example:
        >>> provider = CustomLLMProvider(
        ...     base_url="http://192.168.1.2:10898/v1/",
        ...     model_name="llama3_8B"
        ... )
        >>> llm = provider.get_llm()
        >>> response = llm.invoke("Hello!")
    """
    
    def __init__(
        self,
        base_url: str = "http://192.168.1.2:10898/v1/",
        model_name: str = "llama3_8B",
        api_key: str = "not-needed",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ):
        """
        Initialize the Custom LLM Provider.
        
        Args:
            base_url: The base URL of the OpenAI-compatible API endpoint.
            model_name: The model name to use.
            api_key: API key (set to "not-needed" for local servers without auth).
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens to generate.
            **kwargs: Additional parameters to pass to ChatOpenAI.
        """
        self.base_url = base_url
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs
        self._llm: Optional[BaseLanguageModel] = None
        
        logger.info(f"CustomLLMProvider initialized with base_url: {base_url}, model: {model_name}")
    
    def get_llm(self) -> BaseLanguageModel:
        """
        Get the LLM instance.
        
        Returns:
            Configured ChatOpenAI instance.
            
        Raises:
            LLMError: If initialization fails.
        """
        if self._llm is not None:
            return self._llm
        
        try:
            logger.info(f"Initializing custom LLM: {self.model_name} at {self.base_url}")
            
            self._llm = ChatOpenAI(
                base_url=self.base_url,
                model=self.model_name,
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **self.kwargs
            )
            
            logger.info("Custom LLM initialized successfully")
            return self._llm
            
        except ImportError:
            raise LLMError(
                "langchain-openai package not installed",
                details={"install": "pip install langchain-openai"}
            )
        except Exception as e:
            raise LLMError(
                f"Failed to initialize custom LLM: {e}",
                details={
                    "base_url": self.base_url,
                    "model": self.model_name
                }
            )
    
    def test_connection(self) -> bool:
        """
        Test the connection to the LLM server.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            llm = self.get_llm()
            response = llm.invoke("Hello")
            logger.info("Connection test successful")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


def get_custom_llm(
    base_url: str = "http://192.168.1.2:10898/v1/",
    model_name: str = "llama3_8B",
    **kwargs
) -> BaseLanguageModel:
    """
    Convenience function to get a custom LLM instance.
    
    Args:
        base_url: The base URL of the OpenAI-compatible API endpoint.
        model_name: The model name to use.
        **kwargs: Additional parameters to pass to the provider.
    
    Returns:
        Configured LLM instance.
    
    Example:
        >>> llm = get_custom_llm(
        ...     base_url="http://192.168.1.2:10898/v1/",
        ...     model_name="llama3_8B",
        ...     temperature=0.5
        ... )
        >>> response = llm.invoke("What is AI?")
    """
    provider = CustomLLMProvider(
        base_url=base_url,
        model_name=model_name,
        **kwargs
    )
    return provider.get_llm()


# Example usage configurations
EXAMPLE_CONFIGS = {
    "llama3_local": {
        "base_url": "http://192.168.1.2:10898/v1/",
        "model_name": "llama3_8B",
        "temperature": 0.7,
        "max_tokens": 2048,
    },
    "vllm_server": {
        "base_url": "http://localhost:8000/v1/",
        "model_name": "meta-llama/Meta-Llama-3-8B-Instruct",
        "temperature": 0.7,
        "max_tokens": 2048,
    },
    "ollama_openai": {
        "base_url": "http://localhost:11434/v1/",
        "model_name": "llama3",
        "temperature": 0.7,
        "max_tokens": 2048,
    },
}


if __name__ == "__main__":
    """
    Test script to verify the custom LLM provider.
    
    Usage:
        python -m rag.custom_llm
    """
    print("Testing Custom LLM Provider...")
    print(f"Base URL: http://192.168.1.2:10898/v1/")
    print(f"Model: llama3_8B")
    print("-" * 50)
    
    try:
        # Initialize provider
        provider = CustomLLMProvider(
            base_url="http://192.168.1.2:10898/v1/",
            model_name="llama3_8B"
        )
        
        # Test connection
        print("\n1. Testing connection...")
        if provider.test_connection():
            print("✓ Connection successful!")
        else:
            print("✗ Connection failed!")
            exit(1)
        
        # Get LLM and test query
        print("\n2. Testing query...")
        llm = provider.get_llm()
        response = llm.invoke("Generate 1000 words about Virat kohli")
        print(f"Response: {response.content}")
        
        print("\n✓ All tests passed!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        exit(1)
