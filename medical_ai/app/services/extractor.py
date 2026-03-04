"""
Medical NER - Clean Lab Result Extractor
Output format: { test, value, unit, status }
Status: NORMAL | HIGH | LOW | CRITICAL_HIGH | CRITICAL_LOW | UNKNOWN

Key improvements over v1:
  - Metadata/header lines stripped before parsing (no more address/phone false positives)
  - Each known test has explicit normal ranges (gender-aware)
  - LAB_PATTERN anchored to known test names only — no greedy false matches
  - Status computed by comparing value to range
  - spaCy hook preserved for conditions (diseases/medications)
"""

import re
from dataclasses import dataclass, asdict


# ─── Output Model ─────────────────────────────────────────────────────────────

@dataclass
class MedicalEntity:
    """
    Backward-compatible shape for existing API endpoints that use MedicalEntityOut.
    Maps the new { test, value, unit, status } fields to the old schema.
    """
    text: str           # test name  → was: matched text span
    entity_type: str    # always "LAB_VALUE"
    severity: str       # maps status → CRITICAL | MODERATE | MILD | INFO
    explanation: str    # human-readable status sentence
    value: str          # numeric value as string
    unit: str


@dataclass
class LabResult:
    test: str           # Human-readable test name
    value: float        # Numeric value
    unit: str           # e.g. g/dL, %, x10^9/L
    status: str         # NORMAL | HIGH | LOW | CRITICAL_HIGH | CRITICAL_LOW

    # ── status → severity mapping ──────────────────────────────────────────
    _STATUS_TO_SEVERITY = {
        "CRITICAL_HIGH": "CRITICAL",
        "CRITICAL_LOW":  "CRITICAL",
        "HIGH":          "MODERATE",
        "LOW":           "MODERATE",
        "NORMAL":        "INFO",
    }

    def to_dict(self) -> dict:
        return asdict(self)

    def to_entity(self) -> MedicalEntity:
        """
        Convert to the MedicalEntity shape expected by existing endpoint code:

            MedicalEntityOut(
                text=e.text,
                entity_type=e.entity_type,
                severity=e.severity,
                explanation=e.explanation,
                value=e.value,
                unit=e.unit,
            )
        """
        severity = self._STATUS_TO_SEVERITY.get(self.status, "INFO")
        explanation = f"{self.test} is {self.status.replace('_', ' ').lower()} ({self.value} {self.unit})".strip()
        return MedicalEntity(
            text=self.test,
            entity_type="LAB_VALUE",
            severity=severity,
            explanation=explanation,
            value=str(self.value),
            unit=self.unit,
        )


# ─── Known Test Registry ──────────────────────────────────────────────────────
# Format:
#   "MATCH_KEY": {
#       "name":     display name,
#       "unit":     fallback unit if report doesn't include one,
#       "male":     (low, high),
#       "female":   (low, high),
#       "critical": (critical_low, critical_high)  — None means no threshold
#   }

