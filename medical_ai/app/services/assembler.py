from __future__ import annotations

import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict

from services.patient_header   import extract_header, PatientHeader, infer_report_type
from services.extractor        import extract, extract_lab_results
from services.classifier       import classify, ClassificationResult
from services.llm_extractor    import split_by_category, extract_multi_section, extract_report
from services.patient_splitter import is_multi_patient, split_patients
from services.xray_assembler   import assemble_xray_report

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


def _normalise_test_name(name: str) -> str:
    """Strip parenthetical aliases and common suffixes for matching."""
    name = name.lower().strip()
    name = re.sub(r'\s*\(.*?\)', '', name)          # remove "(Good)", "(SGPT)" etc.
    name = re.sub(r'\b(total|serum|fasting)\b', '', name)
    return name.strip()

# def _build_merged_tests(regex_hits: list[dict], llm_report: dict) -> list[dict]:
#     # Build lookup with BOTH exact and normalised keys
#     llm_lookup: dict[str, dict] = {}
#     for item in llm_report.get("tests_analysis", []):
#         exact = item["test_name"].lower()
#         norm  = _normalise_test_name(item["test_name"])
#         llm_lookup[exact] = item
#         llm_lookup[norm]  = item          # second key for fuzzy matching

#     merged = []
#     seen_norm: set[str] = set()           # ← track normalised names to skip dupes

#     for r in regex_hits:
#         name = r.get("test", "")
#         norm = _normalise_test_name(name)
#         if norm in seen_norm:
#             continue
#         seen_norm.add(norm)

#         llm_row = llm_lookup.get(name.lower()) or llm_lookup.get(norm, {})

#         # ↓ Replace the old single "status" line with these two lines:
#         llm_status = llm_row.get("status", "")
#         has_ref    = bool(llm_row.get("reference_range", "").strip())
#         status     = llm_status if (has_ref and llm_status) else _merge_status(r.get("status", "Unknown"))

#         merged.append({
#             "test_name":           name,
#             "value":               r.get("value", ""),
#             "unit":                r.get("unit", ""),
#             "reference_range":     llm_row.get("reference_range", ""),
#             "status":              status,   # ← use the variable, not _merge_status() inline
#             "keyword_explanation": llm_row.get("keyword_explanation", ""),
#             "result_explanation":  llm_row.get("result_explanation", ""),
#         })

#     regex_names_norm = {_normalise_test_name(r.get("test", "")) for r in regex_hits}
#     for item in llm_report.get("tests_analysis", []):
#         if _normalise_test_name(item.get("test_name", "")) not in regex_names_norm:
#             merged.append(item)

#     return merged

def _build_merged_tests(regex_hits: list[dict], llm_report: dict) -> list[dict]:
    merged = []
    for item in llm_report.get("tests_analysis", []):
        merged.append({
            "test_name":           item.get("test_name", ""),
            "value":               item.get("value", ""),
            "unit":                item.get("unit", ""),
            "reference_range":     item.get("reference_range", ""),
            "status":              item.get("status", ""),
            "keyword_explanation": item.get("keyword_explanation", ""),
            "result_explanation":  item.get("result_explanation", ""),
        })
    return merged



def _risk_from_regex(regex_hits: list[dict]) -> str:
    statuses = [r.get("status", "") for r in regex_hits]
    if any(s in ("CRITICAL_HIGH", "CRITICAL_LOW") for s in statuses): return "High"
    if any(s in ("HIGH", "LOW") for s in statuses):                   return "Medium"
    return "Low"


def _strip_internal_fields(report: dict) -> dict:
    keep = {"section_title", "summary", "voice_explanation", "tests_analysis", "risk_level", "advice", "raw_text"}
    return {k: v for k, v in report.items() if k in keep}


_SECTION_STRIP = {"metadata", "raw_text", "regex_lab_values"}

def _clean_section(section: dict) -> dict:
    return {k: v for k, v in section.items() if k not in _SECTION_STRIP}


def _collect_all_tests(multi_results: dict[str, list[dict]]) -> list[dict]:
    out:  list[dict] = []
    seen: set[str]   = set()

    for category, section_list in multi_results.items():
        for section in section_list:
            if category == "LAB":
                regex_hits = section.get("regex_lab_values", [])
                tests      = _build_merged_tests(regex_hits, section)
            else:
                # XRAY and all other sections: read tests_analysis directly
                tests = section.get("tests_analysis", [])

            for item in tests:
                key = item.get("test_name", "").lower()
                if key and key not in seen:
                    seen.add(key)
                    out.append(item)

    return out


# ══════════════════════════════════════════════════════════════════════════════
# XRAY SECTION BUILDER
# Converts assemble_xray_report() output into the same section shape
# used by text sections so _collect_all_tests / _clean_section work uniformly.
# ══════════════════════════════════════════════════════════════════════════════

