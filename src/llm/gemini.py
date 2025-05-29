"""Gemini LLM client implementation"""

from google import genai
from google.genai import types
from typing import List, Dict, Any
import base64
from PIL import Image
import io

from .base import BaseLLMClient
from ..config.settings import settings


class GeminiClient(BaseLLMClient):
    """Google Gemini API client"""
    
    def __init__(self):
        """Initialize Gemini client with API key"""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.models = {
            "flash": "gemini-2.5-flash-preview-05-20",
            "pro": "gemini-2.5-pro-preview-05-06"
        }
    
    def _prepare_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare messages for google-genai API format"""
        formatted_messages = []
        
        for msg in messages:
            content_parts = []
            
            # Add text content
            if msg.get("content"):
                content_parts.append({"text": msg["content"]})
            
            # Add image if present
            if msg.get("image_data"):
                try:
                    # Base64 image data
                    content_parts.append({
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": msg["image_data"]
                        }
                    })
                except Exception as e:
                    print(f"Error processing image: {e}")
            
            # Map role names - google-genai uses "model" not "assistant"
            role = "user" if msg["role"] == "user" else "model"
            
            formatted_messages.append({
                "role": role,
                "parts": content_parts
            })
        
        return formatted_messages
    
    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        model_name: str,
        max_tokens: int = None,
        temperature: float = 0.7,
        thinking_mode: bool = False
    ) -> str:
        """Generate a response using google-genai API"""
        try:
            # Prepare messages
            formatted_messages = self._prepare_messages(messages)
            
            # Build generation config
            config_params = {"temperature": temperature}
            if max_tokens is not None:
                config_params["max_output_tokens"] = max_tokens
            
            # Add thinking config if enabled
            if thinking_mode:
                config_params["thinking_config"] = types.ThinkingConfig(
                    include_thoughts=True
                )
            
            generation_config = types.GenerateContentConfig(**config_params)
            
            # Generate response
            response = await self.client.aio.models.generate_content(
                model=model_name,
                contents=formatted_messages,
                config=generation_config
            )
            
            # Extract text from response
            if response.candidates and response.candidates[0].content.parts:
                # Combine all text parts (excluding thoughts)
                text_parts = []
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                
                return ' '.join(text_parts) if text_parts else "I couldn't generate a response."
            else:
                return "I couldn't generate a response."
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def get_available_models(self) -> Dict[str, str]:
        """Get available Gemini models"""
        return self.models.copy()
    
    def supports_thinking_mode(self) -> bool:
        """Gemini supports thinking mode"""
        return True