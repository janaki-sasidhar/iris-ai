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
                buttons = [
                    [Button.inline("0.1 (Very Focused)", b"set:temp:0.1")],
                    [Button.inline("0.3 (Focused)", b"set:temp:0.3")],
                    [Button.inline("0.5 (Balanced)", b"set:temp:0.5")],
                    [Button.inline("0.7 (Creative)", b"set:temp:0.7")],
                    [Button.inline("0.9 (Very Creative)", b"set:temp:0.9")],
                    [Button.inline("⬅️ Back", b"settings:back")],
                ]
                await event.edit("Select temperature:", buttons=buttons)

            elif data == "settings:gemini_search":
                cur = (await self.db_manager.get_user_settings(db_user.id)).get(
                    "web_search_mode", False
                )
                new_val = not cur
                await self.db_manager.update_user_settings(
                    user_id=db_user.id, web_search_mode=new_val
                )
                await event.answer(f"Gemini Search is now {'✅ ON' if new_val else '❌ OFF'}")
                await self._show_main_settings(event, db_user)

            elif data == "settings:gemini_thinking":
                options = [256, 1024, 2048, 4096, 8192]
                buttons = [
                    [
                        Button.inline(str(v), f"set:gemthink:{v}".encode())
                        for v in options[:3]
                    ],
                    [
                        Button.inline(str(v), f"set:gemthink:{v}".encode())
                        for v in options[3:]
                    ],
                    [Button.inline("⬅️ Back", b"settings:back")],
                ]
                await event.edit("Select thinking token budget:", buttons=buttons)
            elif data.startswith("set:gemthink:"):
                val = int(data.split(":")[-1])
                await self.db_manager.update_user_settings(
                    user_id=db_user.id, gemini_thinking_tokens=val
                )
                await event.answer(f"Thinking tokens set to {val}")
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

            elif data == "settings:gpt_searchctx":
                choices = ["low", "medium", "high"]
                buttons = [
                    [
                        Button.inline(c.title(), f"set:gpt_searchctx:{c}".encode())
                        for c in choices
                    ],
                    [Button.inline("⬅️ Back", b"settings:back")],
                ]
                await event.edit("Select search context size:", buttons=buttons)
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

        gemini_search_status = (
            "✅ ON" if user_settings.get("web_search_mode", False) else "❌ OFF"
        )

        settings_text = f"⚙️ **Current Settings**\n\n**Model**: {model_display}\n"
        if provider != "openai":
            settings_text += f"**Temperature**: {user_settings['temperature']} ({temp_desc})\n"
        if provider == "gemini":
            settings_text += (
                f"**Thinking Tokens**: {user_settings.get('gemini_thinking_tokens', 2048)}\n"
            )
        elif provider == "openai":
            settings_text += (
                f"**Reasoning Effort**: {user_settings.get('gpt_reasoning_effort','medium')}\n"
                f"**Verbosity**: {user_settings.get('gpt_verbosity','medium')}\n"
                f"**Search Context Size**: {user_settings.get('gpt_search_context_size','medium')}\n"
            )
        if "gemini" in current_model:
            settings_text += f"**Gemini Search**: {gemini_search_status}\n"

        settings_text += "\nSelect what you'd like to change:"

        buttons = [[Button.inline("🤖 Change Model", b"settings:model")]]
        if provider != "openai":
            buttons.append([Button.inline("🌡️ Temperature", b"settings:temperature")])
        if provider == "gemini":
            buttons.append([Button.inline("🧠 Thinking Tokens", b"settings:gemini_thinking")])
            buttons.append([Button.inline("🔍 Gemini Search", b"settings:gemini_search")])
        elif provider == "openai":
            buttons.append([Button.inline("🧠 Reasoning Effort", b"settings:gpt_effort")])
            buttons.append([Button.inline("📝 Verbosity", b"settings:gpt_verbosity")])
            buttons.append([Button.inline("🔎 Search Ctx Size", b"settings:gpt_searchctx")])

        buttons.append([Button.inline("❌ Close", b"settings:close")])

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

