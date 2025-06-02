"""Anthropic Claude LLM client implementation"""

import httpx
import json
import logging
import traceback
from typing import List, Dict, Any, AsyncGenerator
import base64
import asyncio

from .base import BaseLLMClient
from ..config.settings import settings

logger = logging.getLogger(__name__)


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client"""
    
    def __init__(self):
        """Initialize Anthropic client with proxy endpoint"""
        self.api_key = settings.VORREN_API_KEY
        # Use the proxy endpoint but with messages API
        self.base_url = settings.PROXY_ENDPOINTS["aws-claude"]
        
        # Available Claude models - using the correct model names
        self.models = {
            "claude-sonnet-4": "claude-sonnet-4-20250514",
            "claude-3.7-sonnet": "claude-3-7-sonnet-20250219",
            "claude-3.5-sonnet": "claude-3-5-sonnet-20241022"
        }
        
        # Create HTTP client with Anthropic-specific headers
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            timeout=120.0
        )
    
    def _prepare_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare messages in Anthropic format"""
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
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": msg['image_data']
                        }
                    }
                ]
            else:
                # Text-only content
                content = msg.get("content", "")
            
            # Anthropic uses "user" and "assistant" roles
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
        web_search_mode: bool = False  # Keep parameter for interface compatibility
    ) -> str:
        """Generate a response using Anthropic Messages API"""
        try:
            # Prepare messages
            formatted_messages = self._prepare_messages(messages)
            
            # Build request payload in Anthropic format
            # Anthropic requires max_tokens to be set
            default_max_tokens = 10000
            thinking_budget = 5000
            
            if thinking_mode:
                payload = {
                    "model": model_name,
                    "messages": formatted_messages,
                    "max_tokens": default_max_tokens,
                    "temperature": 1.0  # Must be 1.0 with thinking mode
                }
                
                payload["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": thinking_budget
                }
                
                logger.info(f"Thinking mode enabled: temperature=1.0, max_tokens={default_max_tokens}, thinking_budget={thinking_budget}")
            else:
                payload = {
                    "model": model_name,
                    "messages": formatted_messages,
                    "max_tokens": default_max_tokens,
                    "temperature": temperature
                }
            
            logger.info(f"Sending request to Anthropic with model: {model_name}")
            
            # Make API request to Messages endpoint
            response = await self.client.post(
                "/v1/messages",
                json=payload
            )
            
            # Check response status
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Anthropic API error: {response.status_code} - {error_detail}")
                # Don't expose API errors to users
                return "I apologize, but I encountered an error processing your request. Please try again later."
            
            # Parse response
            response_data = response.json()
            print(response_data)  # Debugging output
            logger.info("Received response from Anthropic API")
            
            # Extract thinking and text from the response
            thinking_text = ""
            text_parts = []
            
            # Check if content is present in the response
            if response_data.get("content") and len(response_data["content"]) > 0:
                # Process each content block
                for content_block in response_data["content"]:
                    block_type = content_block.get("type")
                    
                    # Extract thinking
                    if block_type == "thinking" and thinking_mode:
                        thinking = content_block.get("thinking", "")
                        if thinking:
                            thinking_text = "🧠 **Thinking Process:**\n\n" + thinking + "\n\n"
                            logger.info("Thinking process received from Claude")
                    
                    # Extract text
                    elif block_type == "text":
                        text_parts.append(content_block.get("text", ""))
                
                final_response = " ".join(text_parts)
                
                # Prepend thinking if available, and add clear separator for response
                if thinking_text:
                    return thinking_text + "💬 **Response:**\n\n" + final_response
                return final_response
            
            return "I couldn't generate a response."
            
        except httpx.TimeoutException:
            logger.error("Request to Anthropic API timed out")
            return "I apologize, but the request timed out. Please try again later."
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            # Don't expose exception details to users
            return "I apologize, but I encountered an internal error. Please try again later."
    
    async def generate_response_stream(
        self,
        messages: List[Dict[str, Any]],
        model_name: str,
        max_tokens: int = None,
        temperature: float = 0.7,
        thinking_mode: bool = False,
        web_search_mode: bool = False
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response using Anthropic Messages API"""
        try:
            # Prepare messages
            formatted_messages = self._prepare_messages(messages)
            
            # Build request payload with streaming
            default_max_tokens = 10000
            thinking_budget = 5000
            
            if thinking_mode:
                payload = {
                    "model": model_name,
                    "messages": formatted_messages,
                    "max_tokens": default_max_tokens,
                    "temperature": 1.0,  # Must be 1.0 with thinking mode
                    "stream": True  # Enable streaming
                }
                
                payload["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": thinking_budget
                }
                
                logger.info(f"Streaming with thinking mode: temperature=1.0, max_tokens={default_max_tokens}, thinking_budget={thinking_budget}")
            else:
                payload = {
                    "model": model_name,
                    "messages": formatted_messages,
                    "max_tokens": default_max_tokens,
                    "temperature": temperature,
                    "stream": True  # Enable streaming
                }
            
            logger.info(f"Sending streaming request to Anthropic with model: {model_name}")
            
            # Make streaming API request
            async with self.client.stream(
                "POST",
                "/v1/messages",
                json=payload
            ) as response:
                # Check response status
                if response.status_code != 200:
                    error_detail = await response.aread()
                    logger.error(f"Anthropic API error: {response.status_code} - {error_detail}")
                    yield "I apologize, but I encountered an error processing your request. Please try again later."
                    return
                
                # Track content blocks and thinking
                thinking_parts = []
                in_thinking_block = False
                thinking_yielded = False
                
                # Process streaming response
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        try:
                            data = json.loads(data_str)
                            event_type = data.get("type")
                            
                            # Handle different event types
                            if event_type == "content_block_start":
                                # Check if this is a thinking block
                                content_block = data.get("content_block", {})
                                if content_block.get("type") == "thinking":
                                    in_thinking_block = True
                                else:
                                    in_thinking_block = False
                                    # If we have thinking content and haven't yielded it yet
                                    if thinking_mode and thinking_parts and not thinking_yielded:
                                        thinking_text = "🧠 **Thinking Process:**\n\n" + "".join(thinking_parts) + "\n\n💬 **Response:**\n\n"
                                        yield thinking_text
                                        thinking_yielded = True
                            
                            elif event_type == "content_block_delta":
                                # Extract delta content
                                delta = data.get("delta", {})
                                
                                if in_thinking_block and thinking_mode:
                                    # Accumulate thinking content
                                    thinking_content = delta.get("thinking", "")
                                    if thinking_content:
                                        thinking_parts.append(thinking_content)
                                else:
                                    # Yield text content
                                    text_content = delta.get("text", "")
                                    if text_content:
                                        yield text_content
                            
                            elif event_type == "message_stop":
                                # Stream is complete
                                break
                                
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse streaming data: {data_str}")
                            continue
                
        except httpx.TimeoutException:
            logger.error("Streaming request to Anthropic API timed out")
            yield "I apologize, but the request timed out. Please try again later."
        except Exception as e:
            error_msg = f"Error in streaming response: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            yield "I apologize, but I encountered an internal error. Please try again later."
    
    def get_available_models(self) -> Dict[str, str]:
        """Get available Claude models"""
        return self.models.copy()
    
    def supports_thinking_mode(self) -> bool:
        """All Claude models support thinking mode"""
        return True
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close HTTP client"""
        await self.client.aclose()
