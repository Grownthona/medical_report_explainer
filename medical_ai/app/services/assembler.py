from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict

from services.patient_header   import extract_header, PatientHeader, infer_report_type
from services.extractor        import extract, extract_lab_results
from services.classifier       import classify, ClassificationResult
from services.llm_extractor    import split_by_category, extract_multi_section, extract_report
from services.patient_splitter import is_multi_patient, split_patients

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# SERIALIZATION GUARD
# ══════════════════════════════════════════════════════════════════════════════

import dataclasses as _dc

def _to_serializable(obj):
    if _dc.is_dataclass(obj) and not isinstance(obj, type):
        return _to_serializable(_dc.asdict(obj))
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_serializable(i) for i in obj]
    return obj


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
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
    s = raw_status.upper()
    if s in ("CRITICAL_HIGH", "HIGH"): return "High"
    if s in ("CRITICAL_LOW",  "LOW"):  return "Low"
    if s == "NORMAL":                  return "Normal"
    return "Unknown"


def _build_merged_tests(lab_values: list[dict], llm_report: dict) -> list[dict]:
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
    regex_names = {r.get("test", "").lower() for r in lab_values}
    for item in llm_report.get("tests_analysis", []):
        if item["test_name"].lower() not in regex_names:
            merged.append(item)
    return merged


def _risk_from_lab_values(lab_values: list[dict]) -> str:
    statuses = [r.get("status", "") for r in lab_values]
    if any(s in ("CRITICAL_HIGH", "CRITICAL_LOW") for s in statuses):
        return "High"
    if any(s in ("HIGH", "LOW") for s in statuses):
        return "Medium"
    return "Low"


def _strip_internal_fields(report: dict) -> dict:
    keep = {"summary", "voice_explanation", "tests_analysis", "risk_level", "advice", "raw_text"}
    return {k: v for k, v in report.items() if k in keep}


def _collect_mixed_tests_analysis(multi_results: dict[str, list[dict]]) -> list[dict]:
    out  = []
    seen: set[str] = set()
    for section_list in multi_results.values():
        for report in section_list:
            for item in report.get("tests_analysis", []):
                key = item.get("test_name", "").lower()
                if key and key not in seen:
                    seen.add(key)
                    out.append(item)
    return out


# ══════════════════════════════════════════════════════════════════════════════
# SINGLE-PATIENT CORE
# ══════════════════════════════════════════════════════════════════════════════

