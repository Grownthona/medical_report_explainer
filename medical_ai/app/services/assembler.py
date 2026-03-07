from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

from services.patient_header import extract_header, PatientHeader, infer_report_type
from services.extractor import extract_lab_results, extract_conditions
from document_classifier import classify, ClassificationResult


# ─── Output models ────────────────────────────────────────────────────────────

@dataclass
class ReportSummary:
    """Top-level flags computed from the assembled report."""
    total_tests:     int
    abnormal_count:  int          # HIGH or LOW
    critical_count:  int          # CRITICAL_HIGH or CRITICAL_LOW
    has_critical:    bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MedicalReport:
    patient:    dict              # PatientHeader.to_dict()
    results:    list[dict]        # List of { test, value, unit, status }
    conditions: list[dict]        # List of { condition, severity } from spaCy/keyword scan
    summary:    dict              # ReportSummary.to_dict()

    def to_dict(self) -> dict:
        return {
            "patient":    self.patient,
            "results":    self.results,
            "conditions": self.conditions,
            "summary":    self.summary,
        }


# ─── Summary computation ──────────────────────────────────────────────────────

def _compute_summary(results: list[dict]) -> ReportSummary:
    critical_statuses = {"CRITICAL_HIGH", "CRITICAL_LOW"}
    abnormal_statuses = {"HIGH", "LOW", "CRITICAL_HIGH", "CRITICAL_LOW"}

    critical_count = sum(1 for r in results if r["status"] in critical_statuses)
    abnormal_count = sum(1 for r in results if r["status"] in abnormal_statuses)

    return ReportSummary(
        total_tests=len(results),
        abnormal_count=abnormal_count,
        critical_count=critical_count,
        has_critical=critical_count > 0,
    )


# ─── Public API ───────────────────────────────────────────────────────────────

def assemble_report(raw: str) -> dict:
    """
    Full pipeline entry point. Runs all 3 stages:
      Stage 0 → document_classifier  (what kind of report is this?)
      Stage 1 → patient_header       (who is the patient?)
      Stage 2 → correct extractor    (what are the findings/results?)
      Stage 3 → assembler            (merge into unified response)

    Returns:
        {
            "document_type": { "category": str, "sub_type": str,
                               "confidence": str, "is_mixed": bool },
            "patient":  { name, age_years, gender, report_type, collection_date },
            "results":  [ { test, value, unit, status } ... ],   # shape varies by category
            "conditions": [ { condition, severity } ... ],
            "summary":  { total_tests, abnormal_count, critical_count, has_critical }
        }
    """

    # ── Stage 0: classify document ────────────────────────────────────────────
    classification: ClassificationResult = classify(raw)

    # ── Stage 1: extract patient header ──────────────────────────────────────
    # Always runs on raw text (before cleaning) so noise stripping
    # in Stage 2 doesn't destroy name / age / date fields.
    header: PatientHeader = extract_header(raw, lab_results=None)

    # ── Stage 2: route to correct extractor ──────────────────────────────────
    primary_category = classification.category.split(" + ")[0]
    results: list[dict] = []
    conditions: list[dict] = []

    if primary_category == "LAB":
        results = extract_lab_results(raw, gender=header.gender)
        # Back-fill report_type from actual tests found (more reliable than OCR header)
        header.report_type = infer_report_type([r["test"] for r in results])
        conditions = extract_conditions(raw)

    elif primary_category == "IMAGING":
        # Placeholder — radiology_extractor not yet built
        # Swap in: from radiology_extractor import extract_findings
        # results = extract_findings(raw)
        header.report_type = classification.sub_type
        results = [{
            "note": f"Imaging extractor ({classification.sub_type}) not yet implemented",
            "category": "IMAGING",
            "sub_type": classification.sub_type,
        }]

    elif primary_category == "CLINICAL":
        # Placeholder — clinical_summary_extractor not yet built
        header.report_type = classification.sub_type
        results = [{
            "note": f"Clinical extractor ({classification.sub_type}) not yet implemented",
            "category": "CLINICAL",
            "sub_type": classification.sub_type,
        }]

    elif primary_category == "SPECIALIST":
        # Placeholder — specialist_extractor not yet built
        header.report_type = classification.sub_type
        results = [{
            "note": f"Specialist extractor ({classification.sub_type}) not yet implemented",
            "category": "SPECIALIST",
            "sub_type": classification.sub_type,
        }]

    elif primary_category == "PATHOLOGY":
        # Placeholder — pathology_extractor not yet built
        header.report_type = classification.sub_type
        results = [{
            "note": f"Pathology extractor ({classification.sub_type}) not yet implemented",
            "category": "PATHOLOGY",
            "sub_type": classification.sub_type,
        }]

    else:
        # ADMINISTRATIVE or UNKNOWN — no extraction attempted
        header.report_type = classification.sub_type

    # ── Stage 3: assemble ─────────────────────────────────────────────────────
    summary = _compute_summary(results)

    return {
        "document_type": {
            "category":   classification.category,
            "sub_type":   classification.sub_type,
            "confidence": classification.confidence,
            "is_mixed":   classification.is_mixed,
        },
        "patient":    header.to_dict(),
        "results":    results,
        "conditions": conditions,
        "summary":    summary.to_dict(),
    }



# ─── Endpoint-compatible variant ──────────────────────────────────────────────
# If your existing route uses MedicalEntityOut, use this instead of assemble_report().
# The "results" field will use the old { text, entity_type, severity, explanation, value, unit } shape.

def assemble_report_legacy(raw: str) -> dict:
    """
    Same as assemble_report() but results use MedicalEntity shape
    for backward compatibility with existing MedicalEntityOut endpoints.

        entities = assemble_report_legacy(text)["results"]
        return MedicalEntityOut(
            text=e["text"],
            entity_type=e["entity_type"],
            severity=e["severity"],
            explanation=e["explanation"],
            value=e["value"],
            unit=e["unit"],
        )
    """
    from medical_ner import extract_lab_results

    header: PatientHeader = extract_header(raw, lab_results=None)
    entities = extract_lab_results(raw, gender=header.gender, as_entities=True)
    entity_dicts = [asdict(e) for e in entities]

    from patient_header import infer_report_type
    header.report_type = infer_report_type([e["text"] for e in entity_dicts])

    conditions = extract_conditions(raw)
    summary = _compute_summary([
        {"status": e["severity"].replace("MODERATE", "HIGH").replace("INFO", "NORMAL")}
        for e in entity_dicts
    ])

    return {
        "patient":    header.to_dict(),
        "results":    entity_dicts,
        "conditions": conditions,
        "summary":    summary.to_dict(),
    }

