"""Callback handlers for inline buttons"""

import logging
import traceback
from telethon import events, Button
from .decorators import require_authorization
from ..database import DatabaseManager
from ..config.settings import settings

logger = logging.getLogger(__name__)


class CallbackHandler:
    """Handles callback queries from inline buttons"""
    
    def __init__(self, client, db_manager: DatabaseManager):
        self.client = client
        self.db_manager = db_manager
    
    @require_authorization
    async def handle_settings(self, event):
        """Handle /settings command"""
        user = await event.get_sender()
        
        # Get user from database
        db_user = await self.db_manager.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Get current settings
        user_settings = await self.db_manager.get_user_settings(db_user.id)
        
        # Format temperature display
        temp = user_settings["temperature"]
        if temp <= 0.3:
            temp_desc = "focused"
        elif temp <= 0.6:
            temp_desc = "balanced"
        elif temp <= 0.8:
            temp_desc = "creative"
        else:
            temp_desc = "very creative"
        
        # Create settings message with proper model display
        current_model = user_settings["model"]
        
        # Determine model display name
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
            model_display = "Gemini 2.5 Flash" if "flash" in current_model else "Gemini 2.5 Pro"
        
        thinking_status = "✅ ON" if user_settings.get("thinking_mode", False) else "❌ OFF"
        
        settings_text = (
            f"⚙️ **Current Settings**\n\n"
            f"**Model**: {model_display}\n"
            f"**Temperature**: {user_settings['temperature']} ({temp_desc})\n"
            f"**Thinking Mode**: {thinking_status}\n\n"
            f"Select what you'd like to change:"
        )
        
        # Create inline buttons
        buttons = [
            [Button.inline("🤖 Change Model", b"settings:model")],
            [Button.inline("🌡️ Temperature", b"settings:temperature")],
            [Button.inline("🧠 Thinking Mode", b"settings:thinking")],
            [Button.inline("❌ Close", b"settings:close")]
        ]
        
        await event.reply(settings_text, buttons=buttons, parse_mode='markdown')
    
    @require_authorization
    async def handle_settings_callback(self, event):
        """Handle settings callback queries"""
        try:
            user = await event.get_sender()
            
            # Get user from database
            db_user = await self.db_manager.get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            data = event.data.decode('utf-8')
            
            if data == "settings:close":
                await event.delete()
                return
            
            elif data == "settings:model":
                # Show provider selection first
                buttons = [
                    [
                        Button.inline("OpenAI", b"provider:openai"),
                        Button.inline("Anthropic", b"provider:anthropic"),
                        Button.inline("Google", b"provider:google")
                    ],
                    [Button.inline("« Back", b"settings:back")]
                ]
                await event.edit("Select the LLM model provider", buttons=buttons)
            
            elif data == "provider:openai":
                buttons = [
                    [Button.inline("🧠 O4 Mini (Reasoning)", b"set:model:o4-mini")],
                    [Button.inline("🤖 GPT-4.1", b"set:model:gpt-4.1")],
                    [Button.inline("🤖 GPT-4o", b"set:model:gpt-4o")],
                    [Button.inline("« Back", b"settings:model")]
                ]
                await event.edit("Select OpenAI Model:", buttons=buttons)
            
            elif data == "provider:anthropic":
                buttons = [
                    [Button.inline("🎭 Claude Sonnet 4", b"set:model:claude-sonnet-4")],
                    [Button.inline("🎨 Claude 3.7 Sonnet", b"set:model:claude-3.7-sonnet")],
                    [Button.inline("🚀 Claude 3.5 Sonnet", b"set:model:claude-3.5-sonnet")],
                    [Button.inline("« Back", b"settings:model")]
                ]
                await event.edit("Select Anthropic Model:", buttons=buttons)
            
            elif data == "provider:google":
                buttons = [
                    [Button.inline("⚡ Gemini 2.5 Flash", b"set:model:flash")],
                    [Button.inline("💎 Gemini 2.5 Pro", b"set:model:pro")],
                    [Button.inline("« Back", b"settings:model")]
                ]
                await event.edit("Select Google Model:", buttons=buttons)
            
            
            elif data == "settings:temperature":
                buttons = [
                    [Button.inline("0.1 (Very Focused)", b"set:temp:0.1")],
                    [Button.inline("0.3 (Focused)", b"set:temp:0.3")],
                    [Button.inline("0.5 (Balanced)", b"set:temp:0.5")],
                    [Button.inline("0.7 (Creative - default)", b"set:temp:0.7")],
                    [Button.inline("0.9 (Very Creative)", b"set:temp:0.9")],
                    [Button.inline("🔙 Back", b"settings:back")]
                ]
                await event.edit("Select Temperature:", buttons=buttons)
            
            elif data == "settings:thinking":
                current_thinking = (await self.db_manager.get_user_settings(db_user.id)).get("thinking_mode", False)
                new_thinking = not current_thinking
                
                await self.db_manager.update_user_settings(
                    user_id=db_user.id,
                    thinking_mode=new_thinking
                )
                
                status = "✅ ON" if new_thinking else "❌ OFF"
                await event.answer(f"Thinking mode is now {status}")
                
                # Return to main settings
                await self._show_main_settings(event, db_user)
            
            elif data.startswith("set:model:"):
                model_choice = data.split(":")[-1]
                model_map = settings.AVAILABLE_MODELS
                
                if model_choice in model_map:
                    await self.db_manager.update_user_settings(
                        user_id=db_user.id,
                        model=model_map[model_choice]
                    )
                    
                    # Create appropriate model display name
                    if model_choice.startswith("claude"):
                        if model_choice == "claude-sonnet-4":
                            display_name = "Claude Sonnet 4"
                        elif model_choice == "claude-3.7-sonnet":
                            display_name = "Claude 3.7 Sonnet"
                        elif model_choice == "claude-3.5-sonnet":
                            display_name = "Claude 3.5 Sonnet"
                        else:
                            display_name = model_choice.replace("-", " ").title()
                    elif model_choice.startswith("gpt") or model_choice.startswith("o4"):
                        if model_choice == "o4-mini":
                            display_name = "O4 Mini (Reasoning)"
                        elif model_choice == "gpt-4.1":
                            display_name = "GPT-4.1"
                        elif model_choice == "gpt-4o":
                            display_name = "GPT-4o"
                        else:
                            display_name = model_choice.upper()
                    else:
                        display_name = f"Gemini 2.5 {model_choice.title()}"
                    
                    await event.answer(f"Model changed to {display_name}")
            
                # Return to main settings
                await self._show_main_settings(event, db_user)
            
            
            elif data.startswith("set:temp:"):
                temp = float(data.split(":")[-1])
                await self.db_manager.update_user_settings(
                    user_id=db_user.id,
                    temperature=temp
                )
                await event.answer(f"Temperature set to {temp}")
                
                # Return to main settings
                await self._show_main_settings(event, db_user)
            
            elif data == "settings:back":
                await self._show_main_settings(event, db_user)
                
        except Exception as e:
            logger.error(f"Error in settings callback: {str(e)}")
            logger.error(traceback.format_exc())
            await event.answer("An error occurred. Please try again.")
    
    async def _show_main_settings(self, event, db_user):
        """Show main settings menu"""
        # Get current settings
        user_settings = await self.db_manager.get_user_settings(db_user.id)
        
        # Format temperature display
        temp = user_settings["temperature"]
        if temp <= 0.3:
            temp_desc = "focused"
        elif temp <= 0.6:
            temp_desc = "balanced"
        elif temp <= 0.8:
            temp_desc = "creative"
        else:
            temp_desc = "very creative"
        
        # Create settings message with proper model display
        current_model = user_settings["model"]
        
        # Determine model display name
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
            model_display = "Gemini 2.5 Flash" if "flash" in current_model else "Gemini 2.5 Pro"
        
        thinking_status = "✅ ON" if user_settings.get("thinking_mode", False) else "❌ OFF"
        
        settings_text = (
            f"⚙️ **Current Settings**\n\n"
            f"**Model**: {model_display}\n"
            f"**Temperature**: {user_settings['temperature']} ({temp_desc})\n"
            f"**Thinking Mode**: {thinking_status}\n\n"
            f"Select what you'd like to change:"
        )
        
        # Create inline buttons
        buttons = [
            [Button.inline("🤖 Change Model", b"settings:model")],
            [Button.inline("🌡️ Temperature", b"settings:temperature")],
            [Button.inline("🧠 Thinking Mode", b"settings:thinking")],
            [Button.inline("❌ Close", b"settings:close")]
        ]
        
        await event.edit(settings_text, buttons=buttons, parse_mode='markdown')
    
    def register_handlers(self):
        """Register callback handlers"""
        self.client.add_event_handler(
            self.handle_settings,
            events.NewMessage(pattern='/settings')
        )
        
        self.client.add_event_handler(
            self.handle_settings_callback,
            events.CallbackQuery(pattern=b"settings:.*|set:.*|provider:.*")
        )