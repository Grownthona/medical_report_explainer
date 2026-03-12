from __future__ import annotations

import logging
from dataclasses import dataclass, asdict

from services.patient_header import extract_header, PatientHeader, infer_report_type
from services.extractor      import extract,extract_lab_results
from services.classifier     import classify, ClassificationResult
from services.llm_extractor  import split_by_category, extract_multi_section, extract_report

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# SERIALIZATION GUARD
# ══════════════════════════════════════════════════════════════════════════════

import dataclasses as _dc

def _to_serializable(obj):
    """
    Recursively convert any dataclass instances inside the output dict
    to plain dicts so FastAPI / json.dumps never sees a non-mapping object.
    Called as the LAST step of assemble_report() before returning.
    """
    if _dc.is_dataclass(obj) and not isinstance(obj, type):
        return _to_serializable(_dc.asdict(obj))
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_serializable(i) for i in obj]
    return obj


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY — test counts
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ReportSummary:
    total_tests:    int
    abnormal_count: int
    critical_count: int
    has_critical:   bool

    def to_dict(self) -> dict:
        return asdict(self)


def _compute_summary(tests_analysis: list[dict]) -> ReportSummary:
    """Compute summary counts from tests_analysis entries."""
    _ABNORMAL = {"High", "Low", "HIGH", "LOW", "CRITICAL_HIGH", "CRITICAL_LOW"}
    _CRITICAL  = {"CRITICAL_HIGH", "CRITICAL_LOW"}
    return ReportSummary(
        total_tests    = len(tests_analysis),
        abnormal_count = sum(1 for t in tests_analysis
                             if t.get("status", "").upper() in
                             {s.upper() for s in _ABNORMAL}),
        critical_count = sum(1 for t in tests_analysis
                             if t.get("status", "").upper() in _CRITICAL),
        has_critical   = any(t.get("status", "").upper() in _CRITICAL
                             for t in tests_analysis),
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _merge_status(raw_status: str) -> str:
    """Normalise UPPERCASE regex statuses to Title-case for unified output."""
    s = raw_status.upper()
    if s in ("CRITICAL_HIGH", "HIGH"): return "High"
    if s in ("CRITICAL_LOW",  "LOW"):  return "Low"
    if s == "NORMAL":                  return "Normal"
    return "Unknown"


def _build_merged_tests(lab_values: list[dict], llm_report: dict) -> list[dict]:
    """
    Merge regex lab_values (accurate numbers) with LLM tests_analysis
    (explanations, reference_range). Regex wins on value/unit/status.
    LLM fills reference_range, keyword_explanation, result_explanation.
    LLM-only tests (missed by regex) are appended at the end.
    """
    llm_lookup: dict[str, dict] = {
        item["test_name"].lower(): item
        for item in llm_report.get("tests_analysis", [])
    }

    merged = []
    for r in lab_values:
        name    = r.get("test", "")
        llm_row = llm_lookup.get(name.lower(), {})
        merged.append({
            "test_name":           name,
            "value":               r.get("value", ""),
            "unit":                r.get("unit", ""),
            "reference_range":     llm_row.get("reference_range", ""),
            "status":              _merge_status(r.get("status", "Unknown")),
            "keyword_explanation": llm_row.get("keyword_explanation", ""),
            "result_explanation":  llm_row.get("result_explanation", ""),
        })

    # Append any LLM-found tests the regex missed
    regex_names = {r.get("test", "").lower() for r in lab_values}
    for item in llm_report.get("tests_analysis", []):
        if item["test_name"].lower() not in regex_names:
            merged.append(item)

    return merged


def _risk_from_lab_values(lab_values: list[dict]) -> str:
    """Derive risk level from regex-based statuses (reliable, no hallucination)."""
    statuses = [r.get("status", "") for r in lab_values]
    if any(s in ("CRITICAL_HIGH", "CRITICAL_LOW") for s in statuses):
        return "High"
    if any(s in ("HIGH", "LOW") for s in statuses):
        return "Medium"
    return "Low"


def _strip_internal_fields(report: dict) -> dict:
    """
    Return only the fields that belong in the final "report" key.
    Drops report_type, sub_type, metadata — those live in document_type/patient.
    """
    keep = {"summary", "voice_explanation", "tests_analysis", "risk_level", "advice", "raw_text"}
    return {k: v for k, v in report.items() if k in keep}


_STATUS_MAP = {"Normal": "NORMAL", "High": "HIGH", "Low": "LOW", "Unknown": "UNKNOWN"}


def _tests_analysis_to_lab_values(tests: list[dict]) -> list[dict]:
    """
    Convert tests_analysis entries (LLM output) into the flat lab_values shape
    { result_type, test, value, unit, status } used by the rest of the pipeline.
    Skips non-numeric values (imaging findings, text notes).
    """
    out = []
    for item in tests:
        raw_val = item.get("value", "")
        try:
            value = float(str(raw_val).replace(",", "."))
        except (TypeError, ValueError):
            continue
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

    Priority per section:
      1. tests_analysis — always populated when LLM succeeded.
         (lab_values may be [] even when 17 tests are present in tests_analysis)
      2. lab_values     — regex pipeline output; used as fallback only.

    Deduplicates by test name across all sections.
    """
    out  = []
    seen: set[str] = set()

    for report in sections.get("LAB", []):
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


def _collect_mixed_tests_analysis(multi_results: dict[str, list[dict]]) -> list[dict]:
    """
    For mixed PDFs: flatten all tests_analysis from all sections into one list.
    Used to compute the top-level summary counts.
    """
    out = []
    seen: set[str] = set()
    for section_list in multi_results.values():
        for report in section_list:
            for item in report.get("tests_analysis", []):
                key = item.get("test_name", "").lower()
                if key and key not in seen:
                    seen.add(key)
                    out.append(item)
    return out


# ── Public API ────────────────────────────────────────────────────────────────

def assemble_report(raw: str, language: str = "en") -> dict:
    """
    Single entry point for all uploads — mixed or single report.
 
    Args:
        raw:      Raw OCR or report text.
        language: Response language passed to LLM ("en", "bn", "ar", "hi", "ur").
                  Defaults to "en". Forwarded to extract_report() and extract_header().
 
    Auto-detects mixed PDF vs single report via split_by_category().
    Returns a unified dict in the documented output shape.
    """
 
    # ── Stage 1: patient header ───────────────────────────────────────────────
    header: PatientHeader = extract_header(raw, lab_results=None)
 
    # ── Stage 2: mixed vs single detection ───────────────────────────────────
    sections_map = split_by_category(raw)
    is_mixed     = len(sections_map) > 1
 
    # ═════════════════════════════════════════════════════════════════════
    # PATH A — MIXED PDF
    # ═════════════════════════════════════════════════════════════════════
    if is_mixed:
        multi_results = extract_multi_section(sections_map, gender=header.gender, language=language)
 
        # Flatten all tests across all sections for summary counts
        all_tests = _collect_mixed_tests_analysis(multi_results)
 
        # Set patient report_type from LAB tests if present
        lab_test_names = [
            t["test_name"]
            for report in multi_results.get("LAB", [])
            for t in report.get("tests_analysis", [])
        ]
        if lab_test_names:
            header.report_type = infer_report_type(lab_test_names)
 
        # Build a minimal top-level report (full detail is in sections)
        mixed_report = {
            "summary":        " | ".join(
                r.get("summary", "")
                for section_list in multi_results.values()
                for r in section_list
                if r.get("summary")
            ),
            "voice_explanation": next(
                (r.get("voice_explanation", "")
                 for section_list in multi_results.values()
                 for r in section_list
                 if r.get("voice_explanation")),
                ""
            ),
            "tests_analysis": all_tests,
            "risk_level":     (
                "High"   if any(t.get("status") in ("High", "CRITICAL_HIGH", "CRITICAL_LOW")
                                for t in all_tests) else
                "Medium" if any(t.get("status") in ("Low", "HIGH", "LOW")
                                for t in all_tests) else
                "Low"
            ),
            "advice":         " | ".join(
                r.get("advice", "")
                for section_list in multi_results.values()
                for r in section_list
                if r.get("advice")
            ),
            "raw_text": raw,
        }
 
        return _to_serializable({
            "is_mixed":      True,
            "document_type": {
                "category":   " + ".join(multi_results.keys()),
                "sub_type":   "MIXED",
                "confidence": "MEDIUM",
                "is_mixed":   True,
            },
            "patient":  header.to_dict(),
            "report":   mixed_report,
            "sections": multi_results,   # full per-category detail
            "summary":  _compute_summary(all_tests).to_dict(),
        })
 
    # ═════════════════════════════════════════════════════════════════════
    # PATH B — SINGLE REPORT
    # ═════════════════════════════════════════════════════════════════════
 
    # Classify
    classification: ClassificationResult = classify(raw)
 
    effective_sub = classification.sub_type
    if effective_sub == "UNKNOWN" and classification.sub_scores:
        effective_sub = max(classification.sub_scores, key=classification.sub_scores.get)
 
    primary = classification.category.split(" + ")[0].strip().upper()

    # ── LAB: regex values + one LLM call for explanations ───────────────────
    if primary == "LAB":
        lab_values = extract_lab_results(raw, gender=header.gender)
        
        header.report_type = infer_report_type(
            [r["test"] for r in lab_values if "test" in r]
        )
 
        llm_report   = extract_report(raw, report_type="LAB",
                                      sub_type=effective_sub, gender=header.gender,
                                      language=language)
        merged_tests = _build_merged_tests(lab_values, llm_report)
 
        report = {
            "summary":           llm_report.get("summary", ""),
            "voice_explanation": llm_report.get("voice_explanation", ""),
            "tests_analysis":    merged_tests,
            "risk_level":        (_risk_from_lab_values(lab_values)
                                  if lab_values
                                  else llm_report.get("risk_level", "Unknown")),
            "advice":            llm_report.get("advice", ""),
            "raw_text":          raw,
        }
 
    # ── Non-LAB: one LLM call via extract() ──────────────────────────────────
    else:
        header.report_type = effective_sub
        extracted  = extract(raw, category=primary, sub_type=effective_sub,
                             gender=header.gender, language=language)
        raw_report = extracted if isinstance(extracted, dict) else {}
        report = _strip_internal_fields(raw_report) or {
            "summary":           "",
            "voice_explanation": "",
            "tests_analysis":    [],
            "risk_level":        "Unknown",
            "advice":            "",
            "raw_text":          raw,
        }
        report.setdefault("raw_text", raw)
 
    return _to_serializable({
        "is_mixed":      False,
        "document_type": {
            "category":   classification.category,
            "sub_type":   classification.sub_type,
            "confidence": classification.confidence,
            "is_mixed":   classification.is_mixed,
        },
        "patient":  header.to_dict(),
        "report":   report,
        "sections": {},
        "summary":  _compute_summary(report.get("tests_analysis", [])).to_dict(),
    })
 
