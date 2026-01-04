"""
LLM Management Module for AI Knowledge Continuity System.

This module provides a unified interface for multiple LLM providers:
- Google Gemini (primary, cloud-based)
- Local LLMs via HuggingFace (for future use with adequate hardware)
- HuggingFace API (alternative cloud option)
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Any, Dict

from langchain_core.messages import BaseMessage
from langchain_core.language_models.base import BaseLanguageModel

from config.settings import get_settings
from core.logger import get_logger
from core.exceptions import LLMError, ConfigurationError

logger = get_logger(__name__)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def get_llm(self) -> BaseLanguageModel:
        """Get the LLM instance."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
        pass


class GeminiProvider(BaseLLMProvider):
    """
    Google Gemini LLM provider.
    
    This is the primary LLM provider for the system,
    offering excellent performance via the Gemini API.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._llm = None
    
    def is_available(self) -> bool:
        """Check if Gemini API key is configured."""
        return bool(self.settings.GEMINI_API_KEY)
    
    def get_llm(self) -> BaseLanguageModel:
        """
        Get the Gemini LLM instance.
        
        Returns:
            Configured Gemini LLM.
            
        Raises:
            ConfigurationError: If API key is not set.
            LLMError: If initialization fails.
        """
        if self._llm is not None:
            return self._llm
        
        if not self.is_available():
            raise ConfigurationError(
                "Gemini API key not configured",
                details={"setting": "GEMINI_API_KEY"}
            )
        
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            logger.info(f"Initializing Gemini LLM: {self.settings.GEMINI_MODEL}")
            
            self._llm = ChatGoogleGenerativeAI(
                model=self.settings.GEMINI_MODEL,
                google_api_key=self.settings.GEMINI_API_KEY,
                temperature=self.settings.TEMPERATURE,
                max_output_tokens=self.settings.MAX_NEW_TOKENS,
                top_p=self.settings.TOP_P,
                convert_system_message_to_human=True,
            )
            
            logger.info("Gemini LLM initialized successfully")
            return self._llm
            
        except ImportError:
            raise LLMError(
                "langchain-google-genai package not installed",
                details={"install": "pip install langchain-google-genai"}
            )
        except Exception as e:
            raise LLMError(
                f"Failed to initialize Gemini LLM: {e}",
                details={"model": self.settings.GEMINI_MODEL}
            )


class LocalLLMProvider(BaseLLMProvider):
    """
    Local LLM provider using HuggingFace models.
    
    This provider runs models locally on your hardware.
    Requires adequate GPU/CPU resources.
    
    Note: Currently commented out in production due to hardware requirements.
    Uncomment when hardware is available.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._llm = None
    
    def is_available(self) -> bool:
        """
        Check if local LLM is available.
        Always returns False until hardware is available.
        """
        # TODO: Implement hardware check (GPU memory, etc.)
        # For now, return False as hardware is not available
        return False
    
    def get_llm(self) -> BaseLanguageModel:
        """
        Get the local LLM instance.
        
        Returns:
            Configured local LLM.
            
        Raises:
            LLMError: If initialization fails.
        """
        if self._llm is not None:
            return self._llm
        
        try:
            # ============================================================
            # LOCAL LLM IMPLEMENTATION
            # Uncomment this section when you have adequate hardware
            # ============================================================
            
            # from langchain_huggingface import HuggingFacePipeline
            # from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            # import torch
            #
            # logger.info(f"Loading local LLM: {self.settings.LOCAL_LLM_MODEL}")
            #
            # # Determine device
            # if torch.cuda.is_available():
            #     device = "cuda"
            #     torch_dtype = torch.float16
            # elif torch.backends.mps.is_available():
            #     device = "mps"
            #     torch_dtype = torch.float16
            # else:
            #     device = "cpu"
            #     torch_dtype = torch.float32
            #
            # logger.info(f"Using device: {device}")
            #
            # # Load tokenizer
            # tokenizer = AutoTokenizer.from_pretrained(
            #     self.settings.LOCAL_LLM_MODEL,
            #     trust_remote_code=True,
            # )
            #
            # # Load model
            # model = AutoModelForCausalLM.from_pretrained(
            #     self.settings.LOCAL_LLM_MODEL,
            #     torch_dtype=torch_dtype,
            #     device_map="auto",
            #     trust_remote_code=True,
            # )
            #
            # # Create pipeline
            # pipe = pipeline(
            #     "text-generation",
            #     model=model,
            #     tokenizer=tokenizer,
            #     max_new_tokens=self.settings.MAX_NEW_TOKENS,
            #     temperature=self.settings.TEMPERATURE,
            #     top_p=self.settings.TOP_P,
            #     do_sample=True,
            #     repetition_penalty=1.1,
            # )
            #
            # self._llm = HuggingFacePipeline(pipeline=pipe)
            #
            # logger.info("Local LLM initialized successfully")
            # return self._llm
            
            # ============================================================
            # END LOCAL LLM IMPLEMENTATION
            # ============================================================
            
            raise LLMError(
                "Local LLM is not enabled. Hardware requirements not met.",
                details={
                    "model": self.settings.LOCAL_LLM_MODEL,
                    "suggestion": "Use Gemini or HuggingFace API instead"
                }
            )
            
        except Exception as e:
            raise LLMError(
                f"Failed to initialize local LLM: {e}",
                details={"model": self.settings.LOCAL_LLM_MODEL}
            )


