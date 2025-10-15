"""Base class for LLM clients"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator, Optional


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        model_name: str,
        max_tokens: int = None,
        temperature: float = 0.7,
        thinking_mode: bool = False,
        web_search_mode: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a response from the LLM
        
        Args:
            messages: List of conversation messages
            model_name: Name of the model to use
            max_tokens: Maximum tokens in response (optional, uses model default if None)
            temperature: Temperature for generation
            thinking_mode: Whether to enable thinking mode
            web_search_mode: Whether to enable web search (provider-specific)
            
        Returns:
            Generated response text
        """
        pass
    
    async def generate_response_stream(
        self,
        messages: List[Dict[str, Any]],
        model_name: str,
        max_tokens: int = None,
        temperature: float = 0.7,
        thinking_mode: bool = False,
        web_search_mode: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM
        
        Args:
            messages: List of conversation messages
            model_name: Name of the model to use
            max_tokens: Maximum tokens in response (optional, uses model default if None)
            temperature: Temperature for generation
            thinking_mode: Whether to enable thinking mode
            web_search_mode: Whether to enable web search (provider-specific)
            
        Yields:
            Generated response text chunks
        """
        # Default implementation: just yield the full response
        # Subclasses can override for true streaming
        response = await self.generate_response(
            messages=messages,
            model_name=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            thinking_mode=thinking_mode,
            web_search_mode=web_search_mode,
            options=options,
        )
        yield response
    
    @abstractmethod
    def get_available_models(self) -> Dict[str, str]:
        """Get available models for this provider
        
        Returns:
            Dictionary of model aliases to model names
        """
        pass
    
    @abstractmethod
    def supports_thinking_mode(self) -> bool:
        """Check if this provider supports thinking mode
        
        Returns:
            True if thinking mode is supported
        """
        pass
