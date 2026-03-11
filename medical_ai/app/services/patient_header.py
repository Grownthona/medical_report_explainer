"""
patient_header.py
─────────────────
Stage 1 of the medical report pipeline.

Extracts structured patient metadata from raw OCR text:
  - name
  - age (years)
  - gender
  - report_type  ← inferred from which lab tests are present
  - collection_date

Strategy:
  1. LLM extraction via Gemini — handles messy OCR, non-standard formats,
     mixed-language headers (Bangla/English), clinic name leaking into name field.
  2. Regex fallback — for any field the LLM returned null/empty, or if
     GEMINI_API_KEY is not set.

Run this BEFORE clean_text() so noise stripping doesn't destroy header values.
"""

import json
import logging
import os
import re
import urllib.request
import urllib.error
from dataclasses import dataclass, asdict
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

# ── Gemini config (shared with llm_extractor.py) ─────────────────────────────
_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
_MODEL           = os.getenv("GEMINI_MODEL",   "gemini-2.5-flash")
_TIMEOUT         = int(os.getenv("GEMINI_TIMEOUT", "30"))


# ─── Output model ─────────────────────────────────────────────────────────────

@dataclass
class PatientHeader:
    name:            Optional[str]   # "FARAH DIRA RAHMAN"
    age_years:       Optional[int]   # 50
    gender:          str             # "male" | "female" | "unknown"
    report_type:     Optional[str]   # "CBC" | "LFT" | "RFT" | "TFT" | "LIPID" | "MIXED"
    collection_date: Optional[str]   # "2023-07-16"  ISO format

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Report type signatures ───────────────────────────────────────────────────

REPORT_SIGNATURES: list[tuple[frozenset, str]] = [
    (frozenset({"TSH", "T3", "T4"}),                                          "TFT"),
    (frozenset({"ALT", "AST", "ALP", "Total Bilirubin"}),                     "LFT"),
    (frozenset({"ALT", "AST"}),                                                "LFT"),
    (frozenset({"Creatinine", "Blood Urea", "BUN"}),                           "RFT"),
    (frozenset({"Creatinine", "Blood Urea"}),                                  "RFT"),
    (frozenset({"Total Cholesterol", "LDL Cholesterol", "HDL Cholesterol",
                "Triglycerides"}),                                             "LIPID"),
    (frozenset({"Total Cholesterol", "Triglycerides"}),                        "LIPID"),
    (frozenset({"Haemoglobin", "WBC (Total)", "RBC", "Platelets"}),           "CBC"),
    (frozenset({"Haemoglobin", "WBC (Total)"}),                               "CBC"),
    (frozenset({"Haemoglobin", "Platelets"}),                                  "CBC"),
]


def infer_report_type(lab_test_names: list[str]) -> Optional[str]:
    """Infer the report panel type from the list of test names returned by the NER."""
    found_names    = set(lab_test_names)
    matched_panels = []
    for signature, panel in REPORT_SIGNATURES:
        if signature.issubset(found_names):
            if panel not in matched_panels:
                matched_panels.append(panel)
    if not matched_panels:
        return None
    if len(matched_panels) == 1:
        return matched_panels[0]
    return "MIXED"


# ══════════════════════════════════════════════════════════════════════════════
# LLM EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

_HEADER_PROMPT = """You are a medical report parser specializing in patient header extraction.

Extract patient information from the medical report text and return ONLY a JSON object.

Return this exact structure:
{
  "name":             "Patient full name in UPPERCASE, or null if not found",
  "age_years":        25,
  "gender":           "male" or "female" or "unknown",
  "collection_date":  "YYYY-MM-DD format, or null if not found",
  "referred_by":      "Referring doctor name, or null if not found",
  "lab_no":           "Lab number or sample ID, or null if not found",
  "invoice_no":       "Invoice number, or null if not found"
}

RULES:
- name: Extract the PATIENT name only. Ignore clinic names, lab names, hospital
  names, doctor names, and any organisation names. Common clinic name words to
  ignore: Modern, Diagnostic, Centre, Unit, Limited, Ltd, Apollo, Lab, Hospital,
  Clinic, Institute, Health, Care, Medical, Chamber, Complex.
  Return null if you cannot confidently identify the patient name.
- age_years: Return as integer. Convert months to fractional year if needed.
  Return null if not found.
- gender: "male" if Male/M/Mr, "female" if Female/F/Ms/Mrs, "unknown" otherwise.
- collection_date: Convert any date format to YYYY-MM-DD. Use collection/sample
  date, not report date or delivery date. Return null if not found.
- referred_by: Doctor or physician who referred the patient. Return null if not found.
- lab_no: The sample/lab accession number (not invoice number). Return null if not found.
- invoice_no: The invoice or bill number. Return null if not found.
- Return ONLY valid JSON. No markdown. No explanation. No extra keys."""


