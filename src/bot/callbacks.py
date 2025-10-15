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

        db_user = await self.db_manager.get_or_create_user(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )

        await self._show_main_settings(event, db_user)

    @require_authorization
    async def handle_settings_callback(self, event):
        """Handle settings callback queries"""
        try:
            user = await event.get_sender()
            db_user = await self.db_manager.get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )

            data = event.data.decode("utf-8")

            if data == "settings:model":
                buttons = [
                    [
                        Button.inline("Gemini", b"provider:gemini"),
                        Button.inline("OpenAI", b"provider:openai"),
                        Button.inline("Anthropic", b"provider:anthropic"),
                    ],
                    [Button.inline("⬅️ Back", b"settings:back")],
                ]
                await event.edit("Choose a provider:", buttons=buttons)

            elif data == "provider:gemini":
                buttons = [
                    [Button.inline("⚡ 2.5 Flash", b"set:model:gemini-flash")],
                    [Button.inline("💎 2.5 Pro", b"set:model:gemini-pro")],
                    [Button.inline("⬅️ Back", b"settings:model")],
                ]
                await event.edit("Choose a Gemini model:", buttons=buttons)

            elif data == "provider:openai":
                buttons = [
                    [Button.inline("🤖 GPT‑5", b"set:model:gpt-5")],
                    [Button.inline("💬 GPT‑5 Chat", b"set:model:gpt-5-chat")],
                    [Button.inline("⬅️ Back", b"settings:model")],
                ]
                await event.edit("Choose an OpenAI model:", buttons=buttons)

            elif data == "provider:anthropic":
                buttons = [
                    [Button.inline("🎭 Sonnet 4.5", b"set:model:claude-sonnet-4-5")],
                    [Button.inline("🏛️ Opus 4.1", b"set:model:claude-opus-4-1")],
                    [Button.inline("⬅️ Back", b"settings:model")],
                ]
                await event.edit("Choose a Claude model (Vertex):", buttons=buttons)

            elif data == "settings:temperature":
                # Compact presets similar to provided screenshots
                buttons = [
                    [Button.inline("Precise", b"set:temp:0.2")],
                    [Button.inline("Balanced", b"set:temp:0.6")],
                    [Button.inline("Creative", b"set:temp:0.85")],
                    [Button.inline("« Back", b"settings:back")],
                ]
                await event.edit("Select a temp preset", buttons=buttons)

            elif data.startswith("set:temp:"):
                # Apply chosen temperature and return
                try:
                    temp = float(data.split(":")[-1])
                except Exception:
                    temp = 0.7
                await self.db_manager.update_user_settings(user_id=db_user.id, temperature=temp)
                await event.answer(f"Temperature set to {temp}")
                await self._show_main_settings(event, db_user)

            elif data == "settings:gemini_search" or data == "settings:search":
                cur = (await self.db_manager.get_user_settings(db_user.id)).get(
                    "web_search_mode", False
                )
                new_val = not cur
                await self.db_manager.update_user_settings(
                    user_id=db_user.id, web_search_mode=new_val
                )
                await event.answer(f"Search is now {'✅ ON' if new_val else '❌ OFF'}")
                await self._show_main_settings(event, db_user)

            elif data == "settings:gemini_thinking" or data == "settings:thinking":
                # Levels mapped to budgets: Disabled=0, Low=2000, Medium=5000, High=8000
                buttons = [
                    [Button.inline("Disabled", b"set:thinklvl:0")],
                    [Button.inline("Low", b"set:thinklvl:2000"), Button.inline("Medium", b"set:thinklvl:5000"), Button.inline("High", b"set:thinklvl:8000")],
                    [Button.inline("« Back", b"settings:back")],
                ]
                await event.edit("Select thinking (reasoning) level:", buttons=buttons)
            elif data.startswith("set:thinklvl:"):
                val = int(data.split(":")[-1])
                await self.db_manager.update_user_settings(user_id=db_user.id, gemini_thinking_tokens=val)
                level = "Disabled" if val == 0 else ("Low" if val <= 2000 else ("Medium" if val <= 5000 else "High"))
                await event.answer(f"Thinking set to {level}")
                await self._show_main_settings(event, db_user)

            elif data == "settings:gpt_effort":
                choices = ["minimal", "low", "medium", "high"]
                buttons = [
                    [
                        Button.inline(c.title(), f"set:gpt_effort:{c}".encode())
                        for c in choices[:2]
                    ],
                    [
                        Button.inline(c.title(), f"set:gpt_effort:{c}".encode())
                        for c in choices[2:]
                    ],
                    [Button.inline("⬅️ Back", b"settings:back")],
                ]
                await event.edit("Select reasoning effort:", buttons=buttons)
            elif data.startswith("set:gpt_effort:"):
                val = data.split(":")[-1]
                await self.db_manager.update_user_settings(
                    user_id=db_user.id, gpt_reasoning_effort=val
                )
                await event.answer(f"Reasoning effort set to {val}")
                await self._show_main_settings(event, db_user)

            elif data == "settings:gpt_verbosity":
                choices = ["low", "medium", "high"]
                buttons = [
                    [
                        Button.inline(c.title(), f"set:gpt_verbosity:{c}".encode())
                        for c in choices
                    ],
                    [Button.inline("⬅️ Back", b"settings:back")],
                ]
                await event.edit("Select verbosity:", buttons=buttons)
            elif data.startswith("set:gpt_verbosity:"):
                val = data.split(":")[-1]
                await self.db_manager.update_user_settings(
                    user_id=db_user.id, gpt_verbosity=val
                )
                await event.answer(f"Verbosity set to {val}")
                await self._show_main_settings(event, db_user)

            elif data == "settings:gpt_searchctx" or data == "settings:searchctx":
                choices = ["low", "medium", "high"]
                buttons = [
                    [
                        Button.inline(c.title(), f"set:gpt_searchctx:{c}".encode())
                        for c in choices
                    ],
                    [Button.inline("« Back", b"settings:back")],
                ]
                await event.edit("Select Search context size:", buttons=buttons)
            elif data.startswith("set:gpt_searchctx:"):
                val = data.split(":")[-1]
                await self.db_manager.update_user_settings(
                    user_id=db_user.id, gpt_search_context_size=val
                )
                await event.answer(f"Search context size set to {val}")
                await self._show_main_settings(event, db_user)

            elif data.startswith("set:model:"):
                key = data.split(":")[-1]
                model_map = settings.AVAILABLE_MODELS
                if key in model_map:
                    await self.db_manager.update_user_settings(
                        user_id=db_user.id, model=model_map[key]
                    )
                    await event.answer("Model changed.")
                await self._show_main_settings(event, db_user)

            elif data == "settings:thoughts":
                # Placeholder – per request, button exists but does nothing
                await event.answer("Thoughts: not implemented yet 🧩")
            elif data == "settings:close":
                # Delete the settings message if possible
                try:
                    await event.delete()
                except Exception:
                    pass

            elif data == "settings:back":
                await self._show_main_settings(event, db_user)

        except Exception as e:
            logger.error(f"Error in settings callback: {str(e)}")
            logger.error(traceback.format_exc())
            await event.answer("An error occurred. Please try again.")

    async def _show_main_settings(self, event, db_user):
        """Show main settings menu"""
        user_settings = await self.db_manager.get_user_settings(db_user.id)
        temp = user_settings["temperature"]
        if temp <= 0.3:
            temp_desc = "focused"
        elif temp <= 0.6:
            temp_desc = "balanced"
        elif temp <= 0.8:
            temp_desc = "creative"
        else:
            temp_desc = "very creative"

        current_model = user_settings["model"]
        provider = "gemini"
        if "claude" in current_model:
            provider = "anthropic"
            if "claude-sonnet-4-5" in current_model:
                model_display = "Claude Sonnet 4.5"
            elif "claude-opus-4-1" in current_model:
                model_display = "Claude Opus 4.1"
            else:
                model_display = "Claude"
        elif "gpt-5" in current_model:
            provider = "openai"
            model_display = "GPT‑5 Chat" if "chat" in current_model else "GPT‑5"
        else:
            provider = "gemini"
            model_display = (
                "Gemini 2.5 Flash" if "flash" in current_model else "Gemini 2.5 Pro"
            )

        search_status = "✅ ON" if user_settings.get("web_search_mode", False) else "❌ OFF"

        # Determine friendly labels
        think_tokens = int(user_settings.get("gemini_thinking_tokens", 0))
        think_label = (
            "Disabled" if think_tokens == 0 else (
                "Low" if think_tokens <= 2000 else (
                    "Medium" if think_tokens <= 5000 else "High"
                )
            )
        )
        search_ctx = user_settings.get("gpt_search_context_size", "medium")

        settings_text = f"⚙️ **Current Settings**\n\n**Model**: {model_display}\n"
        settings_text += f"**Temperature**: {user_settings['temperature']} ({temp_desc})\n"
        if provider == "gemini":
            settings_text += f"**Thinking**: {think_label.lower()}\n"
        settings_text += f"**Search**: {search_status}\n"
        settings_text += f"**Search context**: {search_ctx}\n\nSelect what you'd like to change:"

        # Two-column layout resembling the screenshots
        buttons = []
        buttons.append([Button.inline("🤖 Change Model", b"settings:model")])
        buttons.append([
            Button.inline(f"🧠 Thinking: {think_label.lower()}", b"settings:thinking"),
            Button.inline(f"🌡️ Temp: {temp_desc}", b"settings:temperature"),
        ])
        buttons.append([
            Button.inline(f"🧭 Search context: {search_ctx}", b"settings:searchctx"),
            Button.inline(f"🔎 Search {search_status}", b"settings:search"),
        ])
        buttons.append([
            Button.inline("💭 Thoughts", b"settings:thoughts"),
            Button.inline("❌ Close", b"settings:close"),
        ])

        # If this came from /settings, we reply; if callback, we edit
        if isinstance(event, events.NewMessage.Event):
            await event.reply(settings_text, buttons=buttons, parse_mode="markdown")
        else:
            await event.edit(settings_text, buttons=buttons, parse_mode="markdown")

    def register_handlers(self):
        """Register callback handlers"""
        self.client.add_event_handler(
            self.handle_settings, events.NewMessage(pattern="/settings")
        )
        self.client.add_event_handler(
            self.handle_settings_callback,
            events.CallbackQuery(pattern=b"settings:.*|set:.*|provider:.*"),
        )