def _assemble_single(raw: str, language: str = "en") -> dict:
    """
    Full pipeline for exactly one patient's text.
    Called directly for single-patient docs, and from the thread pool
    for each chunk in multi-patient docs.
    """
    header: PatientHeader = extract_header(raw, lab_results=None)

    sections_map = split_by_category(raw)
    is_mixed     = len(sections_map) > 1

    # ── PATH A: mixed report ──────────────────────────────────────────────────
    if is_mixed:
        multi_results = extract_multi_section(
            sections_map, gender=header.gender, language=language
        )
        all_tests = _collect_mixed_tests_analysis(multi_results)

        lab_test_names = [
            t["test_name"]
            for report in multi_results.get("LAB", [])
            for t in report.get("tests_analysis", [])
        ]
        if lab_test_names:
            header.report_type = infer_report_type(lab_test_names)

        mixed_report = {
            "summary": " | ".join(
                r.get("summary", "")
                for section_list in multi_results.values()
                for r in section_list if r.get("summary")
            ),
            "voice_explanation": next(
                (r.get("voice_explanation", "")
                 for section_list in multi_results.values()
                 for r in section_list if r.get("voice_explanation")),
                "",
            ),
            "tests_analysis": all_tests,
            "risk_level": (
                "High"   if any(t.get("status") in ("High", "CRITICAL_HIGH", "CRITICAL_LOW")
                                for t in all_tests) else
                "Medium" if any(t.get("status") in ("Low", "HIGH", "LOW")
                                for t in all_tests) else
                "Low"
            ),
            "advice": " | ".join(
                r.get("advice", "")
                for section_list in multi_results.values()
                for r in section_list if r.get("advice")
            ),
            "raw_text": raw,
        }

        return {
            "is_mixed":      True,
            "document_type": {
                "category":   " + ".join(multi_results.keys()),
                "sub_type":   "MIXED",
                "confidence": "MEDIUM",
                "is_mixed":   True,
            },
            "patient":  header.to_dict(),
            "report":   mixed_report,
            "sections": multi_results,
            "summary":  _compute_summary(all_tests).to_dict(),
        }

    # ── PATH B: single-category ───────────────────────────────────────────────
    classification: ClassificationResult = classify(raw)

    effective_sub = classification.sub_type
    if effective_sub == "UNKNOWN" and classification.sub_scores:
        effective_sub = max(classification.sub_scores, key=classification.sub_scores.get)

    primary = classification.category.split(" + ")[0].strip().upper()

    if primary == "LAB":
        lab_values = extract_lab_results(raw, gender=header.gender)
        header.report_type = infer_report_type(
            [r["test"] for r in lab_values if "test" in r]
        )
        llm_report   = extract_report(
            raw, report_type="LAB",
            sub_type=effective_sub, gender=header.gender,
            language=language,
        )
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

    return {
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
    }


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def assemble_report(raw: str, language: str = "en") -> dict:
    """
    Single entry point for all uploads.

    Multi-patient detection
    -----------------------
    split_patients() is pure heuristics (zero LLM cost). If multiple patients
    are found, each chunk is processed by _assemble_single() in parallel via
    ThreadPoolExecutor (same parallelism used for multi-section mixed PDFs).

    Response shape
    --------------
    Single patient (unchanged existing shape):
        {
            "is_multi_patient": false,
            "is_mixed":         bool,
            "document_type":    { category, sub_type, confidence, is_mixed },
            "patient":          { name, age_years, gender, report_type,
                                  collection_date, referred_by, lab_no, invoice_no },
            "report":           { summary, voice_explanation, tests_analysis,
                                  risk_level, advice, raw_text },
            "sections":         { ... },
            "summary":          { total_tests, abnormal_count, critical_count,
                                  has_critical }
        }

    Multiple patients (new wrapper):
        {
            "is_multi_patient": true,
            "total_patients":   int,
            "patients": [
                {
                    "patient_index": 0,     <- 0-based position in document
                    "is_mixed":      bool,
                    "document_type": { ... },
                    "patient":       { ... },
                    "report":        { ... },
                    "sections":      { ... },
                    "summary":       { ... }
                },
                ...
            ]
        }
    """

    # ── Multi-patient check (heuristic, no LLM) ───────────────────────────────
    if is_multi_patient(raw):
        chunks = split_patients(raw)
        logger.info(
            "Multi-patient document: %d patients found, processing in parallel",
            len(chunks),
        )

        results: list[dict | None] = [None] * len(chunks)

        with ThreadPoolExecutor(max_workers=min(len(chunks), 5)) as pool:
            future_to_idx = {
                pool.submit(_assemble_single, chunk, language): idx
                for idx, chunk in enumerate(chunks)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    result = future.result()
                    result["patient_index"] = idx
                    results[idx] = result
                except Exception as e:
                    logger.error("Patient chunk %d failed: %s", idx, e)
                    results[idx] = {
                        "patient_index": idx,
                        "is_mixed":      False,
                        "document_type": {
                            "category": "UNKNOWN", "sub_type": "UNKNOWN",
                            "confidence": "LOW",   "is_mixed": False,
                        },
                        "patient": {
                            "name": None, "age_years": None, "gender": "unknown",
                            "report_type": None, "collection_date": None,
                        },
                        "report": {
                            "summary": "", "voice_explanation": "",
                            "tests_analysis": [], "risk_level": "Unknown",
                            "advice": "", "raw_text": chunks[idx],
                        },
                        "sections": {},
                        "summary": {
                            "total_tests": 0, "abnormal_count": 0,
                            "critical_count": 0, "has_critical": False,
                        },
                        "error": str(e),
                    }

        return _to_serializable({
            "is_multi_patient": True,
            "total_patients":   len(chunks),
            "patients":         [r for r in results if r is not None],
        })

    # ── Single patient (original path, unchanged) ─────────────────────────────
    result = _assemble_single(raw, language=language)
    result["is_multi_patient"] = False
    return _to_serializable(result)