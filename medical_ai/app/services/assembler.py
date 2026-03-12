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
    _ABNORMAL = {"high", "low", "critical_high", "critical_low"}
    _CRITICAL  = {"critical_high", "critical_low"}
    return ReportSummary(
        total_tests    = len(tests_analysis),
        abnormal_count = sum(1 for t in tests_analysis
                             if t.get("status", "").lower() in _ABNORMAL),
        critical_count = sum(1 for t in tests_analysis
                             if t.get("status", "").lower() in _CRITICAL),
        has_critical   = any(t.get("status", "").lower() in _CRITICAL
                             for t in tests_analysis),
    )


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _merge_status(raw_status: str) -> str:
    s = raw_status.upper()
    if s in ("CRITICAL_HIGH", "HIGH"): return "High"
    if s in ("CRITICAL_LOW",  "LOW"):  return "Low"
    if s == "NORMAL":                  return "Normal"
    return "Unknown"


def _build_merged_tests(regex_hits: list[dict], llm_report: dict) -> list[dict]:
    """
    Merge regex lab values (accurate numbers) with LLM tests_analysis
    (explanations, reference_range). Regex wins on value/unit/status.
    LLM-only tests appended at the end.
    """
    llm_lookup: dict[str, dict] = {
        item["test_name"].lower(): item
        for item in llm_report.get("tests_analysis", [])
    }
    merged = []
    for r in regex_hits:
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
    regex_names = {r.get("test", "").lower() for r in regex_hits}
    for item in llm_report.get("tests_analysis", []):
        if item.get("test_name", "").lower() not in regex_names:
            merged.append(item)
    return merged


def _risk_from_regex(regex_hits: list[dict]) -> str:
    statuses = [r.get("status", "") for r in regex_hits]
    if any(s in ("CRITICAL_HIGH", "CRITICAL_LOW") for s in statuses): return "High"
    if any(s in ("HIGH", "LOW") for s in statuses):                   return "Medium"
    return "Low"


def _strip_internal_fields(report: dict) -> dict:
    keep = {"summary", "voice_explanation", "tests_analysis", "risk_level", "advice", "raw_text"}
    return {k: v for k, v in report.items() if k in keep}


# Fields that are internal pipeline data — never sent to the client
_SECTION_STRIP = {"metadata", "raw_text", "regex_lab_values"}

def _clean_section(section: dict) -> dict:
    """Remove internal fields from a section before returning to client."""
    return {k: v for k, v in section.items() if k not in _SECTION_STRIP}


def _collect_all_tests(multi_results: dict[str, list[dict]]) -> list[dict]:
    """
    Flatten tests_analysis from all sections.
    For LAB sections, first applies _build_merged_tests so the client always
    gets the regex-accurate values merged with LLM explanations.
    Deduplicates by test_name.
    """
    out:  list[dict] = []
    seen: set[str]   = set()

    for category, section_list in multi_results.items():
        for section in section_list:
            if category == "LAB":
                regex_hits = section.get("regex_lab_values", [])
                tests      = _build_merged_tests(regex_hits, section)
            else:
                tests = section.get("tests_analysis", [])

            for item in tests:
                key = item.get("test_name", "").lower()
                if key and key not in seen:
                    seen.add(key)
                    out.append(item)

    return out


# ══════════════════════════════════════════════════════════════════════════════
# SINGLE-PATIENT CORE
# ══════════════════════════════════════════════════════════════════════════════