def _call_gemini(user_message: str) -> Optional[str]:
    """Call Gemini REST API. Returns raw text or None on failure."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None

    url  = f"{_GEMINI_API_BASE}/{_MODEL}:generateContent?key={api_key}"
    body = {
        "system_instruction": {"parts": [{"text": _HEADER_PROMPT}]},
        "contents":           [{"role": "user", "parts": [{"text": user_message}]}],
        "generationConfig":   {"temperature": 0.0, "responseMimeType": "application/json"},
    }
    try:
        req = urllib.request.Request(
            url, data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            result = json.loads(resp.read().decode())
            parts  = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            return parts[0].get("text") if parts else None
    except Exception as e:
        logger.warning("Gemini header extraction failed: %s", e)
        return None


def _parse_header_json(raw: Optional[str]) -> Optional[dict]:
    """Parse LLM response into a dict. Returns None on failure."""
    if not raw:
        return None
    # Strip markdown fences if present
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find a JSON object anywhere in the response
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return None


def _extract_header_llm(text: str) -> Optional[dict]:
    """
    Extract patient header fields using Gemini LLM.
    Returns dict with keys: name, age_years, gender, collection_date,
    referred_by, lab_no, invoice_no — or None if LLM unavailable.
    """
    # Limit input to first ~1500 chars — header is always near the top
    user_message = f"Medical report (extract patient header info only):\n\n{text[:1500]}"
    raw    = _call_gemini(user_message)
    parsed = _parse_header_json(raw)
    if parsed is None:
        logger.warning("LLM header extraction failed — falling back to regex")
    return parsed


# ══════════════════════════════════════════════════════════════════════════════
# REGEX FALLBACK EXTRACTORS
# ══════════════════════════════════════════════════════════════════════════════

# ─── Name ────────────────────────────────────────────────────────────────────

_NAME_PREFIX = re.compile(
    r'\b(?:patient\s*(?:name)?\s*[:\.]?\s*(?:ms|mr|mrs|dr)?\.?\s*'
    r'|patientms\.\s*'
    r'|name\s*[:\-]\s*)',
    re.IGNORECASE
)

_NAME_BLOCKLIST = {
    "NORMAL", "RANGE", "RESULT", "REPORT", "TEST", "MALE", "FEMALE",
    "BLOOD", "SPECIMEN", "COLLECTION", "DATE", "PRINTED", "INDOOR",
    "OUTDOOR", "OUT", "DOOR", "TYPE", "GENDER", "AGE", "PATIENT",
    "MODERN", "DIAGNOSTIC", "CENTRE", "UNIT", "LIMITED", "LTD",
    "HAEMATOLOGY", "HEMATOLOGY", "ANALYSIS", "REFERRED", "PROF",
    "TOTAL", "COUNT", "DIFFERENTIAL", "AUTOANALYZER", "METHOD",
    "APOLLO", "HOSPITAL", "CLINIC", "LAB", "LABORATORY", "INSTITUTE",
    "HEALTH", "CARE", "MEDICAL", "CHAMBER", "COMPLEX",
}

def _extract_name(text: str) -> Optional[str]:
    match = _NAME_PREFIX.search(text)
    if match:
        after = text[match.end():]
        words = []
        for part in after.split():
            part = re.sub(r'[^\w]', '', part)
            if re.match(r'^[A-Z][A-Za-z]+$', part) and part.upper() not in _NAME_BLOCKLIST:
                words.append(part)
            else:
                break
            if len(words) == 5:
                break
        if len(words) >= 2:
            return " ".join(words)

    all_caps_run = re.compile(r'\b([A-Z]{2,})(?:\s+([A-Z]{2,})){1,3}\b')
    for m in all_caps_run.finditer(text):
        candidate = m.group(0)
        words     = candidate.split()
        if all(w not in _NAME_BLOCKLIST for w in words):
            return candidate.title()
    return None


# ─── Age ─────────────────────────────────────────────────────────────────────

_AGE_PATTERNS = [
    re.compile(r'\bAge\s*[:\-]?\s*(\d{1,3})\s*Y', re.IGNORECASE),
    re.compile(r'\b(\d{1,3})\s*(?:years?|yrs?)\s*old\b', re.IGNORECASE),
    re.compile(r'\bage\s*[:\-]?\s*(\d{1,3})\b', re.IGNORECASE),
]

def _extract_age(text: str) -> Optional[int]:
    for pattern in _AGE_PATTERNS:
        m = pattern.search(text)
        if m:
            age = int(m.group(1))
            if 0 < age < 130:
                return age
    return None


# ─── Gender ───────────────────────────────────────────────────────────────────

def _extract_gender(text: str) -> str:
    for pattern in [
        re.compile(r'\bGender\s*[:\-]?\s*(Male|Female)\b', re.IGNORECASE),
        re.compile(r'\bSex\s*[:\-]?\s*(Male|Female)\b',    re.IGNORECASE),
    ]:
        m = pattern.search(text)
        if m:
            return m.group(1).lower()
    if re.search(r'\b(MS|MRS)\b\.?\s+[A-Z]', text, re.IGNORECASE):
        return "female"
    if re.search(r'\bMR\b\.?\s+[A-Z]', text, re.IGNORECASE):
        return "male"
    return "unknown"


# ─── Date ────────────────────────────────────────────────────────────────────

_DATE_PATTERNS = [
    re.compile(r'(?:Collection\s*Date|Collected|Collection)\s*[:\-]?\s*'
               r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})(?!\d)', re.IGNORECASE),
    re.compile(r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})\b'),
]

def _extract_date(text: str) -> Optional[str]:
    for pattern in _DATE_PATTERNS:
        m = pattern.search(text)
        if m:
            day, month, year = m.group(1), m.group(2), m.group(3)
            if len(year) == 4 and int(year) > 2100:
                year = year[:2]
            if len(year) == 2:
                year = "20" + year
            try:
                if 1 <= int(day) <= 31 and 1 <= int(month) <= 12 and 1900 <= int(year) <= 2100:
                    return f"{year}-{int(month):02d}-{int(day):02d}"
            except ValueError:
                continue
    return None


# ── Normalise LLM date to ISO ─────────────────────────────────────────────────

def _normalise_date(date_str: Optional[str]) -> Optional[str]:
    """Accept YYYY-MM-DD from LLM (already correct) or try to parse other formats."""
    if not date_str:
        return None
    date_str = str(date_str).strip()
    # Already ISO
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    # Try dd/mm/yyyy or dd-mm-yyyy
    m = re.match(r'^(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})$', date_str)
    if m:
        day, month, year = m.group(1), m.group(2), m.group(3)
        if len(year) == 2:
            year = "20" + year
        try:
            if 1 <= int(day) <= 31 and 1 <= int(month) <= 12:
                return f"{year}-{int(month):02d}-{int(day):02d}"
        except ValueError:
            pass
    return None


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def extract_header(raw: str, lab_results: Optional[list] = None) -> PatientHeader:
    """
    Extract patient metadata from raw OCR text.

    LLM runs first for best accuracy on messy OCR.
    Regex fills in any fields the LLM returns as null/empty.

    Args:
        raw:         Raw OCR or report text (before any cleaning)
        lab_results: Optional list of LabResult dicts from the NER extractor.
                     If provided, used to infer report_type from actual tests found.

    Returns:
        PatientHeader dataclass with extra LLM fields stored in .extra if present
    """
    # ── Step 1: try LLM ───────────────────────────────────────────────────────
    llm = _extract_header_llm(raw)
    
    # ── Step 2: extract each field — LLM first, regex fallback ───────────────
    # Name
    llm_name = (llm.get("name") or "").strip() if llm else ""
    name     = llm_name if llm_name and llm_name.upper() not in ("NULL", "NONE", "N/A") \
               else _extract_name(raw)

    # Age
    llm_age = llm.get("age_years") if llm else None
    try:
        age_years = int(llm_age) if llm_age is not None else None
    except (ValueError, TypeError):
        age_years = None
    if age_years is None:
        age_years = _extract_age(raw)

    # Gender
    llm_gender = (llm.get("gender") or "").strip().lower() if llm else ""
    gender     = llm_gender if llm_gender in ("male", "female") else _extract_gender(raw)

    # Date — LLM returns ISO already; normalise just in case
    llm_date        = _normalise_date(llm.get("collection_date") if llm else None)
    collection_date = llm_date if llm_date else _extract_date(raw)

    # ── Step 3: infer report type from NER results ────────────────────────────
    report_type = None
    if lab_results is not None:
        test_names  = [r["test"] for r in lab_results]
        report_type = infer_report_type(test_names)

    # ── Step 4: build PatientHeader — attach extra LLM-only fields ───────────
    header = PatientHeader(
        name            = name,
        age_years       = age_years,
        gender          = gender,
        report_type     = report_type,
        collection_date = collection_date,
    )

    # Attach extra fields from LLM (not in the dataclass but useful downstream)
    if llm:
        header.referred_by = (llm.get("referred_by") or "").strip() or None
        header.lab_no      = (llm.get("lab_no")      or "").strip() or None
        header.invoice_no  = (llm.get("invoice_no")  or "").strip() or None
    else:
        header.referred_by = None
        header.lab_no      = None
        header.invoice_no  = None

    return header


# ── Patch to_dict() so extra fields are included ─────────────────────────────

_original_to_dict = PatientHeader.to_dict

def _to_dict_extended(self) -> dict:
    d = asdict(self)
    for field in ("referred_by", "lab_no", "invoice_no"):
        if hasattr(self, field):
            d[field] = getattr(self, field)
    return d

PatientHeader.to_dict = _to_dict_extended