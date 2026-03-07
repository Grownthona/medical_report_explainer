"""
document_classifier.py
───────────────────────
Stage 0 of the medical report pipeline.

Two-level classification:
  Level 1 → CATEGORY  : LAB | IMAGING | CLINICAL | SPECIALIST | PATHOLOGY | ADMINISTRATIVE | UNKNOWN
  Level 2 → SUB_TYPE  : CBC | LFT | XRAY | DISCHARGE | PHYSIO | HISTOPATH | ...

Usage:
    from document_classifier import classify, ClassificationResult

    result = classify(raw_text)
    print(result.category)   # "LAB"
    print(result.sub_type)   # "CBC"
    print(result.confidence) # "HIGH" | "MEDIUM" | "LOW"
    print(result.scores)     # { "LAB": 9, "IMAGING": 1, ... }
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Optional


# ─── Output model ─────────────────────────────────────────────────────────────

@dataclass
class ClassificationResult:
    category:   str            # Level 1: LAB | IMAGING | CLINICAL | SPECIALIST | PATHOLOGY | ADMINISTRATIVE | UNKNOWN
    sub_type:   str            # Level 2: CBC | LFT | XRAY | DISCHARGE | PHYSIO | ... | UNKNOWN
    confidence: str            # HIGH (≥5 hits) | MEDIUM (3-4) | LOW (1-2) | NONE
    is_mixed:   bool           # True if multiple sub-types score equally (e.g. CBC + LFT on same report)
    scores:     dict           # { category: hit_count } — useful for debugging
    sub_scores: dict           # { sub_type: hit_count } within winning category

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Level 1 signals — CATEGORY ───────────────────────────────────────────────
# Each keyword list is checked against lowercased text.
# More specific / diagnostic keywords weighted higher (see LEVEL_1_WEIGHTS).

LEVEL_1_SIGNALS: dict[str, list[str]] = {

    "LAB": [
        # Structural table markers
        "normal range", "test name", "result", "reference range",
        # Units that only appear in lab reports
        "g/dl", "gm/dl", "x10^9", "x10^12", "mmol/l", "meq/l",
        "u/l", "iu/l", "mg/dl", "ng/ml", "pg/ml", "fl",
        # Common test names
        "haemoglobin", "hemoglobin", "wbc", "rbc", "platelets",
        "creatinine", "bilirubin", "cholesterol", "triglycerides",
        "tsh", "alt", "ast", "alp", "esr", "crp", "hba1c",
        "inr", "aptt", "fibrinogen",
        # Lab report header words
        "haematology", "hematology", "biochemistry", "pathology report",
        "specimen", "inv no", "collection date",
    ],

    "IMAGING": [
        # Modality names
        "x-ray", "x ray", "radiograph", "chest pa", "chest ap",
        "mri", "magnetic resonance", "ct scan", "computed tomography",
        "ultrasonography", "ultrasound", "usg", "echocardiogram", "echo",
        "pet scan", "fluoroscopy", "mammography", "dexa",
        # Imaging-specific findings vocabulary
        "opacity", "consolidation", "cardiomegaly", "costophrenic",
        "pleural effusion", "pneumothorax", "atelectasis",
        "hypoechoic", "hyperechoic", "echogenicity", "anechoic",
        "hounsfield", "axial section", "coronal", "sagittal",
        "t1 weighted", "t2 weighted", "flair", "diffusion",
        "ejection fraction", "lvef", "mitral valve", "aortic",
        # Impression / conclusion markers common in imaging
        "impression", "findings", "no active", "no acute",
    ],

    "CLINICAL": [
        # Consultation / visit markers
        "chief complaint", "presenting complaint", "complaints of",
        "history of present illness", "hopi", "history of",
        "on examination", "general examination", "systemic examination",
        # Assessment / plan
        "diagnosis", "diagnosed with", "provisional diagnosis",
        "differential diagnosis", "assessment", "plan",
        "advised", "advice given", "prescription", "prescribed",
        # Admission / discharge
        "admitted", "discharge", "date of admission", "date of discharge",
        "length of stay", "condition at discharge",
        # Progress / follow-up
        "follow up", "follow-up", "review after", "next visit",
        "progress note", "patient is", "patient presents",
        # Referral
        "referred to", "referral", "request for",
    ],

    "SPECIALIST": [
        # Orthopaedic / physiotherapy
        "range of motion", "rom", "flexion", "extension", "abduction",
        "adduction", "joint", "fracture", "dislocation", "alignment",
        "tenderness on palpation", "swelling", "crepitus",
        "power grade", "muscle strength", "physiotherapy", "rehab",
        # Neurology
        "deep tendon reflex", "plantar reflex", "gcs", "glasgow coma",
        "cranial nerve", "sensory loss", "motor deficit", "mmse",
        "power in", "tone", "coordination",
        # Psychiatry
        "mental status examination", "mse", "mood", "affect", "depressed",
        "phq-9", "gaf", "insight", "judgement", "cognition", "anxiety", "personality",
        # Dental
        "tooth", "teeth", "caries", "extraction", "root canal",
        "periodontal", "occlusion", "dental chart",
        # Ophthalmology
        "visual acuity", "intraocular pressure", "fundus", "retina",
        "slit lamp", "iop", "snellen",
    ],

    "PATHOLOGY": [
        # Specimen handling
        "specimen received", "biopsy", "tissue received",
        "gross examination", "microscopic examination", "microscopy",
        # Histopathology
        "histopathology", "histology", "sections show",
        "staining", "h&e", "immunohistochemistry", "ihc",
        # Cytology
        "cytology", "fnac", "fine needle", "pap smear",
        "cervical smear", "cells seen",
        # Findings vocabulary
        "malignant", "benign", "carcinoma", "adenocarcinoma",
        "squamous cell", "mitosis", "necrosis", "infiltration",
        "grade", "stage", "margins", "lymphovascular invasion",
        # Microbiology / culture
        "culture", "sensitivity", "organism", "resistant",
        "susceptible", "mics", "colony count", "growth",
    ],

    "ADMINISTRATIVE": [
        # Legal / insurance markers
        "medical summary", "clinical summary", "medicolegal", "medico-legal",
        "fitness to work", "fitness certificate", "certify that",
        "insurance", "claimant", "plaintiff", "compensation",
        "legal", "court", "attorney", "solicitor",
        # Evaluation / audit
        "hospital evaluation", "quality of care", "patient safety",
        "mortality rate", "readmission", "audit",
        # Narrative / summary markers
        "medical narrative", "summary of treatment",
        "chronological", "in summary", "to whom it may concern",
    ],
}

# Keywords that carry extra weight (count as 2 hits)
# because they are highly diagnostic of a category
LEVEL_1_HIGH_WEIGHT: dict[str, set[str]] = {
    "LAB":            {"normal range", "x10^9", "x10^12", "haematology",
                       "hba1c", "haemoglobin"},
    "IMAGING":        {"hounsfield", "ejection fraction", "costophrenic",
                       "x-ray", "echogenicity", "t2 weighted"},
    "CLINICAL":       {"chief complaint", "date of discharge",
                       "condition at discharge", "hopi"},
    "SPECIALIST":     {"range of motion", "deep tendon reflex",
                       "mental status examination", "visual acuity"},
    "PATHOLOGY":      {"histopathology", "specimen received",
                       "microscopic examination", "immunohistochemistry"},
    "ADMINISTRATIVE": {"medicolegal", "fitness certificate",
                       "to whom it may concern"},
}


# ─── Level 2 signals — SUB_TYPE ───────────────────────────────────────────────

LEVEL_2_SIGNALS: dict[str, dict[str, list[str]]] = {

    "LAB": {
        "CBC": [
            "haemoglobin", "hemoglobin", "wbc", "rbc", "platelets",
            "hct", "pcv", "mcv", "mch", "mchc", "rdw", "mpv",
            "neutrophil", "lymphocyte", "monocyte", "eosinophil",
            "basophil", "differential", "esr", "total count",
        ],
        "LFT": [
            "alt", "alanine", "ast", "aspartate", "alp", "alkaline phosphatase",
            "ggt", "gamma", "bilirubin", "albumin", "total protein",
            "globulin", "sgpt", "sgot", "liver function",
        ],
        "RFT": [
            "creatinine", "urea", "bun", "blood urea nitrogen",
            "egfr", "uric acid", "cystatin", "renal function",
            "kidney function", "serum creatinine",
        ],
        "TFT": [
            "tsh", "thyroid stimulating", "t3", "t4",
            "free t3", "free t4", "ft3", "ft4",
            "thyroid function", "thyroxine", "triiodothyronine",
        ],
        "LIPID": [
            "cholesterol", "ldl", "hdl", "triglycerides", "vldl",
            "total cholesterol", "lipid profile", "non-hdl",
        ],
        "HBA1C": [
            "hba1c", "glycated hemoglobin", "glycosylated",
            "fasting glucose", "fasting blood sugar", "fbs",
            "postprandial", "pp glucose", "random blood sugar", "rbs",
        ],
        "ELECTROLYTES": [
            "sodium", "potassium", "chloride", "bicarbonate",
            "calcium", "magnesium", "phosphate", "electrolyte",
            "na", "k+", "cl-",
        ],
        "COAGULATION": [
            "pt", "prothrombin time", "aptt", "inr",
            "fibrinogen", "d-dimer", "bleeding time",
            "clotting time", "coagulation",
        ],
        "CULTURE": [
            "culture", "sensitivity", "organism", "resistant",
            "susceptible", "antibiotic", "mics", "colony",
            "growth", "no growth", "sterile",
        ],
        "HORMONE": [
            "cortisol", "fsh", "lh", "testosterone", "estrogen",
            "estradiol", "prolactin", "progesterone", "insulin",
            "growth hormone", "acth", "dhea",
        ],
        "URINE": [
            "urine", "urinalysis", "urine r/e", "urine routine",
            "albumin urine", "glucose urine", "ketone", "nitrite",
            "leukocyte esterase", "specific gravity", "urine culture",
        ],
    },

    "IMAGING": {
        "XRAY": [
            "x-ray", "x ray", "radiograph", "chest pa", "chest ap",
            "cardiomegaly", "costophrenic", "consolidation",
            "pleural", "pneumothorax", "rib", "spine x-ray",
            "kv", "mas",
        ],
        "USG": [
            "ultrasonography", "ultrasound", "usg",
            "hypoechoic", "hyperechoic", "echogenicity", "anechoic",
            "liver size", "gallbladder", "kidney size", "spleen",
            "ovary", "uterus", "obstetric", "fetal",
        ],
        "CT": [
            "ct scan", "computed tomography", "hounsfield",
            "axial", "coronal", "sagittal", "contrast",
            "hypodense", "hyperdense", "isodense",
            "ct chest", "ct abdomen", "ct brain",
        ],
        "MRI": [
            "mri", "magnetic resonance", "t1", "t2", "flair",
            "diffusion", "dwi", "adc", "gadolinium",
            "hyperintense", "hypointense", "signal",
            "mri brain", "mri spine", "mri knee",
        ],
        "ECHO": [
            "echocardiogram", "echo", "ejection fraction", "lvef",
            "mitral valve", "aortic valve", "tricuspid",
            "left ventricle", "right ventricle", "pericardial",
            "wall motion", "diastolic", "systolic function",
        ],
        "PET": [
            "pet scan", "positron emission", "fdg", "suv",
            "metabolic activity", "uptake", "staging",
        ],
        "MAMMOGRAPHY": [
            "mammography", "mammogram", "birads", "bi-rads",
            "breast density", "calcification", "microcalcification",
        ],
    },

    "CLINICAL": {
        "OPD_NOTE": [
            "outpatient", "opd", "clinic", "presenting complaint",
            "chief complaint", "on examination", "advised",
            "prescription", "follow up",
        ],
        "DISCHARGE": [
            "discharge", "date of discharge", "date of admission",
            "condition at discharge", "discharge diagnosis",
            "discharge medication", "length of stay", "admitted on",
        ],
        "PROGRESS": [
            "progress note", "progress report", "day", "rounds",
            "subjective", "objective", "assessment", "plan",
            "patient is", "vitals", "overnight",
        ],
        "REFERRAL": [
            "referred to", "referral", "dear doctor", "dear dr",
            "request for", "kindly", "for your", "opinion",
        ],
        "OPERATIVE": [
            "operation note", "operative note", "procedure",
            "incision", "anaesthesia", "anesthesia", "surgeon",
            "post-operative", "postoperative", "intraoperative",
        ],
        "EMERGENCY": [
            "emergency", "casualty", "presenting to er",
            "brought by", "gcs", "resuscitation", "triage",
            "acute", "onset",
        ],
    },

    "SPECIALIST": {
        "PHYSIO": [
            "physiotherapy", "physical therapy", "rom",
            "range of motion", "strengthening", "exercise",
            "rehab", "rehabilitation", "gait", "posture",
        ],
        "ORTHO": [
            "fracture", "dislocation", "alignment", "bone",
            "joint", "x-ray", "cast", "splint", "implant",
            "screw", "plate", "fixation", "orthopaedic",
        ],
        "NEURO": [
            "deep tendon reflex", "plantar", "cranial nerve",
            "gcs", "power", "tone", "sensory", "coordination",
            "mmse", "neurology", "neuropathy",
        ],
        "PSYCH": [
            "mental status", "mse", "mood", "affect", "phq",
            "gaf", "insight", "cognition", "psychiatry",
            "anxiety", "depression", "psychosis",
        ],
        "OPHTHA": [
            "visual acuity", "iop", "intraocular pressure",
            "fundus", "retina", "slit lamp", "snellen",
            "refraction", "ophthalmology",
        ],
        "DENTAL": [
            "tooth", "teeth", "caries", "extraction",
            "root canal", "periodontal", "dental",
            "occlusion", "crown", "filling",
        ],
        "CARDIOLOGY": [
            "ecg", "ekg", "electrocardiogram", "sinus rhythm",
            "st segment", "qt interval", "arrhythmia",
            "holter", "stress test", "cardiac",
        ],
    },

    "PATHOLOGY": {
        "HISTOPATH": [
            "histopathology", "biopsy", "sections show",
            "h&e", "staining", "mitosis", "necrosis",
            "grade", "margins", "invasion",
        ],
        "CYTOLOGY": [
            "cytology", "fnac", "fine needle", "pap smear",
            "cervical smear", "cells seen", "aspirate",
        ],
        "CULTURE_MICRO": [
            "culture", "sensitivity", "organism", "resistant",
            "susceptible", "colony", "growth", "antibiotic",
        ],
        "AUTOPSY": [
            "autopsy", "post mortem", "cause of death",
            "organ weight", "external examination",
        ],
    },

    "ADMINISTRATIVE": {
        "MEDICAL_SUMMARY":   ["medical summary", "summary of", "chronological"],
        "NARRATIVE_REPORT":  ["narrative", "medicolegal", "medico-legal", "litigation"],
        "FITNESS_CERT":      ["fitness", "certify", "fit to", "unfit"],
        "EVALUATION_REPORT": ["evaluation", "quality of care", "audit", "mortality"],
    },
}


# ─── Confidence thresholds ────────────────────────────────────────────────────

def _confidence(score: int) -> str:
    if score >= 5:
        return "HIGH"
    if score >= 3:
        return "MEDIUM"
    if score >= 1:
        return "LOW"
    return "NONE"


# ─── Core scoring ─────────────────────────────────────────────────────────────

def _score_category(text: str) -> dict[str, int]:
    scores: dict[str, int] = {}
    for category, keywords in LEVEL_1_SIGNALS.items():
        count = 0
        high_weight = LEVEL_1_HIGH_WEIGHT.get(category, set())
        for kw in keywords:
            if kw in text:
                count += 2 if kw in high_weight else 1
        scores[category] = count
    return scores


def _score_sub_type(text: str, category: str) -> dict[str, int]:
    sub_signals = LEVEL_2_SIGNALS.get(category, {})
    scores: dict[str, int] = {}
    for sub_type, keywords in sub_signals.items():
        scores[sub_type] = sum(1 for kw in keywords if kw in text)
    return scores


def _pick_winner(scores: dict[str, int], min_score: int = 1) -> tuple[str, bool]:
    """
    Return (winner, is_mixed).
    is_mixed=True when two or more types tie for the top score.
    """
    if not scores or max(scores.values()) < min_score:
        return "UNKNOWN", False

    top_score = max(scores.values())
    winners = [k for k, v in scores.items() if v == top_score]

    if len(winners) > 1:
        return " + ".join(sorted(winners)), True
    return winners[0], False


# ─── Public API ───────────────────────────────────────────────────────────────

def classify(raw: str) -> ClassificationResult:
    """
    Classify a raw medical report text into category and sub-type.

    Args:
        raw: Raw OCR or copy-pasted report text

    Returns:
        ClassificationResult with category, sub_type, confidence, is_mixed, scores
    """
    text = raw.lower()
    # Normalise common OCR artefacts that break keyword matching
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('-\n', '')   # hyphenated line breaks

    # ── Level 1: category ────────────────────────────────────────────────────
    cat_scores = _score_category(text)
    category, cat_is_mixed = _pick_winner(cat_scores, min_score=2)

    if category == "UNKNOWN":
        return ClassificationResult(
            category="UNKNOWN",
            sub_type="UNKNOWN",
            confidence="NONE",
            is_mixed=False,
            scores=cat_scores,
            sub_scores={},
        )

    # For mixed categories (e.g. CBC + LFT on same sheet) use primary category
    primary_category = category.split(" + ")[0] if cat_is_mixed else category

    # ── Level 2: sub-type ────────────────────────────────────────────────────
    sub_scores = _score_sub_type(text, primary_category)
    sub_type, sub_is_mixed = _pick_winner(sub_scores, min_score=1)

    # Overall confidence based on top category score
    top_cat_score = cat_scores[primary_category]
    confidence = _confidence(top_cat_score)

    return ClassificationResult(
        category=category,             # may be "LAB + IMAGING" if mixed
        sub_type=sub_type,             # may be "CBC + LFT" if mixed panel
        confidence=confidence,
        is_mixed=cat_is_mixed or sub_is_mixed,
        scores=cat_scores,
        sub_scores=sub_scores,
    )


def classify_dict(raw: str) -> dict:
    """Convenience wrapper — returns plain dict for JSON serialization."""
    return classify(raw).to_dict()
