"""
report_validator.py
────────────────────────────────────────────────────────────────────────────
Pure heuristic validator — no LLM, no external API calls.

Checks extracted OCR text against medical keyword banks and structural
patterns to decide whether a document is a legitimate medical report.

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
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Result
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    is_medical: bool
    reason: str        # human-readable; shown to the user on rejection
    score: int         # raw keyword hit count (useful for debugging)


# ─────────────────────────────────────────────────────────────────────────────
# Keyword banks
# ─────────────────────────────────────────────────────────────────────────────

# Each phrase matched as a substring in lower-cased text adds +1 to score.
_MEDICAL_KEYWORDS: list[str] = [

    # ── Patient / report metadata ─────────────────────────────────────────────
    "patient name", "patient id", "patient no", "reg no", "reg. no",
    "date of birth", "d.o.b", "dob", "age", "sex", "gender",
    "referring physician", "ref. doctor", "ref doctor", "consultant",
    "report date", "collection date", "sample id", "specimen",
    "lab report", "laboratory report", "test report", "medical report",
    "discharge summary", "clinical history", "chief complaint",

    # ── Blood / haematology ───────────────────────────────────────────────────
    "hemoglobin", "haemoglobin", "hematocrit", "haematocrit",
    "platelet count", "wbc", "rbc", "white blood cell", "red blood cell",
    "neutrophil", "lymphocyte", "monocyte", "eosinophil", "basophil",
    "esr", "complete blood count", "cbc", "differential count",
    "mcv", "mch", "mchc", "rdw", "mpv",

    # ── Biochemistry / serum ──────────────────────────────────────────────────
    "serum", "plasma", "creatinine", "urea", "bun", "uric acid",
    "bilirubin", "total protein", "albumin", "globulin", "a/g ratio",
    "alkaline phosphatase", "alp", "alt", "sgpt", "ast", "sgot",
    "gamma gt", "ggt", "ldh",
    "sodium", "potassium", "chloride", "bicarbonate", "calcium",
    "phosphorus", "magnesium", "electrolyte",
    "glucose", "fasting glucose", "random glucose", "hba1c",
    "cholesterol", "triglyceride", "hdl", "ldl", "vldl",
    "lipid profile", "tsh", "t3", "t4", "free t4", "free t3",
    "ferritin", "iron", "tibc", "transferrin",
    "psa", "cea", "ca-125", "afp",
    "lft", "kft", "rft", "thyroid function",

    # ── Urinalysis / microbiology ─────────────────────────────────────────────
    "urinalysis", "urine analysis", "urine r/e", "urine routine",
    "urobilinogen", "ketone", "nitrite",
    "specific gravity", "epithelial cell", "pus cell", "cast",
    "stool r/e", "stool routine", "stool culture",
    "blood culture", "urine culture",
    "mcs", "culture and sensitivity",

    # ── Radiology / imaging ───────────────────────────────────────────────────
    "x-ray", "xray", "chest x-ray", "cxr",
    "ct scan", "mri", "ultrasound", "usg",
    "impression", "findings", "opacity", "consolidation",
    "pleural effusion", "cardiomegaly", "pneumonia",
    "fracture", "calcification", "lesion", "mass",
    "no acute cardiopulmonary", "normal study",
    "echocardiogram", "echo report",

    # ── Vitals / clinical ─────────────────────────────────────────────────────
    "blood pressure", "pulse rate", "heart rate", "temperature",
    "respiratory rate", "spo2", "oxygen saturation",
    "ecg", "ekg", "electrocardiogram",
    "diagnosis", "provisional diagnosis",
    "prescription", "medication", "dosage", "follow up",
    "admission date", "discharge date", "ward",

    # ── Bangladeshi / regional lab names ─────────────────────────────────────
    "popular diagnostic", "ibn sina", "square hospital", "labaid",
    "dmch", "birdem", "apollo", "evercare", "chevron",
    "national heart foundation",
]


# If 3 or more of these match, the document is fast-rejected before
# even checking the medical score.
_NON_MEDICAL_KEYWORDS: list[str] = [
    # Financial / commercial
    "invoice", "tax invoice", "receipt", "purchase order", "quotation",
    "vat", "total amount", "subtotal", "bank statement",
    "account number", "transaction id", "credit card", "debit card",
    "balance due", "deposit", "withdrawal",

    # Legal / administrative
    "deed", "contract", "agreement", "affidavit", "power of attorney",
    "memorandum", "certificate of incorporation", "notary public",
    "visa application", "national id", "nid card",

    # Food / retail
    "menu", "restaurant", "order summary", "delivery address",
    "ingredient list",

    # HR / career
    "curriculum vitae", "cover letter", "salary slip",
    "payroll", "employment contract",

    # Utility bills
    "electricity bill", "water bill", "gas bill", "meter reading",
]


# Minimum medical keyword hits required to accept the document.
_MIN_SCORE: int = 2

# Non-medical hit threshold for fast rejection.
_NON_MEDICAL_THRESHOLD: int = 3


# ─────────────────────────────────────────────────────────────────────────────
# Validator
# ─────────────────────────────────────────────────────────────────────────────

class ReportValidator:
    """
    Validates OCR text to ensure it originates from a medical report.

    Decision logic
    ──────────────
    1. Blank / too-short text          → reject immediately.
    2. ≥ 3 non-medical keyword hits    → reject as wrong document type.
    3. < 2 medical keyword hits        → reject as unrecognised document.
    4. Otherwise                       → accept.
    """

    def validate(self, text: str) -> ValidationResult:
        """
        Args:
            text: Raw OCR-extracted text from the uploaded file.

        Returns:
            ValidationResult — check `.is_medical` before continuing.
        """

        # ── Guard: blank / too short ──────────────────────────────────────────
        cleaned = text.strip() if text else ""
        if len(re.sub(r'[\s\W_]+', '', cleaned)) < 20:
            return ValidationResult(
                is_medical=False,
                score=0,
                reason=(
                    "The document appears to be blank or contains too little text. "
                    "Please upload a clear image or PDF of a medical report."
                ),
            )

        normalized = cleaned.lower()

        # ── Stage 1: non-medical fast-reject ─────────────────────────────────
        non_hits = [kw for kw in _NON_MEDICAL_KEYWORDS if kw in normalized]

        if len(non_hits) >= _NON_MEDICAL_THRESHOLD:
            logger.info("Rejected — non-medical keywords detected: %s", non_hits[:6])
            return ValidationResult(
                is_medical=False,
                score=0,
                reason=(
                    "The uploaded document does not appear to be a medical report. "
                    "It looks like a financial, legal, or administrative document. "
                    "Please upload a valid medical document such as a lab result, "
                    "prescription, discharge summary, or radiology report."
                ),
            )

        # ── Stage 2: medical keyword score ───────────────────────────────────
        med_hits = [kw for kw in _MEDICAL_KEYWORDS if kw in normalized]
        score    = len(med_hits)

        logger.debug(
            "Validation — score=%d  med=%s  non=%s",
            score, med_hits[:6], non_hits,
        )

        if score < _MIN_SCORE:
            return ValidationResult(
                is_medical=False,
                score=score,
                reason=(
                    "The uploaded document does not appear to be a medical report. "
                    "No recognisable medical content was detected (lab values, "
                    "diagnoses, patient information, or imaging results). "
                    "Please upload a valid medical report."
                ),
            )

        return ValidationResult(is_medical=True, score=score, reason="OK")