def _build_xray_section(xray_result: dict, language: str) -> dict:
    """
    Call assemble_xray_report() and reshape its report{} block into the
    flat section shape used by multi-section text reports:

        {
            summary, voice_explanation, tests_analysis,
            risk_level, advice, model, disclaimer, all_findings
        }

    This section is then stored under sections["XRAY"] — identical in
    structure to sections["LAB"], sections["IMAGING"], etc.
    """
    assembled = assemble_xray_report(xray_result, language=language)
    report    = assembled.get("report", {})

    return {
        "section_title":     report.get("section_title",""),
        "summary":           report.get("summary",           ""),
        "voice_explanation": report.get("voice_explanation", ""),
        "tests_analysis":    report.get("tests_analysis",    []),
        "risk_level":        report.get("risk_level",        "Unknown"),
        "advice":            report.get("advice",            ""),
        # X-ray-specific extras — kept in section, not in tests_analysis
        "model":             report.get("model",             ""),
        "disclaimer":        report.get("disclaimer",        ""),
        "all_findings":      report.get("all_findings",      []),
    }


# ══════════════════════════════════════════════════════════════════════════════
# SINGLE-PATIENT CORE
# ══════════════════════════════════════════════════════════════════════════════

def _assemble_single(
    raw:         str,
    language:    str        = "en",
    xray_result: dict|None  = None,
) -> dict:
    """
    Assemble a single-patient report.

    xray_result: if provided, the X-ray findings are added as a XRAY section
                 alongside whatever text sections the document contains.
                 If raw is empty and xray_result is present the response is
                 XRAY-only with sections: { "XRAY": [...] }.
    """
    has_text = bool(raw and raw.strip())
    has_xray = xray_result is not None

    # ── XRAY only (no text) ───────────────────────────────────────────────────
    if has_xray and not has_text:
        xray_section = _build_xray_section(xray_result, language)
        all_tests    = xray_section.get("tests_analysis", [])
        return {
            "is_mixed":      False,
            "document_type": {
                "category":   "XRAY",
                "sub_type":   "CHEST_XRAY",
                "confidence": "HIGH",
                "is_mixed":   False,
            },
            "patient":  {
                "name": None, "age_years": None, "gender": "unknown",
                "report_type": "Chest X-Ray", "collection_date": None,
            },
            "report":   xray_section,   # ← was: "sections": {"XRAY": [xray_section]}
            "sections": {},             # ← added
            "summary":  _compute_summary(all_tests).to_dict(),
        }

    # ── Text pipeline ─────────────────────────────────────────────────────────
    header: PatientHeader = extract_header(raw, lab_results=None)
    sections_map          = split_by_category(raw)
    is_mixed              = len(sections_map) > 1 or has_xray  # xray forces mixed

    # ── PATH A: mixed — multiple text categories OR text + xray ──────────────
    if is_mixed:
        multi_results = extract_multi_section(
            sections_map, gender=header.gender, language=language
        )

        # Inject XRAY section alongside the text sections
        if has_xray:
            xray_section = _build_xray_section(xray_result, language)
            multi_results["XRAY"] = [xray_section]

        all_tests = _collect_all_tests(multi_results)

        lab_test_names = [
            t["test_name"]
            for section in multi_results.get("LAB", [])
            for t in section.get("tests_analysis", [])
        ]
        if lab_test_names:
            header.report_type = infer_report_type(lab_test_names)

        # Build category label — include XRAY in the display string if present
        category_label = " + ".join(multi_results.keys())

        clean_sections = {
            cat: [_clean_section(s) for s in section_list]
            for cat, section_list in multi_results.items()
        }

        return {
            "is_mixed":      True,
            "document_type": {
                "category":   category_label,
                "sub_type":   "MIXED",
                "confidence": "MEDIUM",
                "is_mixed":   True,
            },
            "patient":  header.to_dict(),
            "sections": clean_sections,
            "summary":  _compute_summary(all_tests).to_dict(),
        }

    # ── PATH B: single-category text (no xray) ────────────────────────────────
    classification: ClassificationResult = classify(raw)

    effective_sub = classification.sub_type
    if effective_sub == "UNKNOWN" and classification.sub_scores:
        effective_sub = max(classification.sub_scores, key=classification.sub_scores.get)

    primary = classification.category.split(" + ")[0].strip().upper()

    if primary == "LAB":
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
            "section_title":     llm_report.get("section_title",""),
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
            "section_title":     "",
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

def assemble_report(
    raw:         str        = "",
    language:    str        = "en",
    *,
    xray_result: dict|None  = None,
) -> dict:
    
    return _run_text_pipeline(raw, language, xray_result=xray_result)


def _run_text_pipeline(
    raw:         str,
    language:    str,
    xray_result: dict|None = None,
) -> dict:

    if is_multi_patient(raw):
        chunks = split_patients(raw)
        logger.info("Multi-patient: %d chunks", len(chunks))

        results: list[dict | None] = [None] * len(chunks)

        with ThreadPoolExecutor(max_workers=min(len(chunks), 5)) as pool:
            future_map = {
                # Only pair xray_result with the first patient chunk
                pool.submit(
                    _assemble_single, chunk, language,
                    xray_result if idx == 0 else None,
                ): idx
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

    result = _assemble_single(raw, language=language, xray_result=xray_result)
    result["is_multi_patient"] = False
    return _to_serializable(result)