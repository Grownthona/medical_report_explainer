"""
report_assembler.py
────────────────────
Stage 3 of the medical report pipeline.

Orchestrates the full flow:
  Raw OCR
    → patient_header.extract_header()   (Stage 1)
    → medical_ner.extract_lab_results() (Stage 2)
    → assemble_report()                 (Stage 3)

Single entry point for your API route:

    from report_assembler import assemble_report

    result = assemble_report(raw_text)
    return result  # ready to serialize as JSON
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

from services.patient_header import extract_header, PatientHeader
from services.extractor import extract_lab_results, extract_conditions


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
    Full pipeline entry point.

    Args:
        raw: Raw OCR text from the lab report (messy, single-line or multi-line)

    Returns:
        dict with shape:
        {
            "patient": {
                "name":            str | None,
                "age_years":       int | None,
                "gender":          "male" | "female" | "unknown",
                "report_type":     "CBC" | "LFT" | ... | None,
                "collection_date": "YYYY-MM-DD" | None
            },
            "results": [
                { "test": str, "value": float, "unit": str, "status": str },
                ...
            ],
            "conditions": [
                { "condition": str, "severity": str },
                ...
            ],
            "summary": {
                "total_tests":    int,
                "abnormal_count": int,
                "critical_count": int,
                "has_critical":   bool
            }
        }
    """

    # ── Stage 1: extract header (runs on raw text, before any cleaning) ───────
    # We run header extraction first so noise stripping in Stage 2 doesn't
    # destroy patient name / age / date fields.
    # report_type is left None here — filled in after Stage 2 runs.
    header: PatientHeader = extract_header(raw, lab_results=None)

    # ── Stage 2: NER — extract lab values ────────────────────────────────────
    # Pass gender from header so range comparisons are gender-aware.
    results: list[dict] = extract_lab_results(raw, gender=header.gender)

    # Now that we have the test names, infer report type and update header
    test_names = [r["test"] for r in results]
    from services.patient_header import infer_report_type
    header.report_type = infer_report_type(test_names)

    # ── Stage 2b: condition detection (spaCy or keyword fallback) ─────────────
    conditions: list[dict] = extract_conditions(raw)

    # ── Stage 3: assemble ─────────────────────────────────────────────────────
    summary = _compute_summary(results)

    report = MedicalReport(
        patient=header.to_dict(),
        results=results,
        conditions=conditions,
        summary=summary.to_dict(),
    )

    return report.to_dict()


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
    from services.extractor import extract_lab_results

    header: PatientHeader = extract_header(raw, lab_results=None)
    entities = extract_lab_results(raw, gender=header.gender, as_entities=True)
    entity_dicts = [asdict(e) for e in entities]

    from services.patient_header import infer_report_type
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
