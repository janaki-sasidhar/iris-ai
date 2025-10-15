"""Main message handlers for the bot"""

from telethon import events
from google import genai
from google.genai import types
import base64
import traceback
import logging
import os
import re
import asyncio
import time

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
        print(f"Received message: {event.message.message}")
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
        print(f"Conversation messages: {messages}")
        
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
            # Check if using image generation model (none in current set)
            is_image_gen_model = False
            
            # Check if we should use streaming (for OpenAI, Anthropic, and Gemini models)
            use_streaming = (provider in ["openai", "anthropic", "gemini"]) and not is_image_gen_model
            
            # Build provider-specific options
            llm_options = {}
            if provider == "gemini":
                llm_options["thinking_tokens"] = settings_dict.get("gemini_thinking_tokens", 2048)
            elif provider == "openai":
                llm_options["reasoning_effort"] = settings_dict.get("gpt_reasoning_effort", "medium")
                llm_options["verbosity"] = settings_dict.get("gpt_verbosity", "medium")
                llm_options["search_context_size"] = settings_dict.get("gpt_search_context_size", "medium")
                llm_options["web_search_enabled"] = settings_dict.get("web_search_mode", False)

            if use_streaming:
                # Use streaming for OpenAI/Anthropic/Gemini - this will handle the message sending internally
                response = await self._generate_with_streaming(
                    event=event,
                    messages=messages,
                    settings_dict=settings_dict,
                    provider=provider,
                    conversation=conversation
                )
                # For streaming, the message has already been sent with footer
                return
            else:
                # Normal response for other providers
                async with LLMFactory.create(provider) as llm_client:
                    response = await llm_client.generate_response(
                        messages=messages,
                        model_name=settings_dict["model"],
                        temperature=settings_dict["temperature"],
                        thinking_mode=False,
                        web_search_mode=settings_dict.get("web_search_mode", False),
                        options=llm_options,
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
            if "claude-sonnet-4-5" in current_model:
                model_display = "Claude Sonnet 4.5"
            elif "claude-opus-4-1" in current_model:
                model_display = "Claude Opus 4.1"
            else:
                model_display = "Claude"
        elif "gpt-5" in current_model:
            model_display = "GPT‑5"
            if "chat" in current_model:
                model_display = "GPT‑5 Chat"
        else:
            if "gemini-2.5-flash" in current_model or "flash" in current_model:
                model_display = "Gemini 2.5 Flash"
            else:
                model_display = "Gemini 2.5 Pro"
        
        if "gpt-5" in current_model:
            footer = f"\n\n===\nModel: {model_display}"
        else:
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
    
    async def _generate_with_streaming(self, event, messages, settings_dict, provider, conversation):
        """Generate response with streaming for supported providers"""
        # Send initial message
        print('wtf streaming')
        current_message = await event.reply("💭 Generating response...")
        
        # Track accumulated response and messages
        accumulated_response = ""
        sent_messages = [current_message]
        last_update_time = time.time()
        update_interval = 3.0  # Update every 3 seconds to avoid rate limits
        message_overflow_handled = False
        chunks_since_update = 0
        min_chunks_before_update = 5  # Accumulate at least 5 chunks before updating
        
        # Prepare footer
        temp = settings_dict["temperature"]
        if temp <= 0.3:
            temp_desc = "focused"
        elif temp <= 0.6:
            temp_desc = "balanced"
        elif temp <= 0.8:
            temp_desc = "creative"
        else:
            temp_desc = "very creative"
        
        current_model = settings_dict["model"]
        if "claude" in current_model:
            if "claude-sonnet-4-5" in current_model:
                model_display = "Claude Sonnet 4.5"
            elif "claude-opus-4-1" in current_model:
                model_display = "Claude Opus 4.1"
            else:
                model_display = "Claude"
        elif "gpt-5" in current_model:
            model_display = "GPT‑5 Chat" if "chat" in current_model else "GPT‑5"
        elif "gemini" in current_model or provider == "gemini":
            if "flash" in current_model:
                model_display = "Gemini 2.5 Flash"
            else:
                model_display = "Gemini 2.5 Pro"
        else:
            model_display = "AI Model"
        
        footer = f"\n\n===\nModel: {model_display} ({temp_desc} temp)"
        streaming_indicator = "\n\n⏳ _Generating..._"
        
        try:
            async with LLMFactory.create(provider) as llm_client:
                # Check if the client supports streaming
                if hasattr(llm_client, 'generate_response_stream'):
                    # Provider-specific options
                    llm_options = {}
                    if provider == "gemini":
                        llm_options["thinking_tokens"] = settings_dict.get("gemini_thinking_tokens", 2048)
                    elif provider == "openai":
                        llm_options["reasoning_effort"] = settings_dict.get("gpt_reasoning_effort", "medium")
                        llm_options["verbosity"] = settings_dict.get("gpt_verbosity", "medium")
                        llm_options["search_context_size"] = settings_dict.get("gpt_search_context_size", "medium")
                    # Use streaming
                    async for chunk in llm_client.generate_response_stream(
                        messages=messages,
                        model_name=settings_dict["model"],
                        temperature=settings_dict["temperature"],
                        thinking_mode=False,
                        web_search_mode=settings_dict.get("web_search_mode", False),
                        options=llm_options,
                    ):
                        accumulated_response += chunk
                        chunks_since_update += 1
                        
                        # Update message at intervals AND after accumulating enough chunks
                        current_time = time.time()
                        time_to_update = current_time - last_update_time >= update_interval
                        enough_chunks = chunks_since_update >= min_chunks_before_update
                        
                        if time_to_update and enough_chunks:
                            try:
                                # Check if message would be too long
                                display_text = accumulated_response + streaming_indicator
                                if len(display_text) > settings.MAX_MESSAGE_LENGTH:
                                    if not message_overflow_handled:
                                        # Remove streaming indicator from current message
                                        try:
                                            await current_message.edit(accumulated_response[:settings.MAX_MESSAGE_LENGTH - 50] + "\n\n_(Continued...)_")
                                        except:
                                            pass
                                        
                                        # Create a new message for continuation
                                        current_message = await event.respond("_(Continuing...)_\n\n" + accumulated_response[settings.MAX_MESSAGE_LENGTH - 50:] + streaming_indicator)
                                        sent_messages.append(current_message)
                                        message_overflow_handled = True
                                    else:
                                        # We're already in overflow mode, just update the latest message
                                        # Find how much of the response fits in previous messages
                                        chars_in_previous = (len(sent_messages) - 1) * (settings.MAX_MESSAGE_LENGTH - 50)
                                        remaining_text = accumulated_response[chars_in_previous:]
                                        
                                        if len(remaining_text + streaming_indicator) > settings.MAX_MESSAGE_LENGTH:
                                            # Need another new message
                                            try:
                                                await current_message.edit(remaining_text[:settings.MAX_MESSAGE_LENGTH - 50] + "\n\n_(Continued...)_")
                                            except:
                                                pass
                                            
                                            current_message = await event.respond("_(Continuing...)_\n\n" + remaining_text[settings.MAX_MESSAGE_LENGTH - 50:] + streaming_indicator)
                                            sent_messages.append(current_message)
                                        else:
                                            # Update current message
                                            await current_message.edit("_(Continuing...)_\n\n" + remaining_text + streaming_indicator)
                                else:
                                    # Normal update - message fits
                                    await current_message.edit(display_text)
                                
                                last_update_time = current_time
                                chunks_since_update = 0  # Reset chunk counter
                            except Exception as e:
                                logger.warning(f"Failed to update message: {e}")
                                # If we hit rate limit, increase the interval
                                if "wait" in str(e).lower():
                                    update_interval = min(update_interval * 1.5, 10.0)  # Max 10 seconds
                                    logger.info(f"Rate limited, increasing update interval to {update_interval}s")
                    
                    # Final update with complete response and footer
                    if accumulated_response:
                        try:
                            # Save the response to database
                            await self.db_manager.add_message(
                                conversation_id=conversation.id,
                                role="assistant",
                                content=accumulated_response
                            )
                            
                            # Handle final message update based on whether we had overflow
                            if len(sent_messages) == 1:
                                # Single message - try to update with footer
                                final_text = accumulated_response + footer
                                if len(final_text) <= settings.MAX_MESSAGE_LENGTH:
                                    await current_message.edit(final_text, parse_mode='markdown')
                                else:
                                    # Delete and resend using message splitter
                                    await current_message.delete()
                                    await self.message_splitter.send_long_message(
                                        event,
                                        final_text,
                                        parse_mode='markdown'
                                    )
                            else:
                                # Multiple messages - update the last one with remaining content and footer
                                chars_in_previous = (len(sent_messages) - 1) * (settings.MAX_MESSAGE_LENGTH - 50)
                                remaining_text = accumulated_response[chars_in_previous:]
                                final_part = "_(Continuing...)_\n\n" + remaining_text + footer
                                
                                if len(final_part) <= settings.MAX_MESSAGE_LENGTH:
                                    await current_message.edit(final_part, parse_mode='markdown')
                                else:
                                    # Even the final part is too long, need to split
                                    await current_message.edit("_(Continuing...)_\n\n" + remaining_text[:settings.MAX_MESSAGE_LENGTH - len(footer) - 50], parse_mode='markdown')
                                    await event.respond(footer, parse_mode='markdown')
                                    
                        except Exception as e:
                            logger.warning(f"Failed to update final message: {e}")
                    
                    return accumulated_response
                else:
                    # Fallback to non-streaming
                    print(f'falling back to non-streaming for {provider}')
                    response = await llm_client.generate_response(
                        messages=messages,
                        model_name=settings_dict["model"],
                        temperature=settings_dict["temperature"],
                        thinking_mode=settings_dict.get("thinking_mode", False),
                        web_search_mode=settings_dict.get("web_search_mode", False)
                    )
                    
                    # Save the response to database
                    await self.db_manager.add_message(
                        conversation_id=conversation.id,
                        role="assistant",
                        content=response
                    )
                    
                    # Update the initial message with the response and footer
                    try:
                        final_text = response + footer
                        if len(final_text) <= settings.MAX_MESSAGE_LENGTH:
                            await initial_message.edit(final_text, parse_mode='markdown')
                        else:
                            # If message is too long, send as new messages
                            await initial_message.delete()
                            await self.message_splitter.send_long_message(
                                event,
                                final_text,
                                parse_mode='markdown'
                            )
                    except Exception as e:
                        logger.warning(f"Failed to update message: {e}")
                    
                    return response
                    
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            logger.error(traceback.format_exc())
            error_msg = "I apologize, but I encountered an error while generating the response."
            
            # Save error to database
            await self.db_manager.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=error_msg
            )
            
            try:
                await initial_message.edit(error_msg + footer)
            except:
                pass
            return error_msg
    
    def register_handlers(self):
        """Register message handlers"""
        # Handle all non-command messages
        self.client.add_event_handler(
            self.handle_message,
            events.NewMessage(func=lambda e: not e.message.message.startswith('/'))
        )