class HuggingFaceAPIProvider(BaseLLMProvider):
    """
    HuggingFace API provider for cloud-based inference.
    
    Alternative to Gemini when you prefer HuggingFace's models.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._llm = None
    
    def is_available(self) -> bool:
        """Check if HuggingFace API key is configured."""
        return bool(self.settings.HUGGINGFACE_API_KEY)
    
    def get_llm(self) -> BaseLanguageModel:
        """
        Get the HuggingFace API LLM instance.
        
        Returns:
            Configured HuggingFace LLM.
            
        Raises:
            ConfigurationError: If API key is not set.
            LLMError: If initialization fails.
        """
        if self._llm is not None:
            return self._llm
        
        if not self.is_available():
            raise ConfigurationError(
                "HuggingFace API key not configured",
                details={"setting": "HUGGINGFACE_API_KEY"}
            )
        
        try:
            from langchain_huggingface import HuggingFaceEndpoint
            
            logger.info("Initializing HuggingFace API LLM")
            
            self._llm = HuggingFaceEndpoint(
                repo_id=self.settings.LOCAL_LLM_MODEL,
                huggingfacehub_api_token=self.settings.HUGGINGFACE_API_KEY,
                temperature=self.settings.TEMPERATURE,
                max_new_tokens=self.settings.MAX_NEW_TOKENS,
            )
            
            logger.info("HuggingFace API LLM initialized successfully")
            return self._llm
            
        except Exception as e:
            raise LLMError(
                f"Failed to initialize HuggingFace API LLM: {e}",
                details={"repo_id": self.settings.LOCAL_LLM_MODEL}
            )


class LLMManager:
    """
    Unified LLM Manager with automatic provider selection.
    
    This manager handles multiple LLM providers and automatically
    selects the appropriate one based on configuration and availability.
    
    Provider Priority:
    1. Gemini (if API key configured)
    2. HuggingFace API (if API key configured)
    3. Local LLM (when hardware is available)
    
    Example:
        >>> manager = LLMManager()
        >>> llm = manager.get_llm()
        >>> response = llm.invoke("Hello!")
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize the LLM manager.
        
        Args:
            provider: Force a specific provider ('gemini', 'local', 'huggingface').
                     If None, uses the config setting.
        """
        self.settings = get_settings()
        self.provider_name = provider or self.settings.LLM_PROVIDER
        
        # Initialize providers
        self._providers: Dict[str, BaseLLMProvider] = {
            "gemini": GeminiProvider(),
            "local": LocalLLMProvider(),
            "huggingface": HuggingFaceAPIProvider(),
        }
        
        self._current_llm: Optional[BaseLanguageModel] = None
        
        logger.info(f"LLMManager initialized with provider preference: {self.provider_name}")
    
    def get_llm(self) -> BaseLanguageModel:
        """
        Get the LLM instance based on configuration.
        
        Returns:
            Configured LLM instance.
            
        Raises:
            LLMError: If no LLM provider is available.
        """
        if self._current_llm is not None:
            return self._current_llm
        
        # Try the configured provider first
        provider = self._providers.get(self.provider_name)
        if provider and provider.is_available():
            try:
                self._current_llm = provider.get_llm()
                logger.info(f"Using LLM provider: {self.provider_name}")
                return self._current_llm
            except Exception as e:
                logger.warning(f"Failed to initialize {self.provider_name}: {e}")
        
        # Fallback to other providers
        fallback_order = ["gemini", "huggingface", "local"]
        for provider_name in fallback_order:
            if provider_name == self.provider_name:
                continue  # Already tried
            
            provider = self._providers.get(provider_name)
            if provider and provider.is_available():
                try:
                    self._current_llm = provider.get_llm()
                    logger.info(f"Fallback to LLM provider: {provider_name}")
                    return self._current_llm
                except Exception as e:
                    logger.warning(f"Fallback {provider_name} failed: {e}")
        
        raise LLMError(
            "No LLM provider available",
            details={
                "configured_provider": self.provider_name,
                "available_providers": self.list_available_providers(),
                "suggestion": "Configure GEMINI_API_KEY in .env file"
            }
        )
    
    def list_available_providers(self) -> List[str]:
        """List all available LLM providers."""
        return [
            name for name, provider in self._providers.items()
            if provider.is_available()
        ]
    
    def get_provider_status(self) -> Dict[str, bool]:
        """Get availability status of all providers."""
        return {
            name: provider.is_available()
            for name, provider in self._providers.items()
        }
    
    def switch_provider(self, provider_name: str) -> BaseLanguageModel:
        """
        Switch to a different LLM provider.
        
        Args:
            provider_name: Name of the provider to switch to.
            
        Returns:
            LLM instance from the new provider.
        """
        if provider_name not in self._providers:
            raise LLMError(
                f"Unknown provider: {provider_name}",
                details={"available": list(self._providers.keys())}
            )
        
        provider = self._providers[provider_name]
        if not provider.is_available():
            raise LLMError(
                f"Provider not available: {provider_name}",
                details={"reason": "API key not configured or hardware unavailable"}
            )
        
        self._current_llm = None
        self.provider_name = provider_name
        return self.get_llm()


# Global LLM manager instance
_llm_manager: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    """Get the global LLM manager instance."""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager
