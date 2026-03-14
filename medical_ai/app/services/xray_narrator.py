"""
xray_narrator.py
─────────────────
Turns raw X-ray model probability predictions into patient-friendly language
using OpenAI Chat Completions API.

Input:
    predictions: [{ "label": "Cardiomegaly", "probability": 0.87 }, ...]

Output:
    {
        "findings":         str,   # clinical-style summary
        "voice_explanation":str,   # spoken plain-language paragraph
        "advice":           str,   # safe next-step advice
    }
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

# ── OpenAI config ─────────────────────────────────────────────────────────────
_OPENAI_MODEL   = os.getenv("OPENAI_MODEL",   "gpt-4o-mini")
_OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))

_client = OpenAI(
    api_key = os.getenv("OPENAI_API_KEY", ""),
    timeout = _OPENAI_TIMEOUT,
)

# Threshold above which a finding is considered "significant"
_SIGNIFICANT_THRESHOLD = float(os.getenv("XRAY_THRESHOLD", "0.5"))

# ── Language label map ────────────────────────────────────────────────────────
_LANG_INSTRUCTIONS: dict[str, str] = {
    "en": "Respond in English.",
    "bn": "Respond in Bengali (বাংলা).",
    "ar": "Respond in Arabic (العربية).",
    "hi": "Respond in Hindi (हिन्दी).",
    "ur": "Respond in Urdu (اردو).",
}


# ══════════════════════════════════════════════════════════════════════════════
# PROMPT BUILDER
# ══════════════════════════════════════════════════════════════════════════════

def _build_messages(predictions: list[dict], language: str) -> list[dict]:
    """Build OpenAI messages list for the chat completion."""
    lang_instruction = _LANG_INSTRUCTIONS.get(language, _LANG_INSTRUCTIONS["en"])

    system_prompt = f"""You are a cautious and educational medical AI specializing in chest X-ray report narration.
{lang_instruction}

You will receive a list of X-ray findings with probability scores from an AI classification model.
Your job is to turn these into a clear, patient-friendly explanation.

Return ONLY a valid JSON object with this exact structure:
{{
  "findings":          "Clinical-style summary of what the X-ray analysis detected. Mention significant findings by name with their likelihood. Keep it factual and neutral.",
  "voice_explanation": "Spoken-style paragraph for reading aloud to the patient. 3-5 sentences. Use simple everyday language. Name significant findings naturally. End with a calm reassuring next step. Do NOT say 'your report shows' — speak directly.",
  "advice":            "Safe general advice. Always recommend consulting a doctor for any significant findings. Do NOT diagnose or prescribe."
}}

STRICT RULES:
- Do NOT diagnose diseases.
- Do NOT prescribe any medication or treatment.
- Mention only findings with probability above {_SIGNIFICANT_THRESHOLD:.0%}.
- If ALL findings are below the threshold, say the X-ray appears normal but recommend doctor review.
- Keep the tone calm, clear and reassuring.
- Return VALID JSON only. No markdown. No text outside JSON."""

    rows = "\n".join(
        f"  {p['label']}: {p['probability']:.1%}"
        for p in sorted(predictions, key=lambda x: x["probability"], reverse=True)
    )
    user_message = f"X-ray AI model predictions:\n{rows}"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_message},
    ]


# ══════════════════════════════════════════════════════════════════════════════
# LLM CALL
# ══════════════════════════════════════════════════════════════════════════════

def _call_openai(messages: list[dict]) -> Optional[str]:
    """Call OpenAI Chat Completions and return raw response text."""
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not set")
        return None
    try:
        response = _client.chat.completions.create(
            model       = _OPENAI_MODEL,
            messages    = messages,
            temperature = 0.2,
            response_format = {"type": "json_object"},  # enforces JSON output
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error("OpenAI xray narration failed: %s", e)
        return None


# ══════════════════════════════════════════════════════════════════════════════
# RESPONSE PARSER
# ══════════════════════════════════════════════════════════════════════════════

def _parse_narration(raw: Optional[str]) -> Optional[dict]:
    """Parse and validate the LLM JSON response."""
    if not raw:
        return None

    import re
    cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip())

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r'\{[\s\S]+\}', cleaned)
        if not m:
            return None
        try:
            parsed = json.loads(m.group())
        except json.JSONDecodeError:
            return None

    return {
        "findings":          str(parsed.get("findings",          "")).strip(),
        "voice_explanation": str(parsed.get("voice_explanation", "")).strip(),
        "advice":            str(parsed.get("advice",            "")).strip(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def narrate_xray(predictions: list[dict], language: str = "en") -> dict:
    """
    Convert X-ray model predictions into patient-friendly text via OpenAI.

    Args:
        predictions: list of { "label": str, "probability": float (0–1) }
        language:    "en" | "bn" | "ar" | "hi" | "ur"

    Returns:
        { "findings": str, "voice_explanation": str, "advice": str }
        Falls back to rule-based summary if OpenAI is unavailable.
    """
    if not predictions:
        return _fallback_narration(predictions, language)

    messages = _build_messages(predictions, language)
    raw      = _call_openai(messages)
    result   = _parse_narration(raw)

    if result:
        return result

    logger.warning("OpenAI narration failed — using rule-based fallback")
    return _fallback_narration(predictions, language)


# ══════════════════════════════════════════════════════════════════════════════
# FALLBACK
# ══════════════════════════════════════════════════════════════════════════════

def _fallback_narration(predictions: list[dict], language: str) -> dict:
    """Rule-based fallback when OpenAI is unavailable."""
    significant = [
        p for p in predictions
        if p.get("probability", 0) >= _SIGNIFICANT_THRESHOLD
    ]

    if not significant:
        findings = "No significant findings detected above the threshold."
        voice    = (
            "Your chest X-ray has been analysed by our AI model and no significant "
            "abnormalities were detected. It is still a good idea to review the "
            "results with your doctor."
        )
    else:
        names    = ", ".join(p["label"] for p in significant)
        findings = (
            f"The following findings were detected with significant probability: "
            f"{names}. Please consult a doctor for clinical confirmation."
        )
        voice    = (
            f"The X-ray analysis detected some findings that may need attention, "
            f"including {names.lower()}. Please see your doctor to discuss "
            f"these results and get a proper clinical assessment."
        )

    return {
        "findings":          findings,
        "voice_explanation": voice,
        "advice":            (
            "Please consult a qualified doctor or radiologist to review "
            "these AI-generated findings. Do not use this as a diagnosis."
        ),
    }