def _assemble_single(raw: str, language: str = "en") -> dict:
    header: PatientHeader = extract_header(raw, lab_results=None)

    sections_map = split_by_category(raw)
    is_mixed     = len(sections_map) > 1

    # ── PATH A: mixed (multiple categories in one document) ───────────────────
    if is_mixed:
        multi_results = extract_multi_section(
            sections_map, gender=header.gender, language=language
        )

        # Collect merged tests for summary counts + report_type inference
        all_tests = _collect_all_tests(multi_results)

        lab_test_names = [
            t["test_name"]
            for section in multi_results.get("LAB", [])
            for t in section.get("tests_analysis", [])
        ]
        if lab_test_names:
            header.report_type = infer_report_type(lab_test_names)

        # Strip internal fields from each section before returning
        clean_sections = {
            cat: [_clean_section(s) for s in section_list]
            for cat, section_list in multi_results.items()
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
            "sections": clean_sections,
            "summary":  _compute_summary(all_tests).to_dict(),
        }

    # ── PATH B: single-category ───────────────────────────────────────────────
    classification: ClassificationResult = classify(raw)

    effective_sub = classification.sub_type
    if effective_sub == "UNKNOWN" and classification.sub_scores:
        effective_sub = max(classification.sub_scores, key=classification.sub_scores.get)

    primary = classification.category.split(" + ")[0].strip().upper()

    if primary == "LAB":
        # Regex pass (CPU, no network) + one LLM call
        regex_hits = extract_lab_results(raw, gender=header.gender)
        header.report_type = infer_report_type(
            [r["test"] for r in regex_hits if "test" in r]
        )
        llm_report   = extract_report(
            raw, report_type="LAB",
            sub_type=effective_sub, gender=header.gender,
            language=language,
        )
        merged_tests = _build_merged_tests(regex_hits, llm_report)
        report = {
            "summary":           llm_report.get("summary", ""),
            "voice_explanation": llm_report.get("voice_explanation", ""),
            "tests_analysis":    merged_tests,
            "risk_level":        (_risk_from_regex(regex_hits)
                                  if regex_hits
                                  else llm_report.get("risk_level", "Unknown")),
            "advice":            llm_report.get("advice", ""),
            "raw_text":          raw,
        }
    else:
        header.report_type = effective_sub
        extracted  = extract(raw, category=primary, sub_type=effective_sub,
                             gender=header.gender, language=language)
        raw_report = extracted if isinstance(extracted, dict) else {}
        report     = _strip_internal_fields(raw_report) or {
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
    Single entry point. Handles single-patient, multi-patient, and mixed docs.

    Response — single patient, single category:
        { is_multi_patient, is_mixed, document_type, patient, report, sections, summary }

    Response — single patient, mixed categories:
        { is_multi_patient, is_mixed, document_type, patient, sections, summary }
        (no top-level report — read per-category data from sections)

    Response — multiple patients:
        { is_multi_patient: true, total_patients, patients: [ ... ] }
    """
    if is_multi_patient(raw):
        chunks  = split_patients(raw)
        logger.info("Multi-patient: %d chunks, processing in parallel", len(chunks))

        results: list[dict | None] = [None] * len(chunks)

        with ThreadPoolExecutor(max_workers=min(len(chunks), 5)) as pool:
            future_map = {
                pool.submit(_assemble_single, chunk, language): idx
                for idx, chunk in enumerate(chunks)
            }
            for future in as_completed(future_map):
                idx = future_map[future]
                try:
                    r = future.result()
                    r["patient_index"] = idx
                    results[idx] = r
                except Exception as e:
                    logger.error("Patient chunk %d failed: %s", idx, e)
                    results[idx] = {
                        "patient_index": idx,
                        "is_mixed":      False,
                        "document_type": {"category": "UNKNOWN", "sub_type": "UNKNOWN",
                                          "confidence": "LOW", "is_mixed": False},
                        "patient":       {"name": None, "age_years": None, "gender": "unknown",
                                          "report_type": None, "collection_date": None},
                        "report":        {"summary": "", "voice_explanation": "",
                                          "tests_analysis": [], "risk_level": "Unknown",
                                          "advice": "", "raw_text": chunks[idx]},
                        "sections":      {},
                        "summary":       {"total_tests": 0, "abnormal_count": 0,
                                          "critical_count": 0, "has_critical": False},
                        "error":         str(e),
                    }

        return _to_serializable({
            "is_multi_patient": True,
            "total_patients":   len(chunks),
            "patients":         [r for r in results if r is not None],
        })

    result = _assemble_single(raw, language=language)
    result["is_multi_patient"] = False
    return _to_serializable(result)