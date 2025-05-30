"""Main message handlers for the bot"""

from telethon import events
from google import genai
from google.genai import types
import base64
import traceback
import logging
import os
import re

from .decorators import require_authorization
from ..database import DatabaseManager
from ..llm import LLMFactory
from ..config.settings import settings
from ..utils import MessageSplitter
from ..utils.file_handler import file_handler

# Set up logging
logger = logging.getLogger(__name__)


class MessageHandler:
    """Handles regular messages and AI interactions"""
    
    def __init__(self, client, db_manager: DatabaseManager):
        self.client = client
        self.db_manager = db_manager
        self.message_splitter = MessageSplitter()
    
    @require_authorization
    async def handle_message(self, event):
        """Handle regular text/image messages"""
        user = await event.get_sender()
        
        # Check for ping command
        if event.message.message.strip() == "!ping":
            await event.reply("!pong")
            return
        
        # Get or create user in database
        db_user = await self.db_manager.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Get or create conversation
        conversation = await self.db_manager.get_active_conversation(db_user.id)
        if not conversation:
            conversation = await self.db_manager.create_conversation(db_user.id)
        
        # Extract message content
        message_text = event.message.message
        image_path = None
        
        # Check if message has photo
        if event.message.photo:
            # Download photo
            photo_bytes = await event.message.download_media(bytes)
            if photo_bytes:
                # Save image to disk and get path
                mime_type = "image/jpeg"  # Default for Telegram photos
                image_path = await file_handler.save_user_image(photo_bytes, mime_type)
        
        # Save user message
        await self.db_manager.add_message(
            conversation_id=conversation.id,
            role="user",
            content=message_text,
            image_path=image_path
        )
        
        # Get conversation history
        messages = await self.db_manager.get_conversation_messages(conversation.id)
        
        # Add user context as the first message if this is a new conversation
        if len(messages) == 1:  # Only the current message
            user_context = f"You are chatting with {user.first_name or 'a user'}"
            if user.username:
                user_context += f" (@{user.username})"
            user_context += ". Respond in a friendly and helpful manner."
            
            # Insert context at the beginning
            messages.insert(0, {
                "role": "user",
                "content": user_context
            })
            messages.insert(1, {
                "role": "assistant",
                "content": "I understand. I'll help you with your questions."
            })
        
        # Get user settings
        settings_dict = await self.db_manager.get_user_settings(db_user.id)
        
        # Determine which LLM provider to use based on model
        model_name = settings_dict["model"]
        if "claude" in model_name:
            provider = "anthropic"
        elif "gpt" in model_name or "o4" in model_name:
            provider = "openai"
        else:
            provider = "gemini"
        
        # Generate response
        try:
            # Check if using image generation model
            is_image_gen_model = settings_dict["model"] in [
                "gemini-2.0-flash-preview-image-generation",
                "imagen-3.0-generate-002"
            ]
            
            # Check if thinking mode is enabled and model is Gemini (but not image gen)
            if settings_dict.get("thinking_mode", False) and provider == "gemini" and not is_image_gen_model:
                # Use direct API for thinking mode to get raw response
                response = await self._generate_with_thinking(
                    event=event,
                    messages=messages,
                    settings_dict=settings_dict  # Fixed parameter name
                )
            else:
                # Normal response or Claude with thinking mode
                async with LLMFactory.create(provider) as llm_client:
                    response = await llm_client.generate_response(
                        messages=messages,
                        model_name=settings_dict["model"],
                        temperature=settings_dict["temperature"],
                        thinking_mode=settings_dict.get("thinking_mode", False),
                        web_search_mode=settings_dict.get("web_search_mode", False)
                    )
        except Exception as e:
            # Log the full error to terminal/logs
            logger.error(f"Error generating AI response: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"\n❌ ERROR in message handler: {str(e)}")
            print(traceback.format_exc())
            
            # Send generic error message to user
            response = "I apologize, but I encountered an internal error. Please try again later or contact the bot administrator."
        
        # Check if response contains generated images
        image_match = re.match(r'\[IMAGE_GENERATED:(.*?)\]\n?(.*)', response, re.DOTALL)
        if image_match:
            image_paths_str = image_match.group(1)
            text_response = image_match.group(2) or ""
            image_paths = image_paths_str.split("|") if image_paths_str else []
            
            # Save text response to database (without image markers)
            await self.db_manager.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=text_response if text_response else "Generated image(s)"
            )
        else:
            # Save regular response
            await self.db_manager.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=response
            )
            image_paths = []
            text_response = response
        
        # Format temperature display
        temp = settings_dict["temperature"]
        if temp <= 0.3:
            temp_desc = "focused"
        elif temp <= 0.6:
            temp_desc = "balanced"
        elif temp <= 0.8:
            temp_desc = "creative"
        else:
            temp_desc = "very creative"
        
        # Add model info footer
        current_model = settings_dict["model"]
        
        # Determine model display name for footer
        if "claude" in current_model:
            if "claude-sonnet-4" in current_model:
                model_display = "Claude Sonnet 4"
            elif "claude-3-7-sonnet" in current_model:
                model_display = "Claude 3.7 Sonnet"
            elif "claude-3-5-sonnet" in current_model:
                model_display = "Claude 3.5 Sonnet"
            else:
                model_display = "Claude"
        elif "gpt" in current_model or "o4" in current_model:
            if "o4-mini" in current_model:
                model_display = "O4 Mini (Reasoning)"
            elif "gpt-4.1" in current_model:
                model_display = "GPT-4.1"
            elif "gpt-4o" in current_model:
                model_display = "GPT-4o"
            else:
                model_display = "GPT"
        else:
            if "gemini-2.0-flash-preview-image-generation" in current_model:
                model_display = "Gemini 2.0 Flash (Image Gen)"
            elif "imagen-3.0-generate-002" in current_model:
                model_display = "Imagen 3"
            elif "flash" in current_model:
                model_display = "Gemini 2.5 Flash"
            else:
                model_display = "Gemini 2.5 Pro"
        
        footer = f"\n\n===\nModel: {model_display} ({temp_desc} temp)"
        
        # Send response based on whether images were generated
        if image_paths:
            # Send text response first if any
            if text_response:
                await self.message_splitter.send_long_message(event, text_response + footer, parse_mode='markdown')
            else:
                await event.reply(f"I've generated the image(s) you requested!{footer}", parse_mode='markdown')
            
            # Then send images
            for image_path in image_paths:
                if os.path.exists(image_path):
                    try:
                        # Move image to permanent storage
                        permanent_path = await file_handler.save_generated_image(image_path)
                        
                        # Send the image from permanent location
                        await event.respond(file=permanent_path)
                        
                        # Note: We're keeping the image in permanent storage now
                        # If you want to save the generated image path to database, you could do:
                        # await self.db_manager.add_generated_image_reference(conversation.id, permanent_path)
                    except Exception as e:
                        logger.error(f"Error sending image {image_path}: {e}")
                        # Clean up temp file if something went wrong
                        if os.path.exists(image_path):
                            os.remove(image_path)
        else:
            # Send regular text response
            await self.message_splitter.send_long_message(event, text_response + footer, parse_mode='markdown')
    
    async def _generate_with_thinking(self, event, messages, settings_dict):
        """Generate response with thinking mode enabled"""
        # Create direct client for thinking mode
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # Build generation config
        generation_config = types.GenerateContentConfig(
            temperature=settings_dict["temperature"],
            thinking_config=types.ThinkingConfig(
                include_thoughts=True
            )
        )
        
        # Prepare messages in google-genai format
        formatted_messages = []
        for msg in messages:
            content_parts = []
            if msg.get("content"):
                content_parts.append({"text": msg["content"]})
            if msg.get("image_data"):
                content_parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": msg["image_data"]
                    }
                })
            
            role = "user" if msg["role"] == "user" else "model"
            formatted_messages.append({
                "role": role,
                "parts": content_parts
            })
        
        # Generate with thinking using full conversation history
        raw_response = await client.aio.models.generate_content(
            model=settings_dict["model"],
            contents=formatted_messages,
            config=generation_config
        )
        
        # Extract thinking and answer parts
        thinking_parts = []
        answer_parts = []
        
        if raw_response.candidates and raw_response.candidates[0].content.parts:
            for part in raw_response.candidates[0].content.parts:
                if not part.text:
                    continue
                if part.thought:
                    thinking_parts.append(part.text)
                else:
                    answer_parts.append(part.text)
        
        # Send thinking first if available
        if thinking_parts:
            thinking_msg = "🧠 **Thinking Process:**\n\n" + '\n'.join(thinking_parts)
            await self.message_splitter.send_long_message(event, thinking_msg, parse_mode='markdown')
        
        # Return answer parts
        return ' '.join(answer_parts) if answer_parts else "I couldn't generate a response."
    
    def register_handlers(self):
        """Register message handlers"""
        # Handle all non-command messages
        self.client.add_event_handler(
            self.handle_message,
            events.NewMessage(func=lambda e: not e.message.message.startswith('/'))
        )