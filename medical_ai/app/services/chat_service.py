# chat_service.py
from __future__ import annotations

import logging
import os
from typing import Literal

from openai import AsyncOpenAI
from pydantic import BaseModel
from services.graph_store import MediBotGraph

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

SupportedLanguage = Literal["en", "bn", "ar", "hi", "ur"]

_LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "bn": "Bengali (Bangla)",
    "ar": "Arabic",
    "hi": "Hindi",
    "ur": "Urdu",
}


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    patient_data: dict | None = None
    language: SupportedLanguage = "en"


class ChatResponse(BaseModel):
    reply: str
    model: str
    input_tokens: int
    output_tokens: int


class ChatService:

    DEFAULT_MODEL       = "gpt-4o-mini"
    DEFAULT_MAX_TOKENS  = 1024
    DEFAULT_TEMPERATURE = 0.5

    def __init__(
        self,
        api_key:     str | None = None,
        model:       str        = DEFAULT_MODEL,
        max_tokens:  int        = DEFAULT_MAX_TOKENS,
        temperature: float      = DEFAULT_TEMPERATURE,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self._graph  = MediBotGraph()
        self.model        = model
        self.max_tokens   = max_tokens
        self.temperature  = temperature

    async def chat(self, req: ChatRequest) -> ChatResponse:
        # Rebuild graph from this request's report data
        if req.patient_data:
            self._graph.build_from_report(req.patient_data)

        # Extract latest user query for graph traversal + enrichment
        latest_query = ""
        if req.messages:
            user_msgs = [m.content for m in req.messages if m.role == "user"]
            if user_msgs:
                latest_query = user_msgs[-1]

        # retrieve_context is now async (handles web enrichment internally)
        graph_context = await self._graph.retrieve_context(latest_query)

        system_prompt   = self._build_system_prompt(req.language, graph_context, bool(req.patient_data))
        openai_messages = self._build_messages(system_prompt, req.messages)

        logger.info(
            "ChatService.chat | model=%s lang=%s msgs=%d has_data=%s",
            self.model, req.language, len(req.messages), bool(req.patient_data),
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

        logger.info("ChatService.chat | tokens in=%d out=%d", input_tokens, output_tokens)

        return ChatResponse(
            reply         = reply,
            model         = completion.model,
            input_tokens  = input_tokens,
            output_tokens = output_tokens,
        )

    def _build_system_prompt(
        self,
        language: str,
        graph_context: str,
        has_patient_data: bool,
    ) -> str:
        lang_name = _LANGUAGE_NAMES.get(language, "English")

        base = (
            f"You are MediBot, a friendly medical report explainer for Bangladeshi patients. "
            f"Always respond in {lang_name}. "
            "Explain medical terms in plain, everyday language. "
            "Be empathetic and clear. "
            "Always remind the user to consult a licensed doctor for medical decisions. "
            "Keep responses concise — 2 to 4 sentences unless more detail is clearly needed. "
            "When multiple patients are present, always state which patient you are referring to. "
            "When MedlinePlus data is provided in the context, use it to give accurate explanations "
            "and mention it is from NIH MedlinePlus so the patient knows the source is trustworthy."
        )

        if not has_patient_data:
            return base

        context = (
            "\n\nRelevant patient data retrieved from knowledge graph"
            " (may include NIH MedlinePlus definitions for abnormal tests):\n"
            f"{graph_context}\n\n"
            "Answer based on the above data. "
            "Do not invent values not present in the report. "
            "If MedlinePlus knowledge is included, incorporate it naturally into your explanation."
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