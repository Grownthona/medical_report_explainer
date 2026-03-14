from __future__ import annotations

import json
import logging
import os
from typing import Literal

from openai import AsyncOpenAI
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

SupportedLanguage = Literal["en", "bn", "ar", "hi", "ur"]

# ── Language display names (used in system prompt) ────────────────────────────
_LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "bn": "Bengali (Bangla)",
    "ar": "Arabic",
    "hi": "Hindi",
    "ur": "Urdu",
}


# ══════════════════════════════════════════════════════════════════════════════
# Pydantic schemas
# ══════════════════════════════════════════════════════════════════════════════

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    patient_data: dict | None = None   # full parsed report JSON from the frontend
    language: SupportedLanguage = "en"


class ChatResponse(BaseModel):
    reply: str
    model: str
    input_tokens: int
    output_tokens: int


# ══════════════════════════════════════════════════════════════════════════════
# Service
# ══════════════════════════════════════════════════════════════════════════════

class ChatService:
    """
    Stateless service that wraps OpenAI chat completions for MediBot.

    Usage:
        service = ChatService()                        # reads OPENAI_API_KEY
        service = ChatService(api_key="sk-...")        # explicit key

    Main entry point:
        response: ChatResponse = await service.chat(req)
    """

    DEFAULT_MODEL       = "gpt-4o-mini"
    DEFAULT_MAX_TOKENS  = 512
    DEFAULT_TEMPERATURE = 0.5

    def __init__(
        self,
        api_key:     str | None = None,
        model:       str        = DEFAULT_MODEL,
        max_tokens:  int        = DEFAULT_MAX_TOKENS,
        temperature: float      = DEFAULT_TEMPERATURE,
    ) -> None:
        self._client      = AsyncOpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.model        = model
        self.max_tokens   = max_tokens
        self.temperature  = temperature

    # ── Public API ────────────────────────────────────────────────────────────

    async def chat(self, req: ChatRequest) -> ChatResponse:
        """
        Build the prompt, call OpenAI, and return a structured ChatResponse.

        Raises:
            RuntimeError: if the OpenAI call fails.
        """
        system_prompt    = self._build_system_prompt(req.patient_data, req.language)
        openai_messages  = self._build_messages(system_prompt, req.messages)

        logger.info(
            "ChatService.chat | model=%s lang=%s msgs=%d has_patient_data=%s",
            self.model, req.language, len(req.messages), req.patient_data is not None,
        )

        try:
            completion = await self._client.chat.completions.create(
                model       = self.model,
                max_tokens  = self.max_tokens,
                temperature = self.temperature,
                messages    = openai_messages,
            )
        except Exception as exc:
            logger.error("OpenAI request failed: %s", exc)
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc

        reply         = completion.choices[0].message.content or ""
        input_tokens  = completion.usage.prompt_tokens     if completion.usage else 0
        output_tokens = completion.usage.completion_tokens if completion.usage else 0

        logger.info(
            "ChatService.chat | tokens in=%d out=%d",
            input_tokens, output_tokens,
        )

        return ChatResponse(
            reply         = reply,
            model         = completion.model,
            input_tokens  = input_tokens,
            output_tokens = output_tokens,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_system_prompt(
        self,
        patient_data: dict | None,
        language: str,
    ) -> str:
        lang_name = _LANGUAGE_NAMES.get(language, "English")

        base = (
            f"You are MediBot, a friendly medical report explainer for Bangladeshi patients. "
            f"Always respond in {lang_name}. "
            "Explain medical terms in plain, everyday language. "
            "Be empathetic and clear. "
            "Always remind the user to consult a licensed doctor for medical decisions. "
            "Keep responses concise — 2 to 4 sentences unless more detail is clearly needed."
        )

        if not patient_data:
            return base

        context = (
            f"\n\nThe patient's parsed report data is provided below as JSON. "
            f"Use it to give accurate, personalised answers.\n"
            f"```json\n{json.dumps(patient_data, indent=2, ensure_ascii=False)}\n```"
        )

        return base + context

    @staticmethod
    def _build_messages(
        system_prompt: str,
        history: list[ChatMessage],
    ) -> list[dict]:
        messages: list[dict] = [{"role": "system", "content": system_prompt}]
        messages += [{"role": m.role, "content": m.content} for m in history]
        return messages