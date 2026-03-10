"""
report_assembler.py
────────────────────
Stage 3 of the medical report pipeline. Single entry point for all uploads.

Flow — auto-detects mixed vs single report:

  Raw OCR text
       │
       ▼
  split_by_category(text)
       │
       ├─ multiple categories found?
       │       YES → extract_multi_section()  ← mixed PDF path
       │       NO  → classify() + extract()   ← single report path
       │
       ▼
  assemble_report()  →  unified response dict

Output shape (same for both paths):
    {
        "is_mixed":      bool,
        "document_type": { category, sub_type, confidence, is_mixed },  ← single only
        "patient":       { name, age_years, gender, report_type, collection_date },
        "report":        {                       ← single report info
            report_type, sub_type, summary,
            findings, impressions, advice,
            raw_text, metadata: { gender, confidence }
        },
        "sections":      {                       ← mixed PDF only, else {}
            "LAB":     [ { report dict + lab_values }, ... ],
            "IMAGING": [ { report dict }, ... ],
            ...
        },
        "lab_values":    [ { test, value, unit, status }, ... ],
        "conditions":    [ { condition, severity }, ... ],
        "summary":       { total_tests, abnormal_count, critical_count, has_critical }
    }
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

from services.patient_header  import extract_header, PatientHeader, infer_report_type
from services.extractor       import extract, extract_conditions
from services.classifier      import classify, ClassificationResult
from services.llm_extractor   import split_by_category, extract_multi_section, extract_report


# ── Summary ───────────────────────────────────────────────────────────────────

@dataclass
class ReportSummary:
    total_tests:    int
    abnormal_count: int
    critical_count: int
    has_critical:   bool

    def to_dict(self) -> dict:
        return asdict(self)


def _compute_summary(lab_values: list[dict]) -> ReportSummary:
    critical = {"CRITICAL_HIGH", "CRITICAL_LOW"}
    abnormal = {"HIGH", "LOW", "CRITICAL_HIGH", "CRITICAL_LOW"}
    return ReportSummary(
        total_tests    = len(lab_values),
        abnormal_count = sum(1 for r in lab_values if r.get("status") in abnormal),
        critical_count = sum(1 for r in lab_values if r.get("status") in critical),
        has_critical   = any(r.get("status") in critical for r in lab_values),
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

_STATUS_MAP = {"Normal": "NORMAL", "High": "HIGH", "Low": "LOW", "Unknown": "UNKNOWN"}

def _tests_analysis_to_lab_values(tests: list[dict]) -> list[dict]:
    """
    Convert tests_analysis entries into the flat lab_values shape.
    Skips entries with non-numeric values (imaging findings, text notes).
    """
    out = []
    for item in tests:
        raw_val = item.get("value", "")
        try:
            value = float(str(raw_val).replace(",", "."))
        except (TypeError, ValueError):
            continue  # non-numeric → not a lab value
        test = str(item.get("test_name", "")).strip()
        if not test:
            continue
        out.append({
            "result_type": "LAB",
            "test":   test,
            "value":  value,
            "unit":   str(item.get("unit", "")).strip(),
            "status": _STATUS_MAP.get(item.get("status", "Unknown"), "UNKNOWN"),
        })
    return out


def _collect_lab_values(sections: dict[str, list[dict]]) -> list[dict]:
    """
    Flatten lab values from all LAB sections in a mixed result.

    Source priority per section:
      1. tests_analysis  — always populated when LLM succeeded (may have
                           lab_values: [] even with 17 tests)
      2. lab_values      — populated by regex pipeline; used as fallback
                           if tests_analysis is absent or empty
    """
    out = []
    seen: set[str] = set()  # deduplicate by test name (lower)

    for report in sections.get("LAB", []):
        # Prefer tests_analysis — convert to flat lab_values shape
        tests_analysis = report.get("tests_analysis", [])
        lab_values     = report.get("lab_values",     [])

        candidates = (
            _tests_analysis_to_lab_values(tests_analysis)
            if tests_analysis
            else lab_values
        )

        for item in candidates:
            key = item.get("test", "").lower()
            if key and key not in seen:
                seen.add(key)
                out.append(item)

    return out





# ── Public API ────────────────────────────────────────────────────────────────

def assemble_report(raw: str) -> dict:
    """
    Single entry point for all uploads — mixed or single report.

    Automatically detects whether the text contains multiple report types
    (mixed PDF) or a single report, and routes accordingly.

    Mixed PDF:   split_by_category → extract_multi_section
    Single:      classify → extract (regex + LLM)
    """

    # ── Stage 1: patient header (always from raw text) ────────────────────────
    header: PatientHeader = extract_header(raw, lab_results=None)

    # ── Stage 2: detect mixed vs single ──────────────────────────────────────
    sections_map = split_by_category(raw)
    is_mixed     = len(sections_map) > 1

    # ════════════════════════════════════════════════════════════════════
    # PATH A — MIXED PDF
    # ════════════════════════════════════════════════════════════════════
    if is_mixed:
        multi_results = extract_multi_section(sections_map, gender=header.gender)

        lab_values = _collect_lab_values(multi_results)
        conditions = extract_conditions(raw) if "LAB" in multi_results else []

        if lab_values:
            header.report_type = infer_report_type(
                [r["test"] for r in lab_values if "test" in r]
            )

        summary = _compute_summary(lab_values)

        return {
            "is_mixed":      True,
            "document_type": {               # best-effort for mixed
                "category":   " + ".join(multi_results.keys()),
                "sub_type":   "MIXED",
                "confidence": "MEDIUM",
                "is_mixed":   True,
            },
            "patient":    header.to_dict(),
            "report":     {
                "report_type": "MIXED", "sub_type": "MIXED",
                "summary": "", "tests_analysis": [], "risk_level": "Unknown",
                "advice": "", "raw_text": raw,
                "metadata": {"gender": header.gender, "confidence": "LOW"},
            },
            "sections":   multi_results,     # full per-category section data
            "lab_values": lab_values,
            "conditions": conditions,
            "summary":    summary.to_dict(),
        }

    # ════════════════════════════════════════════════════════════════════
    # PATH B — SINGLE REPORT
    # ════════════════════════════════════════════════════════════════════

    # Stage 0: classify
    classification: ClassificationResult = classify(raw)

    effective_sub = classification.sub_type
    if effective_sub == "UNKNOWN" and classification.sub_scores:
        effective_sub = max(classification.sub_scores, key=classification.sub_scores.get)
    header.report_type = effective_sub

    primary = classification.category.split(" + ")[0].strip().upper()

    # Stage 2: extract
    extracted = extract(raw, category=primary, sub_type=effective_sub, gender=header.gender)

    lab_values: list[dict] = []
    conditions: list[dict] = []
    report:     dict

    if primary == "LAB":
        lab_values = extracted if isinstance(extracted, list) else []
        conditions = extract_conditions(raw)
        header.report_type = infer_report_type(
            [r["test"] for r in lab_values if "test" in r]
        )

        # Get LLM report for explanations (summary, keyword/result explanations,
        # reference_range, risk_level, advice). The regex lab_values are more
        # reliable for values/units/status — we merge both sources.
        llm_report = extract_report(raw, report_type="LAB", sub_type=effective_sub,
                                    gender=header.gender)
        
        # Build a lookup from test name → LLM tests_analysis entry
        llm_lookup: dict[str, dict] = {
            item["test_name"].lower(): item
            for item in llm_report.get("tests_analysis", [])
        }

        # Merge: regex gives accurate value/unit/status;
        #        LLM gives reference_range, keyword_explanation, result_explanation
        def _merge_status(raw_status: str) -> str:
            s = raw_status.upper()
            if s == "CRITICAL_HIGH": return "High"
            if s == "CRITICAL_LOW":  return "Low"
            return s.capitalize()

        merged_tests = []
        for r in lab_values:
            name    = r.get("test", "")
            llm_row = llm_lookup.get(name.lower(), {})
            merged_tests.append({
                "test_name":           name,
                "value":               r.get("value", ""),
                "unit":                r.get("unit", ""),
                "reference_range":     llm_row.get("reference_range", ""),
                "status":              llm_row.get("status", ""),
                "keyword_explanation": llm_row.get("keyword_explanation", ""),
                "result_explanation":  llm_row.get("result_explanation", ""),
            })

        # For any LLM-found tests not in regex results, append them too
        regex_names = {r.get("test", "").lower() for r in lab_values}
        for item in llm_report.get("tests_analysis", []):
            if item["test_name"].lower() not in regex_names:
                merged_tests.append(item)

        # Risk level: prefer regex-based status counts (more reliable),
        # fall back to LLM risk_level if no regex results
        if lab_values:
            statuses = [r.get("status", "") for r in lab_values]
            if any(s in ("CRITICAL_HIGH", "CRITICAL_LOW") for s in statuses):
                risk_level = "High"
            elif any(s in ("HIGH", "LOW") for s in statuses):
                risk_level = "Medium"
            else:
                risk_level = "Low"
        else:
            risk_level = llm_report.get("risk_level", "Unknown")

        report = {
            "report_type":    "LAB",
            "sub_type":       effective_sub,
            "summary":        llm_report.get("summary", ""),
            "tests_analysis": merged_tests,
            "risk_level":     risk_level,
            "advice":         llm_report.get("advice", ""),
            "raw_text":       raw,
            "metadata":       {
                "gender":     header.gender,
                "confidence": llm_report["metadata"]["confidence"],
            },
        }
    else:
        report = extracted if isinstance(extracted, dict) else {
            "report_type": primary, "sub_type": effective_sub,
            "summary": "", "tests_analysis": [], "risk_level": "Unknown",
            "advice": "", "raw_text": raw,
            "metadata": {"gender": header.gender, "confidence": "LOW"},
        }

    summary = _compute_summary(lab_values)

    return {
        "is_mixed":      False,
        "document_type": {
            "category":   classification.category,
            "sub_type":   classification.sub_type,
            "confidence": classification.confidence,
            "is_mixed":   classification.is_mixed,
        },
        "patient":    header.to_dict(),
        "report":     report,
        "sections":   {},        # empty for single reports
        "lab_values": lab_values,
        "conditions": conditions,
        "summary":    summary.to_dict(),
    }