KNOWN_TESTS = {

    # ── Complete Blood Count ──────────────────────────────────────────────────
    "HAEMOGLOBIN": {
        "name": "Haemoglobin", "unit": "g/dL",
        "male": (14.0, 18.0), "female": (12.0, 16.0),
        "critical": (7.0, 20.0),
    },
    "HEMOGLOBIN": {
        "name": "Haemoglobin", "unit": "g/dL",
        "male": (14.0, 18.0), "female": (12.0, 16.0),
        "critical": (7.0, 20.0),
    },
    "HB": {
        "name": "Haemoglobin", "unit": "g/dL",
        "male": (14.0, 18.0), "female": (12.0, 16.0),
        "critical": (7.0, 20.0),
    },
    "WBC": {
        "name": "WBC (Total)", "unit": "x10^9/L",
        "male": (4.0, 11.0), "female": (4.0, 11.0),
        "critical": (2.0, 30.0),
    },
    "RBC": {
        "name": "RBC", "unit": "x10^12/L",
        "male": (4.5, 5.5), "female": (3.8, 5.0),
        "critical": (2.0, 7.0),
    },
    "PLATELETS": {
        "name": "Platelets", "unit": "x10^9/L",
        "male": (150.0, 400.0), "female": (150.0, 400.0),
        "critical": (50.0, 1000.0),
    },
    "PLT": {
        "name": "Platelets", "unit": "x10^9/L",
        "male": (150.0, 400.0), "female": (150.0, 400.0),
        "critical": (50.0, 1000.0),
    },
    "HCT": {
        "name": "HCT/PCV", "unit": "%",
        "male": (40.0, 54.0), "female": (37.0, 47.0),
        "critical": (20.0, 60.0),
    },
    "PCV": {
        "name": "HCT/PCV", "unit": "%",
        "male": (40.0, 54.0), "female": (37.0, 47.0),
        "critical": (20.0, 60.0),
    },
    "HCT/PCV": {
        "name": "HCT/PCV", "unit": "%",
        "male": (40.0, 54.0), "female": (37.0, 47.0),
        "critical": (20.0, 60.0),
    },
    "MCV": {
        "name": "MCV", "unit": "fL",
        "male": (83.0, 101.0), "female": (83.0, 101.0),
        "critical": None,
    },
    "MCH": {
        "name": "MCH", "unit": "pg",
        "male": (27.0, 32.0), "female": (27.0, 32.0),
        "critical": None,
    },
    "MCHC": {
        "name": "MCHC", "unit": "g/dL",
        "male": (31.5, 34.5), "female": (31.5, 34.5),
        "critical": (20.0, 40.0),
    },
    "RDW-CV": {
        "name": "RDW-CV", "unit": "%",
        "male": (11.6, 14.0), "female": (11.6, 14.0),
        "critical": None,
    },
    "RDW-SD": {
        "name": "RDW-SD", "unit": "fL",
        "male": (39.0, 46.0), "female": (39.0, 46.0),
        "critical": None,
    },
    "MPV": {
        "name": "MPV", "unit": "fL",
        "male": (7.4, 10.4), "female": (7.4, 10.4),
        "critical": None,
    },
    "PCT": {
        "name": "PCT", "unit": "%",
        "male": (0.20, 0.50), "female": (0.20, 0.50),
        "critical": None,
    },
    "PDW": {
        "name": "PDW", "unit": "%",
        "male": (10.0, 18.0), "female": (10.0, 18.0),
        "critical": None,
    },

    # ── Differential WBC ─────────────────────────────────────────────────────
    "NEUTROPHILS": {
        "name": "Neutrophils", "unit": "%",
        "male": (40.0, 70.0), "female": (40.0, 70.0),
        "critical": None,
    },
    "LYMPHOCYTES": {
        "name": "Lymphocytes", "unit": "%",
        "male": (20.0, 46.0), "female": (20.0, 46.0),
        "critical": None,
    },
    "MONOCYTES": {
        "name": "Monocytes", "unit": "%",
        "male": (2.0, 8.0), "female": (2.0, 8.0),
        "critical": None,
    },
    "EOSINOPHILS": {
        "name": "Eosinophils", "unit": "%",
        "male": (1.0, 6.0), "female": (1.0, 6.0),
        "critical": None,
    },
    "BASOPHILS": {
        "name": "Basophils", "unit": "%",
        "male": (0.0, 1.0), "female": (0.0, 1.0),
        "critical": None,
    },

    # ── Inflammatory Markers ──────────────────────────────────────────────────
    "ESR": {
        "name": "ESR", "unit": "mm/hr",
        "male": (0.0, 10.0), "female": (0.0, 20.0),
        "critical": None,
    },
    "CRP": {
        "name": "CRP", "unit": "mg/L",
        "male": (0.0, 10.0), "female": (0.0, 10.0),
        "critical": (None, 100.0),
    },

    # ── Metabolic ────────────────────────────────────────────────────────────
    "GLUCOSE": {
        "name": "Glucose (Fasting)", "unit": "mg/dL",
        "male": (70.0, 100.0), "female": (70.0, 100.0),
        "critical": (40.0, 500.0),
    },
    "FBS": {
        "name": "Fasting Blood Sugar", "unit": "mg/dL",
        "male": (70.0, 100.0), "female": (70.0, 100.0),
        "critical": (40.0, 500.0),
    },
    "HBA1C": {
        "name": "HbA1c", "unit": "%",
        "male": (4.0, 5.7), "female": (4.0, 5.7),
        "critical": (None, 10.0),
    },
    "CREATININE": {
        "name": "Creatinine", "unit": "mg/dL",
        "male": (0.7, 1.2), "female": (0.5, 1.0),
        "critical": (None, 10.0),
    },
    "UREA": {
        "name": "Blood Urea", "unit": "mg/dL",
        "male": (15.0, 45.0), "female": (15.0, 45.0),
        "critical": (None, 200.0),
    },
    "BUN": {
        "name": "BUN", "unit": "mg/dL",
        "male": (7.0, 20.0), "female": (7.0, 20.0),
        "critical": (None, 100.0),
    },
    "CHOLESTEROL": {
        "name": "Total Cholesterol", "unit": "mg/dL",
        "male": (0.0, 200.0), "female": (0.0, 200.0),
        "critical": (None, 300.0),
    },
    "LDL": {
        "name": "LDL Cholesterol", "unit": "mg/dL",
        "male": (0.0, 100.0), "female": (0.0, 100.0),
        "critical": None,
    },
    "HDL": {
        "name": "HDL Cholesterol", "unit": "mg/dL",
        "male": (40.0, 999.0), "female": (50.0, 999.0),
        "critical": None,
    },
    "TRIGLYCERIDES": {
        "name": "Triglycerides", "unit": "mg/dL",
        "male": (0.0, 150.0), "female": (0.0, 150.0),
        "critical": None,
    },

    # ── Liver ────────────────────────────────────────────────────────────────
    "ALT": {
        "name": "ALT", "unit": "U/L",
        "male": (7.0, 56.0), "female": (7.0, 45.0),
        "critical": (None, 1000.0),
    },
    "AST": {
        "name": "AST", "unit": "U/L",
        "male": (10.0, 40.0), "female": (10.0, 35.0),
        "critical": (None, 1000.0),
    },
    "ALP": {
        "name": "ALP", "unit": "U/L",
        "male": (44.0, 147.0), "female": (44.0, 147.0),
        "critical": None,
    },
    "BILIRUBIN": {
        "name": "Total Bilirubin", "unit": "mg/dL",
        "male": (0.2, 1.2), "female": (0.2, 1.2),
        "critical": (None, 15.0),
    },

    # ── Thyroid ──────────────────────────────────────────────────────────────
    "TSH": {
        "name": "TSH", "unit": "mIU/L",
        "male": (0.4, 4.0), "female": (0.4, 4.0),
        "critical": (0.1, 10.0),
    },

    # ── Electrolytes ─────────────────────────────────────────────────────────
    "SODIUM": {
        "name": "Sodium (Na)", "unit": "mEq/L",
        "male": (136.0, 145.0), "female": (136.0, 145.0),
        "critical": (120.0, 160.0),
    },
    "POTASSIUM": {
        "name": "Potassium (K)", "unit": "mEq/L",
        "male": (3.5, 5.0), "female": (3.5, 5.0),
        "critical": (2.5, 6.5),
    },
    "CALCIUM": {
        "name": "Calcium", "unit": "mg/dL",
        "male": (8.5, 10.5), "female": (8.5, 10.5),
        "critical": (6.0, 13.0),
    },

    # ── Clotting ─────────────────────────────────────────────────────────────
    "INR": {
        "name": "INR", "unit": "",
        "male": (0.8, 1.2), "female": (0.8, 1.2),
        "critical": (None, 5.0),
    },
    "PT": {
        "name": "Prothrombin Time", "unit": "sec",
        "male": (11.0, 13.5), "female": (11.0, 13.5),
        "critical": None,
    },

    # ── Vitals / Other ───────────────────────────────────────────────────────
    "SPO2": {
        "name": "SpO2", "unit": "%",
        "male": (95.0, 100.0), "female": (95.0, 100.0),
        "critical": (88.0, None),
    },
    "BMI": {
        "name": "BMI", "unit": "kg/m²",
        "male": (18.5, 24.9), "female": (18.5, 24.9),
        "critical": None,
    },
}


