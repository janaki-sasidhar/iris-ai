"""Anthropic Claude client via Vertex AI (google-genai)"""

import logging
from typing import List, Dict, Any, AsyncGenerator, Optional

from google import genai
from google.genai import types

from .base import BaseLLMClient
from ..config.settings import settings

logger = logging.getLogger(__name__)


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude on Vertex using google-genai unified interface"""

    def __init__(self):
        self.client = genai.Client(
            vertexai=True,
            project=settings.GCP_PROJECT,
            location=settings.GCP_LOCATION,
        )
        self.models = {
            "claude-sonnet-4-5": "claude-sonnet-4-5@20250929",
            "claude-opus-4-1": "claude-opus-4-1@20250805",
        }

    def _prepare_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        formatted = []
        for msg in messages:
            parts = []
            if msg.get("content"):
                parts.append({"text": msg["content"]})
            if msg.get("image_data"):
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": msg["image_data"],
                    }
                })
            if not parts:
                continue
            role = "user" if msg["role"] == "user" else "model"
            formatted.append({"role": role, "parts": parts})
        return formatted

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        model_name: str,
        max_tokens: int = None,
        temperature: float = 0.7,
        thinking_mode: bool = False,  # not used explicitly
        web_search_mode: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> str:
        try:
            fm = self._prepare_messages(messages)
            cfg = {"temperature": temperature}
            if max_tokens is not None:
                cfg["max_output_tokens"] = max_tokens
            config = types.GenerateContentConfig(**cfg)
            resp = await self.client.aio.models.generate_content(
                model=model_name, contents=fm, config=config
            )
            if resp.candidates and resp.candidates[0].content.parts:
                texts = [p.text for p in resp.candidates[0].content.parts if getattr(p, "text", None)]
                return " ".join(texts) if texts else "I couldn't generate a response."
            return "I couldn't generate a response."
        except Exception:
            logger.exception("Claude(Vertex) error")
            return "I apologize, but I encountered an error processing your request."

    async def generate_response_stream(
        self,
        messages: List[Dict[str, Any]],
        model_name: str,
        max_tokens: int = None,
        temperature: float = 0.7,
        thinking_mode: bool = False,
        web_search_mode: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        try:
            fm = self._prepare_messages(messages)
            cfg = {"temperature": temperature}
            if max_tokens is not None:
                cfg["max_output_tokens"] = max_tokens
            config = types.GenerateContentConfig(**cfg)
            it = await self.client.aio.models.generate_content_stream(
                model=model_name, contents=fm, config=config
            )
            async for chunk in it:
                if hasattr(chunk, "candidates") and chunk.candidates:
                    for cand in chunk.candidates:
                        if hasattr(cand, "content") and hasattr(cand.content, "parts"):
                            for part in cand.content.parts:
                                if getattr(part, "text", None):
                                    yield part.text
                elif hasattr(chunk, "text") and chunk.text:
                    yield chunk.text
        except Exception:
            logger.exception("Claude(Vertex) streaming error")
            yield "I apologize, but I encountered an error while generating the response."

    def get_available_models(self) -> Dict[str, str]:
        return self.models.copy()

    def supports_thinking_mode(self) -> bool:
        return True

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

