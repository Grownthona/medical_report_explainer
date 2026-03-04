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

Designed to work on messy single-line OCR output (e.g. Bangladeshi lab reports).
Run this BEFORE clean_text() so noise stripping doesn't destroy the header values.
"""

import re
from dataclasses import dataclass, asdict
from typing import Optional


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
# Matched against the SET of test names found by the NER extractor.
# More specific panels listed first — checked in order, first match wins.

REPORT_SIGNATURES: list[tuple[frozenset, str]] = [
    # Thyroid
    (frozenset({"TSH", "T3", "T4"}),                                          "TFT"),
    # Liver
    (frozenset({"ALT", "AST", "ALP", "Total Bilirubin"}),                     "LFT"),
    (frozenset({"ALT", "AST"}),                                                "LFT"),
    # Renal
    (frozenset({"Creatinine", "Blood Urea", "BUN"}),                           "RFT"),
    (frozenset({"Creatinine", "Blood Urea"}),                                  "RFT"),
    # Lipid
    (frozenset({"Total Cholesterol", "LDL Cholesterol", "HDL Cholesterol",
                "Triglycerides"}),                                             "LIPID"),
    (frozenset({"Total Cholesterol", "Triglycerides"}),                        "LIPID"),
    # CBC — broad signature, so checked after more specific panels
    (frozenset({"Haemoglobin", "WBC (Total)", "RBC", "Platelets"}),           "CBC"),
    (frozenset({"Haemoglobin", "WBC (Total)"}),                               "CBC"),
    (frozenset({"Haemoglobin", "Platelets"}),                                  "CBC"),
]


def infer_report_type(lab_test_names: list[str]) -> Optional[str]:
    """
    Infer the report panel type from the list of test names returned by the NER.
    Returns "MIXED" if multiple panel signatures match.
    """
    found_names = set(lab_test_names)
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


# ─── Name extraction ──────────────────────────────────────────────────────────

# Prefixes that immediately precede a patient name in lab reports
_NAME_PREFIX = re.compile(
    r'\b(?:patient\s*(?:name)?\s*[:\.]?\s*(?:ms|mr|mrs|dr)?\.?\s*'
    r'|patientms\.\s*'
    r'|name\s*[:\-]\s*)',
    re.IGNORECASE
)

# A name candidate: 2–5 consecutive ALLCAPS or Title-Case words
_NAME_CANDIDATE = re.compile(
    r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){1,4})',
)

# Words that look like names but are actually report keywords
_NAME_BLOCKLIST = {
    "NORMAL", "RANGE", "RESULT", "REPORT", "TEST", "MALE", "FEMALE",
    "BLOOD", "SPECIMEN", "COLLECTION", "DATE", "PRINTED", "INDOOR",
    "OUTDOOR", "OUT", "DOOR", "TYPE", "GENDER", "AGE", "PATIENT",
    "MODERN", "DIAGNOSTIC", "CENTRE", "UNIT", "LIMITED", "LTD",
    "HAEMATOLOGY", "HEMATOLOGY", "ANALYSIS", "REFERRED", "PROF",
    "TOTAL", "COUNT", "DIFFERENTIAL", "AUTOANALYZER", "METHOD",
}

def _extract_name(text: str) -> Optional[str]:
    # Strategy 1: look for explicit Patient: / PatientMS. prefix
    match = _NAME_PREFIX.search(text)
    if match:
        after = text[match.end():]
        # Grab up to 5 words that start with capital letters
        words = []
        for part in after.split():
            part = re.sub(r'[^\w]', '', part)   # strip trailing punctuation
            if re.match(r'^[A-Z][A-Za-z]+$', part) and part.upper() not in _NAME_BLOCKLIST:
                words.append(part)
            else:
                break
            if len(words) == 5:
                break
        if len(words) >= 2:
            return " ".join(words)

    # Strategy 2: scan for a run of 2–4 ALL-CAPS words not in blocklist
    all_caps_run = re.compile(r'\b([A-Z]{2,})(?:\s+([A-Z]{2,})){1,3}\b')
    for m in all_caps_run.finditer(text):
        candidate = m.group(0)
        words = candidate.split()
        if all(w not in _NAME_BLOCKLIST for w in words):
            return candidate.title()

    return None


# ─── Age extraction ───────────────────────────────────────────────────────────

_AGE_PATTERNS = [
    re.compile(r'\bAge\s*[:\-]?\s*(\d{1,3})\s*Y', re.IGNORECASE),       # Age:50Y  Age: 50Y
    re.compile(r'\b(\d{1,3})\s*(?:years?|yrs?)\s*old\b', re.IGNORECASE), # 50 years old
    re.compile(r'\bage\s*[:\-]?\s*(\d{1,3})\b', re.IGNORECASE),          # age: 50
]

def _extract_age(text: str) -> Optional[int]:
    for pattern in _AGE_PATTERNS:
        m = pattern.search(text)
        if m:
            age = int(m.group(1))
            if 0 < age < 130:   # sanity check
                return age
    return None


# ─── Gender extraction ────────────────────────────────────────────────────────

_GENDER_PATTERNS = [
    (re.compile(r'\bGender\s*[:\-]?\s*(Male|Female)\b', re.IGNORECASE), 1),
    (re.compile(r'\bSex\s*[:\-]?\s*(Male|Female)\b',    re.IGNORECASE), 1),
    # Title prefix as fallback
    (re.compile(r'\bPatient\w*\.\s*(MS|MRS)\b',          re.IGNORECASE), None),  # → female
    (re.compile(r'\bPatient\w*\.\s*(MR)\b',              re.IGNORECASE), None),  # → male
]

def _extract_gender(text: str) -> str:
    # Explicit Gender: field
    for pattern, group in _GENDER_PATTERNS[:2]:
        m = pattern.search(text)
        if m:
            return m.group(group).lower()

    # Title prefix fallback
    ms_mrs = re.search(r'\b(MS|MRS)\b\.?\s+[A-Z]', text, re.IGNORECASE)
    if ms_mrs:
        return "female"
    mr = re.search(r'\bMR\b\.?\s+[A-Z]', text, re.IGNORECASE)
    if mr:
        return "male"

    return "unknown"


# ─── Date extraction ──────────────────────────────────────────────────────────

_DATE_PATTERNS = [
    # CollectionDate:16/07/23 — negative lookahead stops year eating time digits
    re.compile(r'(?:Collection\s*Date|Collected|Collection)\s*[:\-]?\s*'
               r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})(?!\d)', re.IGNORECASE),
    # Generic dd/mm/yy anywhere
    re.compile(r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})\b'),
]

def _extract_date(text: str) -> Optional[str]:
    for pattern in _DATE_PATTERNS:
        m = pattern.search(text)
        if m:
            day, month, year = m.group(1), m.group(2), m.group(3)
            # Guard against OCR gluing year+time: "2309" from "23"+"09:37"
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


# ─── Public API ───────────────────────────────────────────────────────────────

def extract_header(raw: str, lab_results: Optional[list] = None) -> PatientHeader:
    """
    Extract patient metadata from raw OCR text.

    Args:
        raw:         Raw OCR or report text (before any cleaning)
        lab_results: Optional list of LabResult dicts from the NER extractor.
                     If provided, used to infer report_type from actual tests found.
                     If None, report_type will be None.

    Returns:
        PatientHeader dataclass
    """
    name            = _extract_name(raw)
    age_years       = _extract_age(raw)
    gender          = _extract_gender(raw)
    collection_date = _extract_date(raw)

    # Infer report type from NER results if available
    report_type = None
    if lab_results is not None:
        test_names = [r["test"] for r in lab_results]
        report_type = infer_report_type(test_names)

    return PatientHeader(
        name=name,
        age_years=age_years,
        gender=gender,
        report_type=report_type,
        collection_date=collection_date,
    )