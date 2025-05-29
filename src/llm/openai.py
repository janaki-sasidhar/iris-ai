"""OpenAI GPT LLM client implementation"""

import httpx
import json
import logging
import traceback
from typing import List, Dict, Any
import base64

from .base import BaseLLMClient
from ..config.settings import settings

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI GPT API client"""
    
    def __init__(self):
        """Initialize OpenAI client with proxy endpoint"""
        self.api_key = settings.VORREN_API_KEY
        # Use the proxy endpoint for OpenAI
        self.base_url = settings.PROXY_ENDPOINTS["openai"]
        
        # Available OpenAI models
        self.models = {
            "o4-mini": "o4-mini-2025-04-16",  # reasoning model
            "gpt-4.1": "gpt-4.1-2025-04-14",  # non-reasoning
            "gpt-4o": "gpt-4o-2024-08-06"      # non-reasoning
        }
        
        # Create HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=120.0
        )
    
    def _prepare_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare messages in OpenAI format"""
        formatted_messages = []
        
        for msg in messages:
            # Create message content
            if msg.get("image_data"):
                # Handle multimodal content
                content = [
                    {
                        "type": "text",
                        "text": msg.get("content", "")
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{msg['image_data']}"
                        }
                    }
                ]
            else:
                # Text-only content
                content = msg.get("content", "")
            
            # OpenAI uses "user" and "assistant" roles
            formatted_messages.append({
                "role": msg["role"],
                "content": content
            })
        
        return formatted_messages
    
    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        model_name: str,
        max_tokens: int = None,
        temperature: float = 0.7,
        thinking_mode: bool = False,
        web_search_mode: bool = False
    ) -> str:
        """Generate a response using OpenAI Chat Completions API"""
        try:
            # Prepare messages
            formatted_messages = self._prepare_messages(messages)
            
            # Build request payload in OpenAI format
            # Note: These models only support temperature=1
            payload = {
                "model": model_name,
                "messages": formatted_messages,
                "temperature": 1.0  # These models only support default temperature
            }
            
            if temperature != 1.0:
                logger.info(f"Temperature {temperature} requested but model {model_name} only supports 1.0")
            
            # Add system message for thinking mode if enabled
            if thinking_mode:
                system_message = {
                    "role": "system",
                    "content": "Think through your response step by step. Show your reasoning process clearly before providing the final answer."
                }
                payload["messages"].insert(0, system_message)
            
            logger.info(f"Sending request to OpenAI with model: {model_name}")
            
            # Make API request to Chat Completions endpoint
            print(f"payload is {json.dumps(payload, indent=2)}")  # Debugging output
            response = await self.client.post(
                "/v1/chat/completions",
                json=payload
            )
            
            # Check response status
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"OpenAI API error: {response.status_code} - {error_detail}")
                # Don't expose API errors to users
                return "I apologize, but I encountered an error processing your request. Please try again later."
            
            # Parse response
            response_data = response.json()
            print(f"OpenAI response: {json.dumps(response_data, indent=2)}")  # Debugging output
            logger.info("Received response from OpenAI API")
            
            # Extract content from OpenAI response format
            if response_data.get("choices") and len(response_data["choices"]) > 0:
                choice = response_data["choices"][0]
                if choice.get("message") and choice["message"].get("content"):
                    content = choice["message"]["content"]
                    
                    # If thinking mode is enabled, format the response
                    if thinking_mode and "step" in content.lower():
                        # Try to separate thinking from final answer
                        parts = content.split("\n\n")
                        thinking_parts = []
                        answer_parts = []
                        
                        in_answer = False
                        for part in parts:
                            if any(keyword in part.lower() for keyword in ["final answer", "conclusion", "therefore", "in summary"]):
                                in_answer = True
                            
                            if in_answer:
                                answer_parts.append(part)
                            else:
                                thinking_parts.append(part)
                        
                        if thinking_parts and answer_parts:
                            thinking_text = "🧠 **Thinking Process:**\n\n" + "\n\n".join(thinking_parts)
                            answer_text = "\n\n".join(answer_parts)
                            return thinking_text + "\n\n💬 **Response:**\n\n" + answer_text
                    
                    return content
            
            return "I couldn't generate a response."
            
        except httpx.TimeoutException:
            logger.error("Request to OpenAI API timed out")
            return "I apologize, but the request timed out. Please try again later."
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            # Don't expose exception details to users
            return "I apologize, but I encountered an internal error. Please try again later."
    
    def get_available_models(self) -> Dict[str, str]:
        """Get available OpenAI models"""
        return self.models.copy()
    
    def supports_thinking_mode(self) -> bool:
        """OpenAI models support thinking mode through prompting"""
        return True
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close HTTP client"""
        await self.client.aclose()