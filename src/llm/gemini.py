"""Gemini LLM client implementation"""

from google import genai
from google.genai import types
from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator
import base64
from PIL import Image
import io
import os
import tempfile
from datetime import datetime

from .base import BaseLLMClient
from ..config.settings import settings


class GeminiClient(BaseLLMClient):
    """Google Gemini API client"""
    
    def __init__(self):
        """Initialize Gemini client with API key"""
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.models = {
            "flash": "gemini-2.5-flash-preview-05-20",
            "pro": "gemini-2.5-pro-preview-05-06",
            "flash-image": "gemini-2.0-flash-preview-image-generation",
            "imagen3": "imagen-3.0-generate-002"
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
            
            # Only add message if it has content
            if content_parts:
                # Map role names - google-genai uses "model" not "assistant"
                role = "user" if msg["role"] == "user" else "model"
                
                formatted_messages.append({
                    "role": role,
                    "parts": content_parts
                })
        
        return formatted_messages
    
    def _prepare_flash_image_contents(self, messages: List[Dict[str, Any]]) -> List[Any]:
        """Prepare contents for Gemini 2.0 Flash image generation as a flat list"""
        contents = []
        
        # For flash image generation, create a flat list of text and image inputs
        for msg in messages:
            # Only process user messages for image generation
            if msg["role"] == "user":
                # Add text content
                if msg.get("content"):
                    contents.append(msg["content"])
                
                # Add image if present
                if msg.get("image_data"):
                    try:
                        # Create PIL Image from base64 data
                        image_data = base64.b64decode(msg["image_data"])
                        image = Image.open(io.BytesIO(image_data))
                        contents.append(image)
                    except Exception as e:
                        print(f"Error processing image for flash generation: {e}")
        
        return contents
    
    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        model_name: str,
        max_tokens: int = None,
        temperature: float = 0.7,
        thinking_mode: bool = False,
        web_search_mode: bool = False
    ) -> str:
        """Generate a response using google-genai API"""
        try:
            # For Imagen3, only use the last user message as it's purely for image generation
            if model_name == self.models.get("imagen3"):
                # Find the last user message
                last_user_message = None
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        last_user_message = msg
                        break
                
                if last_user_message:
                    # Only use the last user message for Imagen3
                    messages_to_use = [last_user_message]
                else:
                    # Fallback to all messages if no user message found
                    messages_to_use = messages
            else:
                # For all other models including Gemini 2.0 Flash image gen, use full conversation history
                messages_to_use = messages
            
            # Prepare messages based on model type
            if model_name == self.models.get("flash-image"):
                # For flash image generation, use flat content list
                formatted_contents = self._prepare_flash_image_contents(messages_to_use)
            else:
                # For other models, use standard message format
                formatted_messages = self._prepare_messages(messages_to_use)
            
            # Build generation config
            config_params = {"temperature": temperature}
            if max_tokens is not None:
                config_params["max_output_tokens"] = max_tokens
            
            # Add thinking config if enabled
            if thinking_mode:
                config_params["thinking_config"] = types.ThinkingConfig(
                    include_thoughts=True
                )
            
            # Check if using image generation model
            is_image_gen_model = model_name in [self.models.get("flash-image"), self.models.get("imagen3")]
            
            # Add Google Search tool if enabled (but not for image generation models)
            if web_search_mode and not is_image_gen_model:
                google_search_tool = types.Tool(
                    google_search=types.GoogleSearch()
                )
                config_params["tools"] = [google_search_tool]
                config_params["response_modalities"] = ["TEXT"]
            
            # Enable image generation for flash-image model
            if model_name == self.models.get("flash-image"):
                config_params["response_modalities"] = ["TEXT", "IMAGE"]
            
            generation_config = types.GenerateContentConfig(**config_params)
            
            # Handle Imagen3 separately
            if model_name == self.models.get("imagen3"):
                return await self._generate_imagen3(messages, temperature)
            
            print(f"Generating response with model: {model_name}, config: {generation_config}")
            # Generate response
            if model_name == self.models.get("flash-image"):
                # For flash image generation, pass contents directly
                response = await self.client.aio.models.generate_content(
                    model=model_name,
                    contents=formatted_contents,
                    config=generation_config
                )
            else:
                # For other models, use standard format
                response = await self.client.aio.models.generate_content(
                    model=model_name,
                    contents=formatted_messages,
                    config=generation_config
                )

            import pprint
            pprint.pprint(response)  # Debugging: print the full response

            
            # Extract text and images from response
            if response.candidates and response.candidates[0].content.parts:
                text_parts = []
                image_paths = []
                
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                    elif hasattr(part, 'inline_data') and part.inline_data:
                        # Save image to temporary file
                        image_path = await self._save_image_from_inline_data(part.inline_data)
                        if image_path:
                            image_paths.append(image_path)
                
                final_response = ' '.join(text_parts) if text_parts else ""
                
                # If images were generated, include them in response
                if image_paths:
                    # Return special format that indicates images
                    image_info = "|".join(image_paths)
                    return f"[IMAGE_GENERATED:{image_info}]\n{final_response}"
                
                # Check if web search was actually used (not just enabled)
                # Only show indicator if web search was enabled AND model supports it
                if web_search_mode and not is_image_gen_model and hasattr(response.candidates[0], 'grounding_metadata'):
                    # Just add a simple indicator that search was used
                    return f"🔍 *Web search used*\n\n{final_response}"
                
                return final_response if final_response else "I couldn't generate a response."
            else:
                return "I couldn't generate a response."
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            return f"I apologize, but I encountered an error: {str(e)}"
    
    async def _save_image_from_inline_data(self, inline_data) -> Optional[str]:
        """Save inline image data to a temporary file"""
        try:
            # Create temporary directory if it doesn't exist
            temp_dir = os.path.join(tempfile.gettempdir(), "gemini_images")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gemini_image_{timestamp}.png"
            filepath = os.path.join(temp_dir, filename)
            
            # Save image
            image = Image.open(io.BytesIO(inline_data.data))
            image.save(filepath, 'PNG')
            
            return filepath
        except Exception as e:
            print(f"Error saving image: {e}")
            return None
    
    async def _generate_imagen3(self, messages: List[Dict[str, Any]], temperature: float) -> str:
        """Generate images using Imagen3 model"""
        try:
            # Extract the prompt from the last user message
            prompt = ""
            for msg in reversed(messages):
                if msg["role"] == "user" and msg.get("content"):
                    prompt = msg["content"]
                    break
            
            if not prompt:
                return "Please provide a prompt for image generation."
            
            # Generate images
            response = await self.client.aio.models.generate_images(
                model=self.models["imagen3"],
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,  # Generate 1 image by default
                )
            )
            
            # Save generated images
            image_paths = []
            for i, generated_image in enumerate(response.generated_images):
                try:
                    # Create temporary directory
                    temp_dir = os.path.join(tempfile.gettempdir(), "imagen3_images")
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Generate filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"imagen3_{timestamp}_{i}.png"
                    filepath = os.path.join(temp_dir, filename)
                    
                    # Save image
                    image = Image.open(io.BytesIO(generated_image.image.image_bytes))
                    image.save(filepath, 'PNG')
                    
                    image_paths.append(filepath)
                except Exception as e:
                    print(f"Error saving Imagen3 image {i}: {e}")
            
            if image_paths:
                image_info = "|".join(image_paths)
                return f"[IMAGE_GENERATED:{image_info}]\nGenerated {len(image_paths)} image(s) based on your prompt."
            else:
                return "Failed to generate images."
                
        except Exception as e:
            error_msg = f"Error generating Imagen3 response: {str(e)}"
            print(error_msg)
            return f"I apologize, but I encountered an error with image generation: {str(e)}"
    
    async def generate_response_stream(
        self,
        messages: List[Dict[str, Any]],
        model_name: str,
        max_tokens: int = None,
        temperature: float = 0.7,
        thinking_mode: bool = False,
        web_search_mode: bool = False
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response using google-genai API"""
        try:
            # Check for special cases that don't support streaming
            is_image_gen_model = model_name in [self.models.get("flash-image"), self.models.get("imagen3")]
            if is_image_gen_model:
                response = await self.generate_response(
                    messages=messages,
                    model_name=model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    thinking_mode=thinking_mode,
                    web_search_mode=web_search_mode
                )
                yield response
                return
            
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
            
            # Use the exact pattern from the documentation
            stream_iterator = await self.client.aio.models.generate_content_stream(
                model=model_name,
                contents=formatted_messages,
                config=generation_config
            )
            
            thinking_sent = False
            in_thinking = False
            
            async for chunk in stream_iterator:
                # Extract text from the proper structure
                if hasattr(chunk, 'candidates') and chunk.candidates:
                    for candidate in chunk.candidates:
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    # Check if this is a thinking part
                                    if thinking_mode and hasattr(part, 'thought') and part.thought:
                                        if not thinking_sent:
                                            yield "🧠 **Thinking Process:**\n\n"
                                            thinking_sent = True
                                        
                                        # If thinking text is very long, break it into smaller chunks
                                        text = part.text
                                        if len(text) > 200:  # If text is long, break it up
                                            # Split by sentences or newlines for natural breaks
                                            lines = text.split('\n')
                                            current_chunk = ""
                                            
                                            for line in lines:
                                                if len(current_chunk) + len(line) > 200:
                                                    if current_chunk:
                                                        yield current_chunk + "\n"
                                                        current_chunk = line
                                                else:
                                                    current_chunk += line + "\n" if current_chunk else line
                                            
                                            if current_chunk:
                                                yield current_chunk
                                        else:
                                            yield text
                                    else:
                                        # Regular text
                                        if thinking_mode and thinking_sent and not in_thinking:
                                            # First non-thinking text after thinking
                                            yield "\n\n💬 **Response:**\n\n"
                                            in_thinking = True
                                        yield part.text
                elif hasattr(chunk, 'text') and chunk.text:
                    # Fallback to direct text attribute if it exists
                    yield chunk.text
                    
        except Exception as e:
            # Fall back to non-streaming on error
            response = await self.generate_response(
                messages=messages,
                model_name=model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                thinking_mode=thinking_mode,
                web_search_mode=web_search_mode
            )
            yield response
    
    def get_available_models(self) -> Dict[str, str]:
        """Get available Gemini models"""
        return self.models.copy()
    
    def supports_thinking_mode(self) -> bool:
        """Gemini supports thinking mode"""
        return True
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        # No cleanup needed for Gemini client
        pass