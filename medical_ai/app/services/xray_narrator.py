"""
xray_narrator.py
─────────────────
Turns raw X-ray model probability predictions into patient-friendly language
using the configured LLM (Gemini or Ollama).

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
import urllib.request
import urllib.error
from typing import Optional

logger = logging.getLogger(__name__)

# ── Shared config (reads same env vars as llm_extractor.py) ──────────────────
_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_MODEL           = os.getenv("GEMINI_MODEL",    "gemini-2.0-flash")
_TIMEOUT         = int(os.getenv("GEMINI_TIMEOUT", "30"))
_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",    "llama3")
_OLLAMA_TIMEOUT  = int(os.getenv("OLLAMA_TIMEOUT", "120"))
_OLLAMA_ENABLED  = os.getenv("OLLAMA_ENABLED",  "false").lower() == "true"

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

def _build_prompt(predictions: list[dict], language: str) -> tuple[str, str]:
    """
    Build (system_prompt, user_message) for the LLM.
    Filters to significant findings and formats probabilities clearly.
    """
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

    # Format predictions as a readable table
    rows = "\n".join(
        f"  {p['label']}: {p['probability']:.1%}"
        for p in sorted(predictions, key=lambda x: x["probability"], reverse=True)
    )
    user_message = f"X-ray AI model predictions:\n{rows}"

    return system_prompt, user_message


# ══════════════════════════════════════════════════════════════════════════════
# LLM CALLS
# ══════════════════════════════════════════════════════════════════════════════

def _call_gemini(system_prompt: str, user_message: str) -> Optional[str]:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        logger.error("GEMINI_API_KEY not set")
        return None
    url  = f"{_GEMINI_API_BASE}/{_MODEL}:generateContent?key={api_key}"
    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents":           [{"role": "user", "parts": [{"text": user_message}]}],
        "generationConfig":   {"temperature": 0.2, "responseMimeType": "application/json"},
    }
    try:
        req = urllib.request.Request(
            url, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        logger.error("Gemini HTTP %s: %s", e.code, e.read().decode(errors="replace"))
    except Exception as e:
        logger.error("Gemini xray narration failed: %s", e)
    return None


def _call_ollama(system_prompt: str, user_message: str) -> Optional[str]:
    url  = f"{_OLLAMA_BASE_URL}/api/chat"
    body = {
        "model":    _OLLAMA_MODEL,
        "format":   "json",
        "stream":   False,
        "options":  {"temperature": 0.2},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message + "\n\nReturn ONLY a valid JSON object."},
        ],
    }
    try:
        req = urllib.request.Request(
            url, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=_OLLAMA_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
        return data["message"]["content"]
    except urllib.error.URLError as e:
        logger.error("Ollama not reachable at %s: %s", _OLLAMA_BASE_URL, e)
    except Exception as e:
        logger.error("Ollama xray narration failed: %s", e)
    return None


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
    Convert X-ray model predictions into patient-friendly text via LLM.

    Args:
        predictions: list of { "label": str, "probability": float }
                     from XRayService.analyze()
        language:    "en" | "bn" | "ar" | "hi" | "ur"

    Returns:
        {
            "findings":         str,
            "voice_explanation":str,
            "advice":           str,
        }
        Falls back to a plain-text summary if LLM is unavailable.
    """
    if not predictions:
        return _fallback_narration(predictions, language)

    system_prompt, user_message = _build_prompt(predictions, language)

    # Route to Ollama or Gemini
    if _OLLAMA_ENABLED:
        raw = _call_ollama(system_prompt, user_message)
    else:
        raw = _call_gemini(system_prompt, user_message)

    result = _parse_narration(raw)
    if result:
        return result

    logger.warning("LLM narration failed — using rule-based fallback")
    return _fallback_narration(predictions, language)


def _fallback_narration(predictions: list[dict], language: str) -> dict:
    """
    Rule-based fallback when the LLM is unavailable.
    Lists significant findings above threshold in plain English.
    """
    significant = [
        p for p in predictions
        if p.get("probability", 0) >= _SIGNIFICANT_THRESHOLD
    ]

    if not significant:
        findings = "No significant findings detected above the threshold."
        voice    = ("Your chest X-ray has been analysed by our AI model and no significant "
                    "abnormalities were detected. It is still a good idea to review the "
                    "results with your doctor.")
    else:
        names    = ", ".join(p["label"] for p in significant)
        findings = (f"The following findings were detected with significant probability: "
                    f"{names}. Please consult a doctor for clinical confirmation.")
        voice    = (f"The X-ray analysis detected some findings that may need attention, "
                    f"including {names.lower()}. Please see your doctor to discuss "
                    f"these results and get a proper clinical assessment.")

    return {
        "findings":         findings,
        "voice_explanation":voice,
        "advice":           "Please consult a qualified doctor or radiologist to review "
                            "these AI-generated findings. Do not use this as a diagnosis.",
    }