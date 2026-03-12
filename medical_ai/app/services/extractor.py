"""
extractor.py  ─  Unified Medical Report Extractor
══════════════════════════════════════════════════
Category → extractor routing:
  LAB            → regex pipeline only (deterministic, zero API cost)
                   LLM explanations added later by report_assembler
  IMAGING        → extract_report() via LLM  |  keyword fallback
  CLINICAL       → extract_report() via LLM  |  keyword fallback
  SPECIALIST     → extract_report() via LLM  |  keyword fallback
  PATHOLOGY      → extract_report() via LLM  |  keyword fallback
  ADMINISTRATIVE → extract_report() via LLM  |  keyword fallback

Single unified entry point:
    results = extract(text, category, sub_type, gender)

LAB result shape (unchanged):
    { result_type, test, value, unit, status }

Non-LAB result shape (one report dict per document):
    {
        summary, tests_analysis, risk_level, advice,
        raw_text, metadata: { gender, confidence }
        # metadata is internal — stripped from final output by assembler
    }

Backward compatibility:
    extract_lab_results(text, gender, as_entities)  ← unchanged
    extract_conditions(text)                         ← unchanged
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Optional

from services.known_tests    import KNOWN_TESTS
from services.llm_extractor  import extract_report


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 - DATA MODELS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class MedicalEntity:
    text:        str
    entity_type: str
    severity:    str
    explanation: str
    value:       str
    unit:        str


@dataclass
class LabResult:
    test:   str
    value:  float
    unit:   str
    status: str

    _STATUS_TO_SEVERITY = {
        "CRITICAL_HIGH": "CRITICAL",
        "CRITICAL_LOW":  "CRITICAL",
        "HIGH":          "MODERATE",
        "LOW":           "MODERATE",
        "NORMAL":        "INFO",
    }

    def to_dict(self) -> dict:
        return {"result_type": "LAB", **asdict(self)}

    def to_entity(self) -> MedicalEntity:
        severity    = self._STATUS_TO_SEVERITY.get(self.status, "INFO")
        explanation = (
            f"{self.test} is {self.status.replace('_', ' ').lower()}"
            f" ({self.value} {self.unit})"
        ).strip()
        return MedicalEntity(
            text=self.test, entity_type="LAB_VALUE",
            severity=severity, explanation=explanation,
            value=str(self.value), unit=self.unit,
        )


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 - LAB PIPELINE  (regex — unchanged)
# ══════════════════════════════════════════════════════════════════════════════

_NOISE_SUB = [
    re.compile(p, re.IGNORECASE) for p in [
        r'[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}',
        r'https?://\S+',
        r'www\.\S+',
        r'helpline[\d,\s:]+',
        r'web\s*:\s*\S+',
        r'e-?mail\s*:\s*\S+',
        r'inv\.?\s*no\s*:\s*[\w\-]+',
        r'patient\s*(id|ms)\s*[:\.]?\s*[\w.\-]+',
        r'collection\s*date\s*:\s*[\w:/]+',
        r'refd?\s*by\s*\w+\.\s*\w+\.\s*\w+[^%\d]*?(?=[A-Z]{2,}|\Z)',
        r'(mbbs|ms\(ortho\)|frcs|fcps|hand\s*&\s*micro\s+surgeon)',
        r'specimen\s*:\s*\w+',
        r'type\s*:\s*\w+',
        r'out\s+door',
        r'printed?\s*on\s*:\s*[\w\-:]+',
        r'haematology|hematology',
        r'analysis\s+report',
        r'differential\s+count\s+of\s+\w+',
        r'total\s+count\s+\w+\s+count\s+of\s+\w+',
        r'test\s+name|normal\s+range',
        r'centre\s+ltd',
        r'diagnostic\s+unit',
        r'(dhanmondi|dhaka)',
        r'r/a',
        r'(autoanalyzer|autoanalyser)\s+method',
        r'(male|female|child|adult|aduit|wome|men|mae|adu|adut|mmin|mmn|sth|sthr)[\d\s\-.,()x^/:%a-z]*',
        r'(?<!\d)\d+\.?\d*\s*[-]\s*\d+\.?\d*(?!\d)',
        r'\[\w+\]',
        r'IG%|NRBC%?',
        r'\d{5,}',
        r'\(fi\)|\(blood\)',
    ]
]

_OCR_FIXES = [
    (re.compile(r'\bLymphocyi[eo]s\b',     re.IGNORECASE), 'Lymphocytes'),
    (re.compile(r'\bMonocyi[eo]s\b',        re.IGNORECASE), 'Monocytes'),
    (re.compile(r'\bEosinophil[ily]+s?\b',  re.IGNORECASE), 'Eosinophils'),
    (re.compile(r'\bPlatlets\b',            re.IGNORECASE), 'Platelets'),
    (re.compile(r'\bRBC\s*\(Blood\)',       re.IGNORECASE), 'RBC'),
    (re.compile(r'\bHCT\s*/\s*PCV\b',      re.IGNORECASE), 'HCT/PCV'),
    (re.compile(r'\bRDW-SD\s*\(\w*\)',     re.IGNORECASE), 'RDW-SD'),
    (re.compile(r'\bRDW-CV\s*\([^)]*\)',   re.IGNORECASE), 'RDW-CV'),
]


def clean_text(raw: str) -> str:
    text = raw
    for pattern, replacement in _OCR_FIXES:
        text = pattern.sub(replacement, text)
    for pattern in _NOISE_SUB:
        text = pattern.sub(' ', text)
    return re.sub(r'\s{2,}', ' ', text).strip()


def compute_status(value: float, config: dict, gender: str = "unknown") -> str:
    g = gender.lower()
    low, high = config.get(g if g in ("male", "female") else "female", (None, None))
    critical  = config.get("critical")
    if critical:
        crit_low, crit_high = critical
        if crit_low  is not None and value < crit_low:  return "CRITICAL_LOW"
        if crit_high is not None and value > crit_high: return "CRITICAL_HIGH"
    if low  is not None and value < low:  return "LOW"
    if high is not None and value > high: return "HIGH"
    return "NORMAL"


_KEYS_SORTED = sorted(KNOWN_TESTS.keys(), key=len, reverse=True)
_TEST_RE = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in _KEYS_SORTED) + r')\b'
    r'(?:\s*\([^)]*\))?'
    r'[\s:/\-]*'
    r'([\d]+(?:[.,]\d+)?)'
    r'\s*'
    r'(g/dL|gm/dl|mg/dL|mmol/L|mEq/L|U/L|IU/L|fL|pg|%|mm/hr|mIU/L|sec'
    r'|x10\^9/L|x10\^12/L|kg/m2|nmol/L|pmol/L|ng/mL|ng/dL|ng/L'
    r'|ug/dL|ug/mL|uIU/mL|umol/L|IU/mL|mmHg|bpm|breaths/min|cells/uL)?',
    re.IGNORECASE,
)


def extract_lab_results(
    text: str,
    gender: str = "unknown",
    as_entities: bool = False,
) -> list:
    """
    Regex pipeline for LAB reports. Signature unchanged.
    Returns list[dict] or list[MedicalEntity] (as_entities=True).
    """
    cleaned = clean_text(text)
    results = []
    seen: set[str] = set()

    for match in _TEST_RE.finditer(cleaned):
        key          = match.group(1).upper().strip()
        raw_value    = match.group(2).replace(",", ".")
        matched_unit = match.group(3) or ""

        if key in seen:
            continue
        seen.add(key)

        config = KNOWN_TESTS.get(key)
        if not config:
            continue

        try:
            value = float(raw_value)
        except ValueError:
            continue

        unit   = matched_unit or config.get("unit", "")
        status = compute_status(value, config, gender)
        results.append(LabResult(test=config["name"], value=value, unit=unit, status=status))

    if as_entities:
        return [r.to_entity() for r in results]
    return [r.to_dict() for r in results]


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 - KEYWORD FALLBACKS  (used only when LLM is unavailable)
# ══════════════════════════════════════════════════════════════════════════════

_SEVERITY_WORDS: dict[str, list[str]] = {
    "SEVERE":   ["severe", "significant", "extensive", "frank", "marked",
                 "complete", "total", "advanced", "critical", "massive",
                 "gross", "profound", "high-grade", "poorly differentiated"],
    "MODERATE": ["moderate", "partial", "compromised", "incomplete",
                 "localised", "localized", "limited", "reduced",
                 "bilateral", "multifocal", "moderately differentiated"],
    "MILD":     ["mild", "minimal", "slight", "early", "minor", "small",
                 "subtle", "trace", "widening", "borderline", "low-grade",
                 "well differentiated"],
}

_NEGATION_PHRASES = [
    "no ", "not ", "none ", "without ", "absence of", "free of",
    "not present", "not within", "outside the field", "not in the field",
    "not identified", "not visualis", "not visualiz",
    "unremarkable", "within normal", "no evidence", "no abnormal",
    "no acute", "no active",
]


def _detect_severity(text: str) -> Optional[str]:
    t = text.lower()
    for level, words in _SEVERITY_WORDS.items():
        if any(w in t for w in words):
            return level
    return None


def _is_negated(text: str) -> bool:
    return any(p in text.lower() for p in _NEGATION_PHRASES)


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 10]


def _sentences_with(text: str, keywords: list[str]) -> list[str]:
    return [s for s in _split_sentences(text) if any(kw.lower() in s.lower() for kw in keywords)]


def _keyword_extract(text: str, report_type: str, sub_type: str, gender: str = "unknown") -> dict:
    """
    Minimal keyword fallback when LLM is unavailable.
    Returns the same shape as extract_report() (tests_analysis format).
    Each sentence that looks like a finding becomes a bare tests_analysis entry.
    """
    import logging
    logging.getLogger(__name__).warning(
        "LLM unavailable for %s/%s — using keyword fallback", report_type, sub_type
    )

    _GENERAL_KEYWORDS = [
        "finding", "noted", "revealed", "evident", "present", "identified",
        "consolidation", "opacity", "fracture", "effusion", "impression",
        "diagnosis", "complaint", "examination", "medication", "prescribed",
    ]

    finding_sentences = list(dict.fromkeys(
        s for s in _split_sentences(text)
        if any(kw in s.lower() for kw in _GENERAL_KEYWORDS)
    ))

    # Wrap each sentence as a bare tests_analysis entry
    tests_analysis = [
        {
            "test_name":           f"Finding {i+1}",
            "value":               "",
            "unit":                "",
            "reference_range":     "",
            "status":              "Unknown",
            "keyword_explanation": "",
            "result_explanation":  sentence,
        }
        for i, sentence in enumerate(finding_sentences)
    ]

    advice_sentences = [
        s for s in _split_sentences(text)
        if any(w in s.lower() for w in ["recommend", "follow up", "follow-up", "refer", "advised"])
    ]

    return {
        "summary":        "",
        "tests_analysis": tests_analysis,
        "risk_level":     "Unknown",
        "advice":         " ".join(advice_sentences),
        "raw_text":       text,
        "metadata":       {"gender": gender, "confidence": "LOW"},
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 - CONDITIONS EXTRACTOR  (unchanged public API)
# ══════════════════════════════════════════════════════════════════════════════

def load_spacy_model():
    try:
        import spacy
        return spacy.load("en_ner_bc5cdr_md")
    except Exception:
        return None


NLP = load_spacy_model()

CRITICAL_TERMS = {
    "sepsis", "cardiac arrest", "stroke", "infarction", "embolism",
    "haemorrhage", "hemorrhage", "anaphylaxis", "respiratory failure",
    "renal failure", "liver failure", "meningitis", "encephalitis",
    "malignancy", "carcinoma", "leukemia", "lymphoma", "metastasis",
    "thrombosis", "pulmonary edema", "eclampsia", "DIC",
}
MODERATE_TERMS = {
    "hypertension", "diabetes", "pneumonia", "anemia", "infection",
    "inflammation", "fibrosis", "stenosis", "arrhythmia", "tachycardia",
    "bradycardia", "hyperlipidemia", "hypothyroidism", "hyperthyroidism",
    "asthma", "copd", "hepatitis", "pancreatitis", "appendicitis",
}


def _condition_severity(term: str) -> str:
    t = term.lower()
    if any(c in t for c in CRITICAL_TERMS):  return "CRITICAL"
    if any(m in t for m in MODERATE_TERMS):  return "MODERATE"
    return "INFO"


def extract_conditions(text: str) -> list[dict]:
    """
    Detect named medical conditions via spaCy NER or keyword scan.
    Returns: list of { condition, severity }. Signature unchanged.
    """
    found, seen = [], set()

    if NLP:
        for ent in NLP(text).ents:
            if ent.label_ == "DISEASE":
                name = ent.text.lower()
                if name not in seen:
                    seen.add(name)
                    found.append({"condition": ent.text.title(),
                                  "severity":  _condition_severity(ent.text)})
    else:
        for cond in CRITICAL_TERMS | MODERATE_TERMS:
            if re.search(r'\b' + re.escape(cond) + r'\b', text, re.IGNORECASE):
                if cond not in seen:
                    seen.add(cond)
                    found.append({"condition": cond.title(),
                                  "severity":  _condition_severity(cond)})
    return found


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 - UNIFIED DISPATCHER
#
# LAB   → regex only (report_assembler handles LLM explanations separately)
# Other → extract_report() (LLM)  |  _keyword_extract() fallback
# ══════════════════════════════════════════════════════════════════════════════

def extract(
    text:     str,
    category: str,
    sub_type: str = "UNKNOWN",
    gender:   str = "unknown",
    language: str = "en",
) -> dict | list[dict]:
    """
    Unified entry point called by report_assembler.py.

    Returns:
      LAB     → list[dict]  each { result_type, test, value, unit, status }
      Non-LAB → dict        { summary, tests_analysis, risk_level, advice,
                              raw_text, metadata }
      metadata is internal — assembler strips it before final output.
    """
    primary = category.split(" + ")[0].strip().upper()

    # ── LAB: regex pipeline only ─────────────────────────────────────────────
    # LLM explanations are added later by report_assembler via extract_report().
    # Running extract_lab_values() here caused a redundant LLM call → timeouts.
    if primary == "LAB":
        return extract_lab_results(text, gender=gender)

    # ── UNKNOWN ───────────────────────────────────────────────────────────────
    if primary == "UNKNOWN":
        return {
            "summary":        "Document category could not be determined.",
            "tests_analysis": [],
            "risk_level":     "Unknown",
            "advice":         "",
            "raw_text":       text,
            "metadata":       {"gender": gender, "confidence": "LOW"},
        }

    # ── Non-LAB: LLM first, keyword fallback if LLM unavailable ──────────────
    report = extract_report(text, report_type=primary, sub_type=sub_type, gender=gender, language=language)

    if report["metadata"]["confidence"] == "LOW":
        # LLM failed — use keyword fallback but keep raw_text from extract_report
        return _keyword_extract(text, report_type=primary, sub_type=sub_type, gender=gender)

    return report