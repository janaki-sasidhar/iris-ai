"""Factory for creating LLM clients"""

from typing import Dict, Type, List
from .base import BaseLLMClient
from .gemini import GeminiClient
from .anthropic import AnthropicClient
from .openai import OpenAIClient


class LLMFactory:
    """Factory for creating LLM client instances"""
    
    # Registry of available LLM providers
    _providers: Dict[str, Type[BaseLLMClient]] = {
        "gemini": GeminiClient,
        "anthropic": AnthropicClient,
        "openai": OpenAIClient,
    }
    
    @classmethod
    def create(cls, provider: str = "gemini") -> BaseLLMClient:
        """Create an LLM client instance
        
        Args:
            provider: Name of the LLM provider
            
        Returns:
            LLM client instance
            
        Raises:
            ValueError: If provider is not supported
        """
        if provider not in cls._providers:
            raise ValueError(f"Unknown LLM provider: {provider}. Available: {list(cls._providers.keys())}")
        
        return cls._providers[provider]()
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseLLMClient]):
        """Register a new LLM provider
        
        Args:
            name: Name for the provider
            provider_class: Class implementing BaseLLMClient
        """
        cls._providers[name] = provider_class
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available providers"""
        return list(cls._providers.keys())