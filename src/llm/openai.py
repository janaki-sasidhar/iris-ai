"""OpenAI GPT‑5 client using the Responses API"""

import logging
from typing import List, Dict, Any, AsyncGenerator, Optional

from openai import OpenAI

from .base import BaseLLMClient
from ..config.settings import settings

logger = logging.getLogger(__name__)


class OpenAIClient(BaseLLMClient):
    """OpenAI client targeting GPT‑5 family via Responses API"""

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not configured")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.models = {
            "gpt-5": "gpt-5",
            "gpt-5-chat": "gpt-5-chat-latest",
        }

    def _flatten_messages_to_input(self, messages: List[Dict[str, Any]]) -> str:
        """Flatten role-tagged messages to a single textual prompt for Responses.input.
        We omit image payloads for now."""
        lines = []
        for msg in messages:
            role = msg.get("role", "user")
            text = msg.get("content") or ""
            # If images are present, note them in text for context
            if msg.get("image_data"):
                text = (text + "\n[User attached an image]").strip()
            prefix = "User" if role == "user" else "Assistant"
            lines.append(f"{prefix}: {text}")
        return "\n".join(lines)

    def _supports_reasoning(self, model_name: str) -> bool:
        """Return True if the model supports the Responses `reasoning` param.
        Keep this conservative to avoid 400s on non-reasoning models."""
        # Explicit allowlist based on our configured models
        return model_name in {"gpt-5"}

    def _supports_web_search(self, model_name: str) -> bool:
        """Return True if model supports the built-in web_search tool.
        GPT‑5 Chat has partial feature parity and may not support hosted tools."""
        if model_name == "gpt-5":
            return True
        # include popular 4o/4.1 series if added later
        return model_name.startswith("gpt-4o") or model_name.startswith("gpt-4.1")

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        model_name: str,
        max_tokens: int = None,
        temperature: float = 0.7,  # Ignored for GPT‑5
        thinking_mode: bool = False,  # Deprecated; use reasoning_effort
        web_search_mode: bool = False,  # Not used here
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        try:
            input_text = self._flatten_messages_to_input(messages)

            # Defaults per your guidance
            effort = (options or {}).get("reasoning_effort", "medium")
            verbosity = (options or {}).get("verbosity", "medium")
            search_ctx = (options or {}).get("search_context_size", "medium")

            kwargs: Dict[str, Any] = {
                "model": model_name,
                "input": input_text,
                "text": {"verbosity": verbosity},
            }
            if self._supports_reasoning(model_name):
                kwargs["reasoning"] = {"effort": effort}
            # Set web_search_options only if enabled at the handler level
            if (options or {}).get("web_search_enabled") and self._supports_web_search(model_name):
                kwargs["tools"] = [{"type": "web_search"}]
                kwargs["web_search_options"] = {"search_context_size": search_ctx}
            if max_tokens is not None:
                kwargs["max_output_tokens"] = max_tokens

            logger.info(f"OpenAI Responses request: model={model_name}, effort={effort}, verbosity={verbosity}, search_context_size={search_ctx}")
            resp = await self.client.responses.with_options(timeout=120).create_async(**kwargs)

            if hasattr(resp, "output_text") and resp.output_text:
                return resp.output_text
            # Fallback: stitch text from outputs
            try:
                parts = []
                for item in getattr(resp, "output", []) or []:
                    if getattr(item, "type", "") == "output_text" and getattr(item, "text", ""):
                        parts.append(item.text)
                return "".join(parts) if parts else "I couldn't generate a response."
            except Exception:
                return "I couldn't generate a response."
        except Exception as e:
            logger.exception("OpenAI error")
            return "I apologize, but I encountered an error processing your request."

    async def generate_response_stream(
        self,
        messages: List[Dict[str, Any]],
        model_name: str,
        max_tokens: int = None,
        temperature: float = 0.7,  # Ignored
        thinking_mode: bool = False,
        web_search_mode: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        try:
            input_text = self._flatten_messages_to_input(messages)
            effort = (options or {}).get("reasoning_effort", "medium")
            verbosity = (options or {}).get("verbosity", "medium")
            search_ctx = (options or {}).get("search_context_size", "medium")

            kwargs: Dict[str, Any] = {
                "model": model_name,
                "input": input_text,
                "text": {"verbosity": verbosity},
            }
            if self._supports_reasoning(model_name):
                kwargs["reasoning"] = {"effort": effort}
            if (options or {}).get("web_search_enabled") and self._supports_web_search(model_name):
                kwargs["tools"] = [{"type": "web_search"}]
                kwargs["web_search_options"] = {"search_context_size": search_ctx}
            if max_tokens is not None:
                kwargs["max_output_tokens"] = max_tokens

            with self.client.responses.stream(**kwargs) as stream:
                for event in stream:
                    etype = getattr(event, "type", None)
                    if etype == "response.output_text.delta":
                        yield getattr(event, "delta", "") or ""
                    elif etype == "response.error":
                        yield "I apologize, but I encountered an error while generating the response."
                        break
                # Ensure completion
                stream.close()
        except Exception:
            logger.exception("OpenAI streaming error")
            yield "I apologize, but I encountered an error while generating the response."

    def get_available_models(self) -> Dict[str, str]:
        return self.models.copy()

    def supports_thinking_mode(self) -> bool:
        # Thinking is controlled via reasoning.effort; always available
        return True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # OpenAI client has no async close requirement
        pass