# ─── Noise token cleaner ─────────────────────────────────────────────────────
# Strips header/metadata TOKENS in-place. Works on single-line OCR output.
# Does NOT drop whole lines (that's what broke things before).

_NOISE_SUB = [
    re.compile(p, re.IGNORECASE) for p in [
        r'[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}',   # emails
        r'https?://\S+',                                  # URLs
        r'www\.\S+',                                      # bare URLs
        r'helpline[\d,\s:]+',                         # Helpline:10652...
        r'web\s*:\s*\S+',                               # Web:www...
        r'e-?mail\s*:\s*\S+',                           # E-mail:...
        r'inv\.?\s*no\s*:\s*[\w\-]+',                   # Inv.No:2307-22003
        r'patient\s*(id|ms)\s*[:\.]?\s*[\w.\-]+',       # Patient Id / PatientMS
        r'collection\s*date\s*:\s*[\w:/]+',             # CollectionDate:16/07/23...
        r'refd?\s*by\s*\w+\.\s*\w+\.\s*\w+[^%\d]*?(?=[A-Z]{2,}|\Z)',  # Refd by Prof...Surgeon
        r'(mbbs|ms\(ortho\)|frcs|fcps|hand\s*&\s*micro\s+surgeon)',
        r'specimen\s*:\s*\w+',
        r'type\s*:\s*\w+',
        r'out\s+door',
        r'printed?\s*on\s*:\s*[\w\-:]+',
        r'haematology|hematology',
        r'analysis\s+report',
        r'differential\s+count\s+of\s+\w+',
        r'total\s+count\s+\w+\s+count\s+of\s+\w+',   # "Total Count Joal Countof WBC"
        r'test\s+name|normal\s+range',
        r'centre\s+ltd',
        r'diagnostic\s+unit',
        r'(dhanmondi|dhaka)',
        r'r/a',
        r'(autoanalyzer|autoanalyser)\s+method',
        # Inline gender reference ranges glued to values: "Male14.00-18.00Female12.00"
        r'(male|female|child|adult|aduit|wome|men|mae|adu|adut|mmin|mmn|sth|sthr)[\d\s\-.,()x^/:%a-z]*',
        # Standalone numeric ranges: "4.0-11.0" "150.0-400.0" "83-101"
        r'(?<!\d)\d+\.?\d*\s*[-–]\s*\d+\.?\d*(?!\d)',
        r'\[\w+\]',                      # [HN20230700010425]
        r'IG%|NRBC%?',           # IG% NRBC% — not in our registry
        r'\d{5,}',                   # long standalone number strings
        r'\(fi\)|\(blood\)',             # (fi) (Blood) OCR artifacts
    ]
]

