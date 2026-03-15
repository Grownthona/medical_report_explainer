"""
report_validator.py
────────────────────────────────────────────────────────────────────────────
Multi-layer heuristic validator — no LLM, no external API calls.

Validation pipeline (in order):
  Layer 0 — Blank / too-short text guard
  Layer 1 — Hard-reject: non-medical document fast-reject (financial, legal…)
  Layer 2 — Hard-reject: personally harmful / offensive content
  Layer 3 — Structural pattern check (reference ranges, units, numeric values)
  Layer 4 — Medical keyword scoring
  Layer 5 — Language / encoding plausibility check
  Layer 6 — Confidence composite score gate

Usage:
    from services.report_validator import ReportValidator, ValidationResult

    validator = ReportValidator()
    result    = validator.validate(ocr_text)

    if not result.is_medical:
        raise HTTPException(status_code=422, detail=result.reason)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Result
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    is_medical: bool
    reason: str            # human-readable; shown to the user on rejection
    score: int             # raw medical keyword hit count
    structural_score: int  # bonus points from structural patterns
    rejection_layer: str   # which layer rejected (empty string if accepted)
    matched_keywords: list[str] = field(default_factory=list)   # debug info


# ─────────────────────────────────────────────────────────────────────────────
# ── LAYER 1: Non-medical keyword banks ───────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

_NON_MEDICAL_FINANCIAL: list[str] = [
    "invoice", "tax invoice", "proforma invoice", "receipt", "purchase order",
    "quotation", "vat", "total amount", "subtotal", "grand total",
    "bank statement", "account number", "transaction id", "credit card",
    "debit card", "balance due", "deposit", "withdrawal", "cheque",
    "remittance", "swift code", "iban", "routing number",
    "profit and loss", "balance sheet", "cash flow",
]

_NON_MEDICAL_LEGAL: list[str] = [
    "deed", "contract", "legal agreement", "affidavit", "power of attorney",
    "memorandum of association", "certificate of incorporation",
    "notary public", "visa application", "passport application",
    "court order", "judgement", "plaintiff", "defendant",
    "terms and conditions", "privacy policy",
]

_NON_MEDICAL_HR: list[str] = [
    "curriculum vitae", "cover letter", "salary slip", "payroll",
    "employment contract", "offer letter", "resignation letter",
    "performance appraisal", "job description",
]

_NON_MEDICAL_RETAIL: list[str] = [
    "menu", "restaurant", "order summary", "delivery address",
    "ingredient list", "nutritional information per serving",
    "shopping cart", "product catalogue", "discount code",
    "loyalty points", "return policy",
]

_NON_MEDICAL_UTILITY: list[str] = [
    "electricity bill", "water bill", "gas bill", "meter reading",
    "internet bill", "phone bill", "broadband invoice",
]

_NON_MEDICAL_SOCIAL: list[str] = [
    "likes", "followers", "retweet", "hashtag", "instagram",
    "facebook post", "tweet", "tiktok", "youtube video",
    "subscribe", "unsubscribe", "click here to view",
]

_NON_MEDICAL_ACADEMIC: list[str] = [
    "question paper", "mark sheet", "grade sheet", "roll number",
    "semester result", "cgpa", "gpa result", "admit card",
    "hall ticket", "board exam", "university exam",
]

# Aggregate — any category with ≥ threshold hits triggers rejection
_NON_MEDICAL_GROUPS: dict[str, list[str]] = {
    "financial document":  _NON_MEDICAL_FINANCIAL,
    "legal document":      _NON_MEDICAL_LEGAL,
    "HR/employment document": _NON_MEDICAL_HR,
    "retail/menu document":   _NON_MEDICAL_RETAIL,
    "utility bill":           _NON_MEDICAL_UTILITY,
    "social media content":   _NON_MEDICAL_SOCIAL,
    "academic document":      _NON_MEDICAL_ACADEMIC,
}

_NON_MEDICAL_THRESHOLD: int = 2   # hits per category to trigger rejection


# ─────────────────────────────────────────────────────────────────────────────
# ── LAYER 2: Harmful / offensive content ─────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

_HARMFUL_KEYWORDS: list[str] = [
    "how to make bomb", "explosive recipe", "drug synthesis",
    "weapon instructions", "terrorist", "child abuse",
    "self harm instructions", "suicide method",
]

_HARMFUL_THRESHOLD: int = 1   # even a single hit → immediate rejection


# ─────────────────────────────────────────────────────────────────────────────
# ── LAYER 3: Structural patterns ─────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

# Each compiled regex that matches adds structural_score points
_STRUCTURAL_PATTERNS: list[tuple[re.Pattern, int, str]] = [
    # Reference range formats:  "3.5 – 5.0"  or  "(0.5-1.5)"
    (re.compile(r'\d+\.?\d*\s*[-–]\s*\d+\.?\d*'), 2, "reference_range"),

    # Numeric result with unit:  "12.5 g/dL"  "98 mg/dL"  "0.9 mmol/L"
    (re.compile(r'\d+\.?\d*\s*(g/dl|mg/dl|mmol/l|iu/l|u/l|ng/ml|pg/ml|meq/l|fl|pg|%|miu/ml|nmol/l|µmol/l|umol/l)', re.I), 3, "lab_unit"),

    # H / L flags common in lab reports
    (re.compile(r'\b(high|low|normal|abnormal|positive|negative|reactive|non.reactive|borderline)\b', re.I), 1, "result_flag"),

    # Date patterns  dd/mm/yyyy  or  dd-mm-yyyy
    (re.compile(r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b'), 1, "date_pattern"),

    # Doctor / hospital signature fields
    (re.compile(r'(dr\.?|md\.?|mbbs|fcps|mrcp|ms\.?)\s+[a-z]+', re.I), 2, "doctor_credential"),

    # Page break label inserted by OCR multi-page
    (re.compile(r'---\s*PAGE BREAK\s*---', re.I), 1, "page_break_marker"),

    # Numeric rows:  at least 3 numbers on one line (typical lab table row)
    (re.compile(r'(\d+\.?\d*\s+){3,}'), 2, "numeric_table_row"),

    # Common report section headers
    (re.compile(r'\b(test name|result|reference|unit|method|remarks)\b', re.I), 2, "table_header"),

    # Patient ID / registration number patterns
    (re.compile(r'(patient\s*(id|no|#)|reg\.?\s*(no|#))\s*[:\-]?\s*\w+', re.I), 2, "patient_id"),

    # Barcode / accession number
    (re.compile(r'\b(accession|barcode|sample\s*no|specimen\s*id)\s*[:\-]?\s*\w+', re.I), 1, "accession"),
]


# ─────────────────────────────────────────────────────────────────────────────
# ── LAYER 4: Medical keyword banks ───────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

_MEDICAL_KEYWORDS: list[str] = [

    # ── Patient / report metadata ─────────────────────────────────────────────
    "patient name", "patient id", "patient no", "reg no", "reg. no",
    "date of birth", "d.o.b", "dob", "age", "sex", "gender",
    "referring physician", "ref. doctor", "ref doctor", "consultant",
    "report date", "collection date", "sample id", "specimen",
    "lab report", "laboratory report", "test report", "medical report",
    "discharge summary", "clinical history", "chief complaint",
    "indoor", "outdoor", "opd", "ipd", "ward no",

    # ── Blood / haematology ───────────────────────────────────────────────────
    "hemoglobin", "haemoglobin", "hematocrit", "haematocrit",
    "platelet count", "wbc", "rbc", "white blood cell", "red blood cell",
    "neutrophil", "lymphocyte", "monocyte", "eosinophil", "basophil",
    "esr", "complete blood count", "cbc", "differential count",
    "mcv", "mch", "mchc", "rdw", "mpv", "reticulocyte",
    "prothrombin", "pt", "aptt", "inr", "fibrinogen",
    "blood group", "abo", "rh factor",

    # ── Biochemistry / serum ──────────────────────────────────────────────────
    "serum", "plasma", "creatinine", "urea", "bun", "uric acid",
    "bilirubin", "total protein", "albumin", "globulin", "a/g ratio",
    "alkaline phosphatase", "alp", "alt", "sgpt", "ast", "sgot",
    "gamma gt", "ggt", "ldh", "amylase", "lipase",
    "sodium", "potassium", "chloride", "bicarbonate", "calcium",
    "phosphorus", "magnesium", "electrolyte",
    "glucose", "fasting glucose", "random glucose", "hba1c",
    "cholesterol", "triglyceride", "hdl", "ldl", "vldl",
    "lipid profile", "tsh", "t3", "t4", "free t4", "free t3",
    "ferritin", "iron", "tibc", "transferrin",
    "psa", "cea", "ca-125", "afp", "ca 19-9",
    "lft", "kft", "rft", "thyroid function",
    "vitamin d", "vitamin b12", "folate", "zinc", "copper",
    "troponin", "ck-mb", "bnp", "d-dimer", "crp", "c-reactive protein",
    "anti-ccp", "rheumatoid factor", "rf", "ana",
    "hbsag", "anti-hcv", "hiv", "vdrl", "widal",
    "dengue", "malaria", "typhoid",

    # ── Urinalysis / microbiology ─────────────────────────────────────────────
    "urinalysis", "urine analysis", "urine r/e", "urine routine",
    "urobilinogen", "ketone", "nitrite",
    "specific gravity", "epithelial cell", "pus cell", "cast",
    "stool r/e", "stool routine", "stool culture",
    "blood culture", "urine culture", "sputum culture",
    "mcs", "culture and sensitivity", "sensitivity pattern",
    "gram stain", "acid fast bacilli", "afb",

    # ── Radiology / imaging ───────────────────────────────────────────────────
    "x-ray", "xray", "chest x-ray", "cxr",
    "ct scan", "mri", "ultrasound", "usg",
    "impression", "findings", "opacity", "consolidation",
    "pleural effusion", "cardiomegaly", "pneumonia",
    "fracture", "calcification", "lesion", "mass", "nodule",
    "no acute cardiopulmonary", "normal study",
    "echocardiogram", "echo report", "doppler",
    "bony trabeculae", "soft tissue", "radioopaque",
    "hepatomegaly", "splenomegaly", "ascites",

    # ── Vitals / clinical ─────────────────────────────────────────────────────
    "blood pressure", "pulse rate", "heart rate", "temperature",
    "respiratory rate", "spo2", "oxygen saturation",
    "ecg", "ekg", "electrocardiogram",
    "diagnosis", "provisional diagnosis", "final diagnosis",
    "prescription", "medication", "dosage", "follow up",
    "admission date", "discharge date", "ward",
    "systolic", "diastolic", "pulse oximetry",

    # ── Pathology / histology ─────────────────────────────────────────────────
    "biopsy", "histopathology", "cytology", "pap smear",
    "malignant", "benign", "carcinoma", "adenocarcinoma",
    "metastasis", "lymph node", "neoplasm", "dysplasia",

    # ── Bangladeshi / regional lab names ─────────────────────────────────────
    "popular diagnostic", "ibn sina", "square hospital", "labaid",
    "dmch", "birdem", "apollo", "evercare", "chevron",
    "national heart foundation", "shaheed suhrawardy",
    "dhaka medical", "combined military hospital", "cmh",
]

_MIN_MEDICAL_SCORE: int = 2        # minimum keyword hits
_MIN_COMPOSITE_SCORE: int = 3      # keyword + structural combined minimum


# ─────────────────────────────────────────────────────────────────────────────
# ── LAYER 5: Language / encoding plausibility ────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

# Medical reports from BD are in English, Bengali, or a mix.
# If the text is almost entirely random symbols / mojibake → reject.
_MAX_GARBAGE_RATIO: float = 0.60   # more than 60 % non-printable/garbage → reject

def _garbage_ratio(text: str) -> float:
    """Fraction of characters that are non-ASCII and non-Bengali Unicode."""
    if not text:
        return 1.0
    total   = len(text)
    # Accept: ASCII printable, Bengali Unicode block (0x0980-0x09FF), whitespace
    valid   = sum(
        1 for ch in text
        if ch.isspace()
        or (0x20 <= ord(ch) <= 0x7E)          # ASCII printable
        or (0x0980 <= ord(ch) <= 0x09FF)       # Bengali
        or (0x0600 <= ord(ch) <= 0x06FF)       # Arabic (Urdu/Arabic reports)
        or (0x0900 <= ord(ch) <= 0x097F)       # Devanagari (Hindi)
    )
    return 1.0 - (valid / total)


# ─────────────────────────────────────────────────────────────────────────────
# Validator
# ─────────────────────────────────────────────────────────────────────────────

class ReportValidator:
    """
    Multi-layer validator that checks OCR text against six criteria.

    Decision pipeline
    ─────────────────
    Layer 0  Blank / too-short text                    → reject immediately
    Layer 1  Non-medical category fast-reject           → reject with category name
    Layer 2  Harmful / offensive content               → reject immediately
    Layer 3  Structural patterns (bonus scoring)        → contributes to composite
    Layer 4  Medical keyword scoring                   → contributes to composite
    Layer 5  Language / encoding plausibility          → reject if mostly garbage
    Layer 6  Composite score gate                      → reject if too low
    """

    # ── public ────────────────────────────────────────────────────────────────

    def validate(self, text: str) -> ValidationResult:
        """
        Args:
            text: Raw OCR-extracted (or directly submitted) text.

        Returns:
            ValidationResult — always check `.is_medical` before proceeding.
        """

        # ── Layer 0: blank guard ─────────────────────────────────────────────
        cleaned = (text or "").strip()
        if len(re.sub(r'[\s\W_]+', '', cleaned)) < 20:
            return self._reject(
                layer="layer_0_blank",
                reason=(
                    "The document appears to be blank or contains too little text. "
                    "Please upload a clear image or PDF of a medical report."
                ),
            )

        normalized = cleaned.lower()

        # ── Layer 1: non-medical category rejection ──────────────────────────
        for category, keywords in _NON_MEDICAL_GROUPS.items():
            hits = [kw for kw in keywords if kw in normalized]
            if len(hits) >= _NON_MEDICAL_THRESHOLD:
                logger.info(
                    "Layer-1 reject (%s) — matched: %s", category, hits[:5]
                )
                return self._reject(
                    layer="layer_1_non_medical",
                    reason=(
                        f"The uploaded document appears to be a {category}, "
                        "not a medical report. "
                        "Please upload a valid medical document such as a lab result, "
                        "prescription, discharge summary, or radiology report."
                    ),
                )

        # ── Layer 2: harmful content ─────────────────────────────────────────
        harm_hits = [kw for kw in _HARMFUL_KEYWORDS if kw in normalized]
        if len(harm_hits) >= _HARMFUL_THRESHOLD:
            logger.warning("Layer-2 reject — harmful content detected")
            return self._reject(
                layer="layer_2_harmful",
                reason=(
                    "The document contains content that cannot be processed. "
                    "Please upload a valid medical report."
                ),
            )

        # ── Layer 3: structural pattern scoring ──────────────────────────────
        structural_score = 0
        structural_hits: list[str] = []
        for pattern, points, label in _STRUCTURAL_PATTERNS:
            if pattern.search(cleaned):
                structural_score += points
                structural_hits.append(label)

        logger.debug("Layer-3 structural score=%d  hits=%s", structural_score, structural_hits)

        # ── Layer 4: medical keyword scoring ─────────────────────────────────
        med_hits = [kw for kw in _MEDICAL_KEYWORDS if kw in normalized]
        score    = len(med_hits)

        logger.debug("Layer-4 keyword score=%d  hits=%s", score, med_hits[:8])

        # ── Layer 5: encoding / language plausibility ────────────────────────
        garbage = _garbage_ratio(cleaned)
        if garbage > _MAX_GARBAGE_RATIO:
            logger.info("Layer-5 reject — garbage ratio=%.2f", garbage)
            return self._reject(
                layer="layer_5_encoding",
                reason=(
                    "The document could not be read — it may be corrupted, "
                    "heavily watermarked, or saved in an unsupported format. "
                    "Please upload a clear, readable medical report."
                ),
            )

        # ── Layer 6: composite score gate ────────────────────────────────────
        composite = score + min(structural_score, 10)   # cap structural bonus at 10

        if score < _MIN_MEDICAL_SCORE and composite < _MIN_COMPOSITE_SCORE:
            logger.info(
                "Layer-6 reject — keyword=%d  structural=%d  composite=%d",
                score, structural_score, composite,
            )
            return self._reject(
                layer="layer_6_score",
                reason=(
                    "The uploaded document does not appear to be a medical report. "
                    "No recognisable medical content was detected (lab values, "
                    "diagnoses, patient information, or imaging results). "
                    "Please upload a valid medical report."
                ),
                score=score,
                structural_score=structural_score,
                matched_keywords=med_hits,
            )

        logger.info(
            "Accepted — keyword=%d  structural=%d  composite=%d",
            score, structural_score, composite,
        )
        return ValidationResult(
            is_medical=True,
            reason="OK",
            score=score,
            structural_score=structural_score,
            rejection_layer="",
            matched_keywords=med_hits,
        )

    # ── private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _reject(
        layer: str,
        reason: str,
        score: int = 0,
        structural_score: int = 0,
        matched_keywords: list[str] | None = None,
    ) -> ValidationResult:
        return ValidationResult(
            is_medical=False,
            reason=reason,
            score=score,
            structural_score=structural_score,
            rejection_layer=layer,
            matched_keywords=matched_keywords or [],
        )