"""
Example: Adding OpenAI as a new LLM provider

This file demonstrates how easy it is to add a new LLM provider
to the refactored bot architecture.
"""

from typing import List, Dict, Any
import openai  # pip install openai
from src.llm.base import BaseLLMClient


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT client implementation"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        # You would get this from settings
        self.api_key = "your-openai-api-key"
        openai.api_key = self.api_key
        
        self.models = {
            "gpt4": "gpt-4",
            "gpt35": "gpt-3.5-turbo",
            "gpt4-turbo": "gpt-4-turbo-preview"
        }
    
    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        model_name: str,
        max_tokens: int,
        temperature: float,
        thinking_mode: bool = False
    ) -> str:
        """Generate a response using OpenAI API"""
        try:
            # Convert messages to OpenAI format
            openai_messages = []
            
            for msg in messages:
                content = msg.get("content", "")
                
                # Handle image data if present
                if msg.get("image_data"):
                    # OpenAI expects base64 images in a specific format
                    content = [
                        {"type": "text", "text": content},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{msg['image_data']}"
                            }
                        }
                    ]
                
                openai_messages.append({
                    "role": msg["role"],  # OpenAI uses "user" and "assistant"
                    "content": content
                })
            
            # Add system message for thinking mode
            if thinking_mode:
                openai_messages.insert(0, {
                    "role": "system",
                    "content": "Think through your response step by step before answering."
                })
            
            # Make API call
            response = await openai.ChatCompletion.acreate(
                model=model_name,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error with OpenAI: {str(e)}"
    
    def get_available_models(self) -> Dict[str, str]:
        """Get available OpenAI models"""
        return self.models.copy()
    
    def supports_thinking_mode(self) -> bool:
        """OpenAI supports thinking through system prompts"""
        return True


# To register this provider, add to src/llm/factory.py:
"""
from .openai_client import OpenAIClient

class LLMFactory:
    _providers: Dict[str, Type[BaseLLMClient]] = {
        "gemini": GeminiClient,
        "openai": OpenAIClient,  # Add this line
    }
"""

# Then in your bot configuration, you could:
"""
# src/config/settings.py
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # Can be "gemini" or "openai"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
"""

# And in the message handler:
"""
# src/bot/handlers.py
self.llm_client = LLMFactory.create(settings.LLM_PROVIDER)
"""

# That's it! The bot now supports multiple LLM providers.