# OCR commonly misspells test names — normalize before matching
_OCR_FIXES = [
    # Fuzzy OCR misspelling fixes - run BEFORE noise removal
    (re.compile(r'\bLymphocyi[eo]s\b',      re.IGNORECASE), 'Lymphocytes'),
    (re.compile(r'\bMonocyi[eo]s\b',         re.IGNORECASE), 'Monocytes'),
    (re.compile(r'\bEosinophil[ily]+s?\b',   re.IGNORECASE), 'Eosinophils'),
    (re.compile(r'\bPlatlets\b',              re.IGNORECASE), 'Platelets'),
    (re.compile(r'\bRBC\s*\(Blood\)',         re.IGNORECASE), 'RBC'),
    (re.compile(r'\bHCT\s*/\s*PCV\b',        re.IGNORECASE), 'HCT/PCV'),
    (re.compile(r'\bRDW-SD\s*\(\w*\)',       re.IGNORECASE), 'RDW-SD'),
    (re.compile(r'\bRDW-CV\s*\([^)]*\)',      re.IGNORECASE), 'RDW-CV'),
]


def clean_text(raw: str) -> str:
    """
    Normalize OCR typos then strip noise tokens.
    Safe for single-line concatenated OCR output.
    """
    text = raw
    # 1. Fix OCR misspellings first
    for pattern, replacement in _OCR_FIXES:
        text = pattern.sub(replacement, text)
    # 2. Remove noise tokens
    for pattern in _NOISE_SUB:
        text = pattern.sub(' ', text)
    # 3. Collapse whitespace
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text


