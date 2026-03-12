"""
llm_extractor.py
─────────────────
LLM extraction for ALL medical report types (LAB, IMAGING, CLINICAL, etc.)
using a single educational medical explanation prompt.

Output shape (uniform for ALL report types):
    {
        "summary":          str,
        "voice_explanation":str,   # spoken-style plain-English paragraph for TTS
        "tests_analysis": [
            {
                "test_name":          str,
                "value":              float | str,
                "unit":               str,
                "reference_range":    str,
                "status":             "Normal" | "High" | "Low" | "Unknown",
                "keyword_explanation":str,
                "result_explanation": str,
            }
        ],
        "risk_level":  "Low" | "Medium" | "High" | "Unknown",
        "advice":      str,
        "raw_text":    str,
        "metadata":    { "gender": str, "confidence": "HIGH" | "LOW" }
        # metadata is internal — stripped from final API output by assembler
    }

Public API:
    extract_report(text, report_type, sub_type, gender)      -> dict
    extract_lab_values(text, already_extracted, gender)      -> list[dict]  (compat)
    split_by_category(text)                                  -> dict[str, list[str]]
    extract_multi_section(sections, gender, sub_types)       -> dict[str, list[dict]]

Backward-compat:
    extract_with_llm(text, category, sub_type, gender)       -> list[dict] | None
    extract_lab_with_llm(text, already_extracted, gender)    -> list[dict]
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

import urllib.request
import urllib.error

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Gemini config ─────────────────────────────────────────────────────────────
_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_MODEL           = os.getenv("GEMINI_MODEL",   "gemini-2.5-flash")
_TIMEOUT         = int(os.getenv("GEMINI_TIMEOUT", "30"))


# ══════════════════════════════════════════════════════════════════════════════
# PROMPT  — single prompt for ALL report types
# ══════════════════════════════════════════════════════════════════════════════

# ── Language config ───────────────────────────────────────────────────────────
_LANGUAGES: dict[str, dict[str, str]] = {
    "en": {
        "name":        "English",
        "instruction": "Write ALL text fields in English.",
        "consult":     "Consult a doctor",
    },
    "bn": {
        "name":        "Bengali",
        "instruction": "সমস্ত টেক্সট ফিল্ড বাংলায় লিখুন। ONLY use Bengali for all explanations, summaries, advice, and voice_explanation. Do NOT use English for any text field.",
        "consult":     "একজন ডাক্তারের পরামর্শ নিন",
    },
    "ar": {
        "name":        "Arabic",
        "instruction": "اكتب جميع حقول النص باللغة العربية. ONLY use Arabic for all explanations, summaries, advice, and voice_explanation.",
        "consult":     "استشر طبيبًا",
    },
    "hi": {
        "name":        "Hindi",
        "instruction": "सभी टेक्स्ट फ़ील्ड हिंदी में लिखें। ONLY use Hindi for all explanations, summaries, advice, and voice_explanation.",
        "consult":     "किसी डॉक्टर से सलाह लें",
    },
    "ur": {
        "name":        "Urdu",
        "instruction": "تمام متن کے خانوں میں اردو لکھیں۔ ONLY use Urdu for all explanations, summaries, advice, and voice_explanation.",
        "consult":     "کسی ڈاکٹر سے مشورہ کریں",
    },
}

def _get_lang(language: str) -> dict[str, str]:
    """Return language config dict, falling back to English."""
    return _LANGUAGES.get(language, _LANGUAGES["en"])


def _build_prompt(language: str = "en") -> str:
    """
    Build the system prompt with language requirement baked in.
    The language instruction appears at the TOP (before task description)
    so the model treats it as a primary constraint, not an afterthought.
    """
    lang    = _get_lang(language)
    consult = lang["consult"]
    lang_instruction = lang["instruction"]

    return f"""You are a cautious and educational medical explanation AI.

LANGUAGE REQUIREMENT (MANDATORY):
{lang_instruction}
Every single text field in your JSON response — including test_name (if translatable),
keyword_explanation, result_explanation, summary, voice_explanation, and advice —
MUST be written in {lang["name"]}. This is non-negotiable.
The only exceptions are: numeric values, units (g/dL, mg/L etc.), and the status
field values ("Normal", "High", "Low", "Unknown") which must stay in English for
downstream parsing.

TASK:
Analyze the medical report and return structured JSON.
For EACH medical test or finding, create a JSON object with the following fields:

