"""
patient_splitter.py
────────────────────
Detects and splits a multi-patient document into per-patient text chunks.

Design principle:
  - NO separate LLM calls — splitting is pure heuristics.
  - Works with the same page-break markers your OCR service already inserts.
  - Reuses _PATIENT_START_PATTERNS aligned with patient_header.py's regex
    fallbacks so both modules agree on what a "patient boundary" looks like.

Strategy (in order of confidence):
  1. PAGE BREAK boundaries  — strongest signal; each page that contains a
     patient header is treated as a new patient record. Pages without a header
     are treated as continuation pages and merged into the previous patient.
  2. Repeated header signals — "Name:", "Patient:", "Reg No:" etc. appearing
     more than once in flat text (no page breaks).
  3. No split needed        — return [text] as-is (single patient).

Public API:
    is_multi_patient(text)   -> bool
    split_patients(text)     -> list[str]   # one str per patient, never empty
"""

from __future__ import annotations

import re
import logging

logger = logging.getLogger(__name__)

# ── Page-break marker (must match what OCRService inserts) ────────────────────
_PAGE_BREAK = "\n\n--- PAGE BREAK ---\n\n"

# Minimum chars a chunk must have to count as a real patient record.
# Shorter chunks are merged into the previous record (likely header/footer pages).
_MIN_PATIENT_CHARS = 200

# ══════════════════════════════════════════════════════════════════════════════
# PATIENT BOUNDARY PATTERNS
# Aligned with patient_header.py's regex fallbacks so both modules agree on
# what a "new patient" looks like. Each pattern must match at line start.
# ══════════════════════════════════════════════════════════════════════════════

_PATIENT_START_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE | re.MULTILINE)
    for p in [
        # Explicit "Patient Name / Patient:" label
        r"^\s*patient\s*(?:name)?\s*[:\-]\s*\S",
        # "Name: John" — Title-case name required to avoid false positives
        r"^\s*name\s*[:\-]\s*[A-Z][a-z]",
        # Salutation prefix: "Mr. John", "Mrs. Fatima"
        r"^\s*(?:mr|mrs|ms|dr)\.?\s+[A-Z][a-z]",
        # Registration / Patient ID lines
        r"^\s*reg(?:istration)?\s*(?:no|#|id)?\s*[:\-]\s*\w",
        r"^\s*patient\s*id\s*[:\-]\s*\w",
        r"^\s*pid\s*[:\-]\s*\w",
        # "Age: 45" — present in almost every Bangladeshi lab report header
        r"^\s*age\s*[:\-]\s*\d",
        # Date of birth
        r"^\s*(?:date\s*of\s*birth|dob)\s*[:\-]",
        # South Asian name formats: "S/O Ahmed", "D/O Rahman", "W/O Islam"
        r"^\s*[sdw]/o\s+\w",
    ]
]


def _page_has_patient_header(page: str) -> bool:
    """True if any patient-start pattern matches anywhere in this page."""
    return any(pat.search(page) for pat in _PATIENT_START_PATTERNS)


def _find_header_positions(text: str) -> list[int]:
    """
    Return sorted char positions where a new patient header starts.
    Snaps each match to the beginning of its line.
    Deduplicates positions within 5 chars of each other
    (multiple patterns can fire on the same line).
    """
    raw_positions: set[int] = set()
    for pattern in _PATIENT_START_PATTERNS:
        for m in pattern.finditer(text):
            line_start = text.rfind("\n", 0, m.start()) + 1
            raw_positions.add(line_start)

    sorted_pos = sorted(raw_positions)
    deduped: list[int] = []
    for pos in sorted_pos:
        if not deduped or pos - deduped[-1] > 5:
            deduped.append(pos)
    return deduped


