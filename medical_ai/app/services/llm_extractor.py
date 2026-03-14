"""
llm_extractor.py
─────────────────
LLM extraction for ALL medical report types (LAB, IMAGING, CLINICAL, etc.)

Key changes vs previous version:
  - _process_section for LAB no longer calls extract_lab_values() (which was
    a second LLM call). Regex hits are merged directly from tests_analysis.
  - lab_values key removed from section output — tests_analysis is the single
    source of truth. Assembler reads tests_analysis directly.
  - metadata and raw_text stripped from section output to reduce response size.
  - LLM backend: OpenAI API (replaces Gemini + Ollama).
"""

from __future__ import annotations

import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import urllib.request
import urllib.error

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

_OPENAI_API_BASE = "https://api.openai.com/v1"
_MODEL           = os.getenv("OPENAI_MODEL",   "gpt-4o-mini")
_TIMEOUT         = int(os.getenv("OPENAI_TIMEOUT", "45"))
_MAX_INPUT_CHARS = int(os.getenv("MAX_REPORT_CHARS", "4000"))


def _truncate(text: str, max_chars: int = _MAX_INPUT_CHARS) -> str:
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    last_nl = cut.rfind("\n")
    return cut[:last_nl] if last_nl > max_chars * 0.8 else cut


# ══════════════════════════════════════════════════════════════════════════════
# PROMPT
# ══════════════════════════════════════════════════════════════════════════════

_LANGUAGES: dict[str, dict[str, str]] = {
    "en": {"name": "English",   "instruction": "Write ALL text fields in English.",  "consult": "Consult a doctor"},
    "bn": {"name": "Bengali",   "instruction": "সমস্ত টেক্সট ফিল্ড বাংলায় লিখুন। ONLY use Bengali for all explanations, summaries, advice, and voice_explanation.", "consult": "একজন ডাক্তারের পরামর্শ নিন"},
    "ar": {"name": "Arabic",    "instruction": "اكتب جميع حقول النص باللغة العربية. ONLY use Arabic for all explanations, summaries, advice, and voice_explanation.", "consult": "استشر طبيبًا"},
    "hi": {"name": "Hindi",     "instruction": "सभी टेक्स्ट फ़ील्ड हिंदी में लिखें। ONLY use Hindi for all explanations, summaries, advice, and voice_explanation.", "consult": "किसी डॉक्टर से सलाह लें"},
    "ur": {"name": "Urdu",      "instruction": "تمام متن کے خانوں میں اردو لکھیں۔ ONLY use Urdu for all explanations, summaries, advice, and voice_explanation.", "consult": "کسی ڈاکٹر سے مشورہ کریں"},
}

def _get_lang(language: str) -> dict[str, str]:
    return _LANGUAGES.get(language, _LANGUAGES["en"])


def _build_prompt(language: str = "en") -> str:
    lang = _get_lang(language)
    return f"""You are a cautious and educational medical explanation AI.

LANGUAGE REQUIREMENT (MANDATORY):
{lang["instruction"]}
Every text field MUST be in {lang["name"]}. Exceptions: numeric values, units, and
status values ("Normal", "High", "Low", "Unknown") which stay in English.

TASK: Analyze the medical report and return structured JSON.
Identify the section or report type from the document context (e.g. "Dental Findings",
"CBCT Scan Overview", "Blood Test Results") and set it as "section_title".
Each section title should be unique.
If the document has a clear test category or specialist area, use that as the title.

For EACH test or finding:
1) "test_name": Name of the test.
2) "value": Measured value (number if possible, else string).
3) "unit": Unit of measurement.
4) "reference_range": Normal range if provided.
5) "status": MUST be one of: "Normal", "High", "Low", "Unknown" — always English.
6) "keyword_explanation": In {lang["name"]} — what this test measures (3-5 lines).
7) "result_explanation": In {lang["name"]} — what this patient's result means.

STRICT RULES:
- Do NOT diagnose or prescribe. Do NOT invent values.
- If unsure, say "{lang["consult"]}".
- Return VALID JSON only. No markdown. No text outside JSON.

VOICE EXPLANATION: A short spoken paragraph (3-5 sentences) in {lang["name"]} for TTS.

Return ONLY this JSON:
{{
  "section_title": "Short unique English title of this report section of this report about (e.g. Dental Impact Evaluation, Radicular Cyst - lower left, Radicular Reference & disclaimer)",
  "summary": "Overall explanation in {lang["name"]}",
  "voice_explanation": "Spoken paragraph in {lang["name"]}",
  "tests_analysis": [
    {{
      "test_name": "name", "value": 10.2, "unit": "g/dL",
      "reference_range": "13.0-17.0", "status": "Low",
      "keyword_explanation": "...", "result_explanation": "..."
    }}
  ],
  "risk_level": "Low | Medium | High",
  "advice": "General advice in {lang["name"]}."
}}"""