1) "test_name": Name of the test or finding (transliterate/translate if natural in {lang["name"]}).
2) "value": The measured value (as a number if possible, else as string).
3) "unit": The unit of measurement, if provided. Keep as-is (e.g. g/dL, mmol/L).
4) "reference_range": The normal reference range, if provided in the report.
5) "status": MUST be one of: "Normal", "High", "Low", "Unknown" — always in English.
6) "keyword_explanation": In {lang["name"]} — explain what this test measures,
   why it matters, what body system it relates to, and common reasons it goes high or low.
   Keep it concise (1-2 lines).
7) "result_explanation": In {lang["name"]} — explain this patient's specific result
   in simple terms. Is it normal? What might it mean? What should they do?

IMPORTANT INSTRUCTIONS:
- Analyze each test or finding separately in its own JSON object.
- Do NOT merge explanations between different tests.
- Keep explanations factual, neutral, and educational.
- Always include all JSON keys even if value is unknown (use "Unknown" or "").

STRICT RULES:
- Do NOT diagnose diseases.
- Do NOT prescribe medication.
- Do NOT suggest specific treatments.
- If unsure, say "{consult}".
- Do NOT invent missing values.
- Only analyze what is explicitly present in the report.
- Return VALID JSON only. No markdown. No text outside JSON.

VOICE EXPLANATION (in {lang["name"]}):
Return a "voice_explanation" field — a short spoken-style paragraph (3-5 sentences)
in {lang["name"]} that can be read aloud to the patient. Rules:
- Use simple everyday language (no medical jargon).
- Mention the overall result (good / mixed / concerning).
- Name any abnormal values naturally.
- End with a calm reassuring next step.
- Speak directly — do NOT say "your report shows".
- Do NOT diagnose or prescribe.

Return this exact JSON structure:
{{
  "summary": "Overall simplified explanation in {lang["name"]}",
  "voice_explanation": "Spoken paragraph in {lang["name"]} for TTS",
  "tests_analysis": [
    {{
      "test_name": "test name",
      "value": 10.2,
      "unit": "g/dL",
      "reference_range": "13.0-17.0",
      "status": "Low",
      "keyword_explanation": "explanation in {lang["name"]}",
      "result_explanation": "explanation in {lang["name"]}"
    }}
  ],
  "risk_level": "Low | Medium | High",
  "advice": "General safety advice in {lang["name"]}. If abnormalities exist, recommend consulting a doctor."
}}"""


# ══════════════════════════════════════════════════════════════════════════════
# GEMINI CALL
# ══════════════════════════════════════════════════════════════════════════════

def _call_llm(system_prompt: str, user_message: str) -> Optional[str]:
    """Call Gemini REST API. Returns raw text response or None on any failure."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        logger.error("GEMINI_API_KEY not set — LLM extraction unavailable")
        return None

    url  = f"{_GEMINI_API_BASE}/{_MODEL}:generateContent?key={api_key}"
    body = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents":           [{"role": "user", "parts": [{"text": user_message}]}],
        "generationConfig":   {"temperature": 0.1, "responseMimeType": "application/json"},
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
    except TimeoutError:
        logger.error("Gemini timed out after %ss", _TIMEOUT)
    except Exception as e:
        logger.error("Gemini call failed: %s", e)
    return None


# ══════════════════════════════════════════════════════════════════════════════
# OLLAMA CALL  (local inference — no API key required)
#
# Usage:
#   Set OLLAMA_ENABLED=true in your .env to route all extraction through Ollama.
#   Set OLLAMA_MODEL to any model you have pulled, e.g. "llama3", "mistral",
#   "phi3", "gemma2". Defaults to "llama3".
#   Set OLLAMA_BASE_URL if Ollama is not on localhost (default http://localhost:11434).
#
#   To call directly from code:
#       result = extract_report_ollama(text, report_type="LAB", gender="female")
#
# Notes:
#   • Ollama uses the /api/chat endpoint with OpenAI-compatible message format.
#   • JSON mode is requested via "format": "json" — works on llama3, mistral,
#     phi3, gemma2. If your model ignores it, _parse_json() will still strip
#     markdown fences and extract the JSON object.
#   • Ollama can be slow for large reports — OLLAMA_TIMEOUT defaults to 120s.
# ══════════════════════════════════════════════════════════════════════════════

_OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
_OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",    "llama3")
_OLLAMA_TIMEOUT  = int(os.getenv("OLLAMA_TIMEOUT", "120"))
_OLLAMA_ENABLED  = os.getenv("OLLAMA_ENABLED",  "false").lower() == "true"