def _merge_short_chunks(chunks: list[str]) -> list[str]:
    """
    Merge chunks that are too short (header/footer pages, cover pages)
    into the immediately preceding chunk.
    If the very first chunk is short, merge it into the second one.
    """
    if not chunks:
        return chunks

    merged = [chunks[0]]
    for chunk in chunks[1:]:
        if len(chunk.strip()) < _MIN_PATIENT_CHARS:
            merged[-1] = merged[-1] + "\n\n" + chunk
        else:
            merged.append(chunk)

    # Edge case: first chunk was a short preamble
    if len(merged) > 1 and len(merged[0].strip()) < _MIN_PATIENT_CHARS:
        merged[1] = merged[0] + "\n\n" + merged[1]
        merged = merged[1:]

    return merged


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def is_multi_patient(text: str) -> bool:
    """
    Fast heuristic check: does this document contain more than one patient?

    Returns True if:
      - Multiple page-break-delimited pages each contain a patient header, OR
      - Patient-header patterns appear >= 2 times in flat text
    """
    pages = text.split(_PAGE_BREAK)

    if len(pages) >= 2:
        pages_with_header = sum(1 for p in pages if _page_has_patient_header(p))
        if pages_with_header >= 2:
            logger.debug(
                "is_multi_patient=True: %d/%d pages have patient headers",
                pages_with_header, len(pages),
            )
            return True

    positions = _find_header_positions(text)
    if len(positions) >= 2:
        logger.debug(
            "is_multi_patient=True: %d header positions in flat text",
            len(positions),
        )
        return True

    return False


def split_patients(text: str) -> list[str]:
    """
    Split a (possibly multi-patient) document into per-patient text chunks.

    Algorithm
    ---------
    1. Page-break split (highest confidence)
       Split on _PAGE_BREAK markers. Pages that contain a patient header open
       a new patient chunk. Pages WITHOUT a header are continuation pages and
       are appended to the current patient's chunk (fixes the 3-chunk bug where
       a patient's data spans multiple pages).

    2. Header-position split (flat text, no page breaks)
       Find all positions where a patient-start pattern fires. Split there.
       Preamble text before the first header is prepended to the first patient
       chunk (it usually contains the clinic name/date which apply to all).

    3. No split
       Return [text] — single patient or unrecognised format.

    Returns
    -------
    list[str] — at least one element; each element is raw text for one patient.
                Preserves all original text so extract_header() works correctly.
    """

    # ── Strategy 1: page-break split ─────────────────────────────────────────
    pages = text.split(_PAGE_BREAK)
    if len(pages) >= 2:
        pages_with_header = [p for p in pages if _page_has_patient_header(p)]
        if len(pages_with_header) >= 2:
            logger.info(
                "split_patients: page-break strategy -> %d pages, %d with headers",
                len(pages), len(pages_with_header),
            )

            chunks: list[str] = []
            for page in pages:
                if not page.strip():
                    continue
                if _page_has_patient_header(page):
                    # This page opens a new patient record
                    chunks.append(page.strip())
                else:
                    # Continuation page — belongs to the current patient
                    if chunks:
                        chunks[-1] = chunks[-1] + "\n\n" + page.strip()
                    else:
                        # Preamble before any patient header (clinic letterhead etc.)
                        # Keep it so the first patient's extract_header() sees it
                        chunks.append(page.strip())

            return _merge_short_chunks(chunks)

    # ── Strategy 2: repeated-header split in flat text ───────────────────────
    positions = _find_header_positions(text)
    if len(positions) >= 2:
        logger.info(
            "split_patients: header-position strategy -> %d boundaries",
            len(positions),
        )
        chunks: list[str] = []

        # Text before first header (clinic letterhead, date, etc.)
        # Prepend to first patient so extract_header() sees the date/clinic.
        preamble = text[: positions[0]].strip()

        for i, start in enumerate(positions):
            end   = positions[i + 1] if i + 1 < len(positions) else len(text)
            chunk = text[start:end].strip()
            if not chunk:
                continue
            if i == 0 and preamble:
                chunk = preamble + "\n\n" + chunk
            chunks.append(chunk)

        return _merge_short_chunks(chunks) if chunks else [text]

    # ── Strategy 3: single patient ───────────────────────────────────────────
    logger.debug("split_patients: single patient, no split needed")
    return [text]