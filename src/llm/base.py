"""Base class for LLM clients"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients"""
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        model_name: str,
        max_tokens: int = None,
        temperature: float = 0.7,
        thinking_mode: bool = False
    ) -> str:
        """Generate a response from the LLM
        
        Args:
            messages: List of conversation messages
            model_name: Name of the model to use
            max_tokens: Maximum tokens in response (optional, uses model default if None)
            temperature: Temperature for generation
            thinking_mode: Whether to enable thinking mode
            
        Returns:
            Generated response text
        """
        pass
    
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