# ══════════════════════════════════════════════════════════════════════════════
# LLM CALLS — OpenAI
# ══════════════════════════════════════════════════════════════════════════════

def _call_llm(system_prompt: str, user_message: str) -> Optional[str]:
    """Call OpenAI Chat Completions API."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        logger.error("OPENAI_API_KEY not set")
        return None

    url  = f"{_OPENAI_API_BASE}/chat/completions"
    body = {
        "model": _MODEL,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},   # enforces JSON output
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
        return data["choices"][0]["message"]["content"]

    except urllib.error.HTTPError as e:
        body_text = e.read().decode(errors="replace")
        logger.error("OpenAI HTTP %s: %s", e.code, body_text)
    except TimeoutError:
        logger.error("OpenAI timed out after %ss", _TIMEOUT)
    except Exception as e:
        logger.error("OpenAI call failed: %s", e)

    return None


def _parse_json(raw: str) -> Optional[dict]:
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
# CORE EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

def _empty_report(report_type: str, sub_type: str, text: str, gender: str) -> dict:
    return {
        "summary": "", "voice_explanation": "", "tests_analysis": [],
        "risk_level": "Unknown", "advice": "", "raw_text": text,
        "metadata": {"gender": gender, "confidence": "LOW"},
    }


def _normalise_tests(parsed: dict, report_type: str, sub_type: str,
                     text: str, gender: str) -> dict:
    _VALID_STATUS = {"Normal", "High", "Low", "Unknown"}
    _VALID_RISK   = {"Low", "Medium", "High"}

    tests = []
    for item in parsed.get("tests_analysis", []):
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
        "section_title":     str(parsed.get("section_title","")).strip(),
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
    truncated   = _truncate(text)
    gender_hint = f" Patient gender: {gender}." if gender != "unknown" else ""
    user_msg    = f"Report type: {report_type} / {sub_type}.{gender_hint}\n\nMedical Report:\n{truncated}"
    prompt      = _build_prompt(language)

    raw = _call_llm(prompt, user_msg)
    if raw is None:
        # One retry with an extra nudge
        raw = _call_llm(prompt, user_msg + "\n\nReturn ONLY a JSON object.")

    parsed = _parse_json(raw) if raw else None
    if not parsed:
        logger.warning("LLM unavailable for %s/%s", report_type, sub_type)
        return _empty_report(report_type, sub_type, text, gender)

    return _normalise_tests(parsed, report_type, sub_type, text, gender)


# ── Compat shims ──────────────────────────────────────────────────────────────

def extract_lab_values(
    text: str,
    already_extracted: list[str] | None = None,
    gender: str = "unknown",
) -> list[dict]:
    """Compat shim — used by extractor.py only. Prefer tests_analysis directly."""
    report = extract_report(text, report_type="LAB", gender=gender)
    if report["metadata"]["confidence"] == "LOW":
        return []
    already_lower = {n.lower() for n in (already_extracted or [])}
    _MAP = {"Normal": "NORMAL", "High": "HIGH", "Low": "LOW", "Unknown": "UNKNOWN"}
    out  = []
    for item in report.get("tests_analysis", []):
        test = item.get("test_name", "").strip()
        if not test or test.lower() in already_lower:
            continue
        try:
            value = float(str(item.get("value", "")).replace(",", "."))
        except (TypeError, ValueError):
            continue
        out.append({"result_type": "LAB", "test": test, "value": value,
                    "unit": item.get("unit", ""),
                    "status": _MAP.get(item.get("status", "Unknown"), "UNKNOWN")})
    return out


def extract_with_llm(text, category, sub_type="UNKNOWN", gender="unknown"):
    report = extract_report(text, report_type=category, sub_type=sub_type, gender=gender)
    if report["metadata"]["confidence"] == "LOW":
        return None
    return [{"result_type": category, **report}]


def extract_lab_with_llm(text, already_extracted=None, gender="unknown"):
    return extract_lab_values(text, already_extracted=already_extracted, gender=gender)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION SPLITTING
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


def split_by_category(text: str) -> dict[str, list[str]]:
    pages  = text.split("\n\n--- PAGE BREAK ---\n\n")
    result: dict[str, list[str]] = {}

    for page in pages:
        heading_re = re.compile(
            r'(?m)^[ \t]*([A-Z][A-Z \-/]{2,50}'
            r'(?:REPORT|FINDINGS?|PROFILE|TEST|SCAN|STUDY|RESULT|CERTIFICATE|NOTE|SUMMARY)?'
            r'[\s]*(?::|\n|$))'
        )
        positions = [(m.start(), m.group()) for m in heading_re.finditer(page)]
        chunks: list[str] = []

        if len(positions) >= 2:
            if positions[0][0] > 0 and page[:positions[0][0]].strip():
                chunks.append(page[:positions[0][0]].strip())
            for i, (start, _) in enumerate(positions):
                end   = positions[i + 1][0] if i + 1 < len(positions) else len(page)
                chunk = page[start:end].strip()
                if chunk:
                    chunks.append(chunk)
        else:
            chunks = [page.strip()] if page.strip() else []

        def _score(chunk: str) -> str:
            lower  = chunk.lower()
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


# ══════════════════════════════════════════════════════════════════════════════
# MULTI-SECTION — parallel, one LLM call per section
# ══════════════════════════════════════════════════════════════════════════════

def _process_section(
    category:     str,
    section_text: str,
    sub_type:     str,
    gender:       str,
    language:     str,
) -> dict:
    """
    One LLM call per section.
    For LAB sections a CPU-only regex pass is also run (zero network cost).
    """
    report = extract_report(
        section_text, report_type=category,
        sub_type=sub_type, gender=gender, language=language,
    )

    if category == "LAB":
        try:
            from services.extractor import extract_lab_results
            regex_hits = extract_lab_results(section_text, gender=gender)
            report["regex_lab_values"] = regex_hits
        except Exception as e:
            logger.error("Regex LAB extraction failed: %s", e)
            report["regex_lab_values"] = []

    return report


def extract_multi_section(
    sections:  dict[str, list[str]],
    gender:    str = "unknown",
    sub_types: dict[str, str] | None = None,
    language:  str = "en",
) -> dict[str, list[dict]]:
    """Extract all sections in parallel — one LLM call per section."""
    sub_types   = sub_types or {}
    max_workers = int(os.getenv("OPENAI_MAX_WORKERS", "5"))

    tasks: list[tuple[str, int, str]] = [
        (cat, idx, text)
        for cat, section_list in sections.items()
        if cat != "UNKNOWN"
        for idx, text in enumerate(section_list)
    ]

    if not tasks:
        return {}

    output: dict[str, list[Optional[dict]]] = {
        cat: [None] * len(section_list)
        for cat, section_list in sections.items()
        if cat != "UNKNOWN"
    }

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_map = {
            pool.submit(
                _process_section, cat, text,
                sub_types.get(cat, "UNKNOWN"), gender, language,
            ): (cat, idx)
            for cat, idx, text in tasks
        }
        for future in as_completed(future_map):
            cat, idx = future_map[future]
            try:
                output[cat][idx] = future.result()
            except Exception as e:
                logger.error("Section %s[%d] failed: %s", cat, idx, e)
                output[cat][idx] = _empty_report(
                    cat, sub_types.get(cat, "UNKNOWN"), "", gender
                )

    return {cat: [r for r in reports if r is not None]
            for cat, reports in output.items()}