def _call_ollama(system_prompt: str, user_message: str) -> Optional[str]:
    """
    Call a locally running Ollama model via its /api/chat REST endpoint.
    Returns raw text response, or None on any failure.

    The prompt instructs the model to return JSON — same contract as _call_llm().
    Works offline with no API key. Configure via env vars:
        OLLAMA_BASE_URL  (default: http://localhost:11434)
        OLLAMA_MODEL     (default: llama3)
        OLLAMA_TIMEOUT   (default: 120s — local models are slower)
    """
    url  = f"{_OLLAMA_BASE_URL}/api/chat"
    body = {
        "model":    _OLLAMA_MODEL,
        "format":   "json",          # request JSON output where supported
        "stream":   False,           # single response, not streaming
        "options":  {"temperature": 0.1},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    }
    try:
        req = urllib.request.Request(
            url, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=_OLLAMA_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
        # Ollama /api/chat response: { "message": { "content": "..." }, ... }
        return data["message"]["content"]
    except urllib.error.URLError as e:
        logger.error("Ollama not reachable at %s — is it running? (%s)", _OLLAMA_BASE_URL, e)
    except KeyError:
        logger.error("Ollama response missing expected fields: %s", data)
    except TimeoutError:
        logger.error("Ollama timed out after %ss (model: %s)", _OLLAMA_TIMEOUT, _OLLAMA_MODEL)
    except Exception as e:
        logger.error("Ollama call failed: %s", e)
    return None


def extract_report_ollama(
    text:        str,
    report_type: str = "UNKNOWN",
    sub_type:    str = "UNKNOWN",
    gender:      str = "unknown",
    language:    str = "en",
) -> dict:
    """
    Extract a structured medical report using a local Ollama model.

    Drop-in replacement for extract_report() — same return shape, same prompt.
    Use this when:
      • You want fully offline / air-gapped processing.
      • You want to avoid Gemini API costs during development.
      • You want to test a specific local model.

    Returns the same dict shape as extract_report():
        { summary, voice_explanation, tests_analysis, risk_level,
          advice, raw_text, metadata }

    Example:
        from services.llm_extractor import extract_report_ollama
        result = extract_report_ollama(raw_text, report_type="LAB", gender="female")
    """
    gender_hint  = f" Patient gender: {gender}." if gender != "unknown" else ""
    user_message = (
        f"Report type: {report_type} / {sub_type}.{gender_hint}\n\n"
        f"Medical Report:\n{text}"
        f"\n\nReturn ONLY a valid JSON object. No markdown. No text outside JSON."
    )

    raw    = _call_ollama(_build_prompt(language), user_message)
    parsed = _parse_json(raw) if raw else None

    if not parsed:
        logger.warning(
            "Ollama extraction failed for %s/%s (model: %s) — raw_text stored only",
            report_type, sub_type, _OLLAMA_MODEL,
        )
        return _empty_report(report_type, sub_type, text, gender)

    return _normalise_tests(parsed, report_type, sub_type, text, gender)


def _parse_json(raw: str) -> Optional[dict]:
    """Parse JSON, stripping markdown fences if present."""
    cleaned = re.sub(r'^```(?:json)?\s*', '', raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r'\s*```$', '', cleaned.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        m = re.search(r'\{[\s\S]+\}', cleaned)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return None


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def _empty_report(report_type: str, sub_type: str, text: str, gender: str) -> dict:
    """Fallback report when LLM is unavailable."""
    return {
        "summary":           "",
        "voice_explanation": "",
        "tests_analysis":    [],
        "risk_level":        "Unknown",
        "advice":            "",
        "raw_text":          text,
        "metadata":          {"gender": gender, "confidence": "LOW"},
    }


def _normalise_tests(parsed: dict, report_type: str, sub_type: str,
                     text: str, gender: str) -> dict:
    """
    Normalise raw LLM JSON into the canonical report dict.
    Handles missing keys gracefully.
    """
    _VALID_STATUS   = {"Normal", "High", "Low", "Unknown"}
    _VALID_RISK     = {"Low", "Medium", "High"}

    tests = []
    for item in parsed.get("tests_analysis", []):
        # Normalise value — keep as float if possible, else string
        raw_val = item.get("value", "")
        try:
            value = float(str(raw_val).replace(",", "."))
        except (TypeError, ValueError):
            value = str(raw_val).strip()

        status = str(item.get("status", "Unknown")).capitalize()
        if status not in _VALID_STATUS:
            status = "Unknown"

        tests.append({
            "test_name":           str(item.get("test_name",           "")).strip(),
            "value":               value,
            "unit":                str(item.get("unit",                "")).strip(),
            "reference_range":     str(item.get("reference_range",     "")).strip(),
            "status":              status,
            "keyword_explanation": str(item.get("keyword_explanation", "")).strip(),
            "result_explanation":  str(item.get("result_explanation",  "")).strip(),
        })

    risk = str(parsed.get("risk_level", "Unknown")).capitalize()
    if risk not in _VALID_RISK:
        risk = "Unknown"

    return {
        "summary":           str(parsed.get("summary",           "")).strip(),
        "voice_explanation": str(parsed.get("voice_explanation", "")).strip(),
        "tests_analysis":    tests,
        "risk_level":        risk,
        "advice":            str(parsed.get("advice", "")).strip(),
        "raw_text":          text,
        "metadata":          {"gender": gender, "confidence": "HIGH"},
    }


def extract_report(
    text:        str,
    report_type: str = "UNKNOWN",
    sub_type:    str = "UNKNOWN",
    gender:      str = "unknown",
    language:    str = "en",
) -> dict:
    """
    Extract structured educational analysis from ANY medical report.

    Works for LAB, IMAGING, CLINICAL, SPECIALIST, PATHOLOGY, ADMINISTRATIVE.
    The same prompt is used for all types — each test/finding gets its own
    detailed explanation entry in tests_analysis.

    Always returns a valid dict. raw_text is always populated so downstream
    steps (chatbot, RAG) always have content even if the LLM call fails.

    Returns:
        {
            "summary":           str,
            "voice_explanation": str,   # spoken-style paragraph for TTS/audio
            "tests_analysis": [
                {
                    "test_name":           str,
                    "value":               float | str,
                    "unit":                str,
                    "reference_range":     str,
                    "status":              "Normal"|"High"|"Low"|"Unknown",
                    "keyword_explanation": str,
                    "result_explanation":  str,
                }
            ],
            "risk_level":  "Low"|"Medium"|"High"|"Unknown",
            "advice":      str,
            "raw_text":    str,
            "metadata":    { "gender": str, "confidence": "HIGH"|"LOW" }
        }
        Note: metadata is internal — consumed by pipeline, stripped from final output.
        Set OLLAMA_ENABLED=true to route through local Ollama instead of Gemini.
    """
    # ── Ollama fast-path ──────────────────────────────────────────────────────
    if _OLLAMA_ENABLED:
        logger.debug("OLLAMA_ENABLED — routing to local model %s", _OLLAMA_MODEL)
        return extract_report_ollama(text, report_type=report_type,
                                     sub_type=sub_type, gender=gender, language=language)

    # ── Gemini path ───────────────────────────────────────────────────────────
    gender_hint  = f" Patient gender: {gender}." if gender != "unknown" else ""
    user_message = (
        f"Report type: {report_type} / {sub_type}.{gender_hint}\n\n"
        f"Medical Report:\n{text}"
    )

    prompt = _build_prompt(language)
    raw = _call_llm(prompt, user_message)
    if raw is None:
        raw = _call_llm(prompt, user_message + "\n\nReturn ONLY a JSON object.")

    parsed = _parse_json(raw) if raw else None

    if not parsed:
        logger.warning("LLM unavailable for %s/%s — raw_text stored only", report_type, sub_type)
        return _empty_report(report_type, sub_type, text, gender)

    return _normalise_tests(parsed, report_type, sub_type, text, gender)


def extract_lab_values(
    text:              str,
    already_extracted: list[str] | None = None,
    gender:            str = "unknown",
) -> list[dict]:
    """
    Compatibility shim — extracts lab values from tests_analysis for callers
    that still expect the old { test, value, unit, status } list shape.

    Used by extractor.py LAB dispatcher and report_assembler.py.
    Always returns [] on failure — never raises.
    """
    report = extract_report(text, report_type="LAB", gender=gender)
    if report["metadata"]["confidence"] == "LOW":
        return []

    already_lower = {n.lower() for n in (already_extracted or [])}
    _STATUS_MAP   = {"Normal": "NORMAL", "High": "HIGH",
                     "Low": "LOW", "Unknown": "UNKNOWN"}
    results = []

    for item in report.get("tests_analysis", []):
        test = item.get("test_name", "").strip()
        if not test or test.lower() in already_lower:
            continue

        raw_val = item.get("value", "")
        try:
            value = float(str(raw_val).replace(",", "."))
        except (TypeError, ValueError):
            continue   # skip non-numeric for lab_values compat list

        status = _STATUS_MAP.get(item.get("status", "Unknown"), "UNKNOWN")
        results.append({
            "result_type": "LAB",
            "test":   test,
            "value":  value,
            "unit":   item.get("unit", ""),
            "status": status,
        })

    return results


# ══════════════════════════════════════════════════════════════════════════════
# BACKWARD-COMPAT — called by extractor.py dispatcher (signatures unchanged)
# ══════════════════════════════════════════════════════════════════════════════

def extract_with_llm(
    text:     str,
    category: str,
    sub_type: str = "UNKNOWN",
    gender:   str = "unknown",
) -> Optional[list[dict]]:
    """
    Called by extractor.py for non-LAB categories.
    Returns a single-element list wrapping the extract_report() dict,
    or None on failure so extractor.py falls back to keyword extractor.
    """
    report = extract_report(text, report_type=category, sub_type=sub_type, gender=gender)
    if report["metadata"]["confidence"] == "LOW":
        return None  # triggers keyword fallback in extractor.py
    return [{"result_type": category, **report}]


def extract_lab_with_llm(
    text:              str,
    already_extracted: list | None = None,
    gender:            str = "unknown",
) -> list[dict]:
    """Called by extractor.py LAB dispatcher as second-pass."""
    return extract_lab_values(text, already_extracted=already_extracted, gender=gender)


# ══════════════════════════════════════════════════════════════════════════════
# MULTI-SECTION — split mixed PDF, extract each section independently
# ══════════════════════════════════════════════════════════════════════════════

_SECTION_SIGNALS: dict[str, list[str]] = {
    "LAB": [
        "haemoglobin", "hemoglobin", "wbc", "white blood cell", "platelet",
        "haematology", "hematology", "biochemistry", "liver function",
        "renal function", "thyroid function", "lipid profile", "blood glucose",
        "hba1c", "serum", "urine analysis", "urinalysis", "cbc",
        "complete blood", "lft", "rft", "tft", "differential count",
    ],
    "IMAGING": [
        "x-ray", "xray", "radiograph", "ultrasound", "usg",
        "ct scan", "computed tomography", "mri", "magnetic resonance",
        "pet scan", "mammogram", "echocardiogram", "findings:", "impression:",
    ],
    "SPECIALIST": [
        "dental", "cbct", "periapical", "orthodontic", "orthopaedic",
        "orthopedic", "physiotherapy", "neurology", "psychiatric",
        "mental state", "ophthalmology", "visual acuity", "cardiology",
        "ecg", "electrocardiogram",
    ],
    "PATHOLOGY": [
        "histopathology", "histopath", "biopsy", "cytology", "culture",
        "sensitivity", "organism", "microscopy", "gross examination",
        "sections show", "bethesda",
    ],
    "CLINICAL": [
        "chief complaint", "presenting complaint", "c/o", "on examination",
        "diagnosis:", "prescription", "discharge summary", "opd note",
        "progress note", "plan:", "advice:",
    ],
    "ADMINISTRATIVE": [
        "to whom it may concern", "certify that", "fit to",
        "medically fit", "medical certificate", "fitness certificate",
    ],
}


# Chunks shorter than this are treated as continuation fragments (header/footer
# pages, page numbers, clinic logos etc.) and merged into the previous section.
_MIN_CHUNK_CHARS = 300

# Known page-break markers inserted by PDF extractors
_PAGE_BREAK_PATTERNS = [
    "\n\n--- PAGE BREAK ---\n\n",   # our own marker
    "\f",                            # form-feed character (PyMuPDF, pdfminer)
    "\x0c",                          # same as \f
    "- - - PAGE - - -",
    "========== PAGE",
]


def _normalise_page_breaks(text: str) -> str:
    """
    Replace all known page-break markers with a single blank line.
    A single report spans multiple pages — page breaks are layout
    artifacts and must NOT be used as report boundaries.
    """
    for marker in _PAGE_BREAK_PATTERNS:
        text = text.replace(marker, "\n\n")
    # Collapse 3+ consecutive blank lines into 2 (keeps paragraph spacing)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _score_category(chunk: str) -> tuple[str, int]:
    """
    Score a text chunk against category keyword signals.
    Returns (best_category, score). score=0 → UNKNOWN.
    """
    lower  = chunk.lower()
    scores = {cat: sum(1 for sig in sigs if sig in lower)
              for cat, sigs in _SECTION_SIGNALS.items()}
    best, score = max(scores.items(), key=lambda x: x[1])
    return (best, score) if score > 0 else ("UNKNOWN", 0)


def split_by_category(text: str) -> dict[str, list[str]]:
    """
    Split mixed PDF text into per-category section lists.

    Returns: { "LAB": ["section text", ...], "IMAGING": [...], ... }
    Consecutive same-category chunks are merged automatically.
    """

    # NEW: Split text by page break
    pages = text.split("\n\n--- PAGE BREAK ---\n\n")

    result: dict[str, list[str]] = {}

    for page in pages:

        heading_re = re.compile(
            r'(?m)^[ \t]*'
            r'([A-Z][A-Z \-/]{2,50}'
            r'(?:REPORT|FINDINGS?|PROFILE|TEST|SCAN|STUDY|RESULT|CERTIFICATE|NOTE|SUMMARY)?'
            r'[\s]*(?::|\n|$))'
        )

        positions = [(m.start(), m.group()) for m in heading_re.finditer(page)]

        chunks: list[str] = []

        if len(positions) >= 2:
            if positions[0][0] > 0 and page[:positions[0][0]].strip():
                chunks.append(page[:positions[0][0]].strip())

            for i, (start, _) in enumerate(positions):
                end = positions[i + 1][0] if i + 1 < len(positions) else len(page)
                chunk = page[start:end].strip()
                if chunk:
                    chunks.append(chunk)
        else:
            chunks = [page.strip()] if page.strip() else []

        def _score(chunk: str) -> str:
            lower = chunk.lower()
            scores = {c: sum(1 for s in sigs if s in lower)
                      for c, sigs in _SECTION_SIGNALS.items()}
            best, score = max(scores.items(), key=lambda x: x[1])
            return best if score > 0 else "UNKNOWN"

        merged: list[tuple[str, str]] = []
        for cat, chunk in [(_score(c), c) for c in chunks]:
            if merged and merged[-1][0] == cat:
                merged[-1] = (cat, merged[-1][1] + "\n\n" + chunk)
            else:
                merged.append((cat, chunk))

        for cat, chunk in merged:
            result.setdefault(cat, []).append(chunk)

    return result



def extract_multi_section(
    sections:  dict[str, list[str]],
    gender:    str = "unknown",
    sub_types: dict[str, str] | None = None,
    language:  str = "en",
) -> dict[str, list[dict]]:
    """
    Extract all sections from a mixed PDF.
    Each section is processed with extract_report() independently,
    then stored as a list under its category key.

    LAB sections also get lab_values populated via regex + LLM.

    Returns:
        {
          "LAB":     [ { report_type, sub_type, summary, findings, ..., lab_values }, ... ],
          "IMAGING": [ { report_type, sub_type, summary, findings, ... }, ... ],
          ...
        }

    Usage:
        sections = split_by_category(raw_pdf_text)
        results  = extract_multi_section(sections, gender="female")

        # Flat list if needed:
        all_sections = [r for cat in results.values() for r in cat]
    """
    sub_types = sub_types or {}
    output: dict[str, list[dict]] = {}

    for category, section_list in sections.items():
        if category == "UNKNOWN":
            continue

        sub_type     = sub_types.get(category, "UNKNOWN")
        cat_results: list[dict] = []

        for idx, section_text in enumerate(section_list):
            logger.debug("Processing %s section %d/%d", category, idx + 1, len(section_list))

            report = extract_report(section_text, report_type=category,
                                    sub_type=sub_type, gender=gender, language=language)

            # LAB: attach structured lab_values from regex + LLM second-pass
            if category == "LAB":
                try:
                    from services.extractor import extract_lab_results  # type: ignore
                    regex_hits  = extract_lab_results(section_text, gender=gender)
                    found_names = [r["test"] for r in regex_hits if "test" in r]
                    llm_hits    = extract_lab_values(section_text,
                                                     already_extracted=found_names,
                                                     gender=gender)
                    report["lab_values"] = regex_hits + llm_hits
                except Exception as e:
                    logger.error("LAB value extraction failed: %s", e)
                    report["lab_values"] = []

            cat_results.append(report)

        output[category] = cat_results

    return output