# ─── Status computation ───────────────────────────────────────────────────────

def compute_status(value: float, config: dict, gender: str = "unknown") -> str:
    g = gender.lower()
    low, high = config.get(g if g in ("male", "female") else "female", (None, None))
    critical = config.get("critical")

    if critical:
        crit_low, crit_high = critical
        if crit_low is not None and value < crit_low:
            return "CRITICAL_LOW"
        if crit_high is not None and value > crit_high:
            return "CRITICAL_HIGH"

    if low is not None and value < low:
        return "LOW"
    if high is not None and value > high:
        return "HIGH"

    return "NORMAL"


# ─── Compiled matcher ─────────────────────────────────────────────────────────
# Keys sorted longest-first so multi-word keys (e.g. HCT/PCV) match before substrings.

_KEYS_SORTED = sorted(KNOWN_TESTS.keys(), key=len, reverse=True)
_TEST_RE = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in _KEYS_SORTED) + r')\b'
    # Skip noise between test name and value: spaces, parens, brackets, colons, slashes
    # Also skip full words-in-parens like '(Autoanalyzer Method)' or '(%)'
    r'(?:\s*\([^)]*\))?'   # optional (anything) block e.g. (Autoanalyzer Method)
    r'[\s:/\-]*'
    r'([\d]+(?:[.,]\d+)?)'
    r'\s*'
    r'(g/dL|gm/dl|mg/dL|mmol/L|mEq/L|U/L|IU/L|fL|pg|%|mm/hr|mIU/L|sec|x10\^9/L|x10\^12/L|kg/m²)?',
    re.IGNORECASE
)


# ─── Public API ───────────────────────────────────────────────────────────────

def extract_lab_results(
    text: str,
    gender: str = "unknown",
    as_entities: bool = False,
) -> list[dict] | list[MedicalEntity]:
    """
    Parse raw report text and return structured lab results.

    Args:
        text:        Raw OCR or copy-pasted report text
        gender:      "male" | "female" | "unknown"
        as_entities: If True, return list[MedicalEntity] compatible with
                     existing endpoint code that uses MedicalEntityOut.
                     If False (default), return list[dict] with clean
                     { test, value, unit, status } shape.

    Endpoint usage (no changes needed in your route):
        entities = extract_lab_results(text, gender=gender, as_entities=True)
    """
    cleaned = clean_text(text)
    results: list[LabResult] = []
    seen: set[str] = set()

    for match in _TEST_RE.finditer(cleaned):
        key = match.group(1).upper().strip()
        raw_value = match.group(2).replace(",", ".")
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

        unit = matched_unit or config.get("unit", "")
        status = compute_status(value, config, gender)

        results.append(LabResult(
            test=config["name"],
            value=value,
            unit=unit,
            status=status,
        ))

    if as_entities:
        return [r.to_entity() for r in results]
    return [r.to_dict() for r in results]


# ─── spaCy condition extraction (optional, unchanged hook) ────────────────────

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
    if any(c in t for c in CRITICAL_TERMS):
        return "CRITICAL"
    if any(m in t for m in MODERATE_TERMS):
        return "MODERATE"
    return "INFO"


def extract_conditions(text: str) -> list[dict]:
    """
    Detect named medical conditions.
    Returns: list of { condition, severity }
    """
    found, seen = [], set()

    if NLP:
        for ent in NLP(text).ents:
            if ent.label_ == "DISEASE":
                name = ent.text.lower()
                if name not in seen:
                    seen.add(name)
                    found.append({"condition": ent.text.title(),
                                  "severity": _condition_severity(ent.text)})
    else:
        for cond in CRITICAL_TERMS | MODERATE_TERMS:
            if re.search(r'\b' + re.escape(cond) + r'\b', text, re.IGNORECASE):
                if cond not in seen:
                    seen.add(cond)
                    found.append({"condition": cond.title(),
                                  "severity": _condition_severity(cond)})
    return found