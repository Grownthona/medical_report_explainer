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
     patient header is treated as a new patient record ONLY if the patient
     name differs from the previous page. Pages without a header are treated
     as continuation pages and merged into the previous patient.
  2. Repeated header signals — "Name:", "Patient:", "Reg No:" etc. appearing
     more than once in flat text (no page breaks), with different names.
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
_MIN_PATIENT_CHARS = 200

# ══════════════════════════════════════════════════════════════════════════════
# PATIENT BOUNDARY PATTERNS
# ══════════════════════════════════════════════════════════════════════════════

_PATIENT_START_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE | re.MULTILINE)
    for p in [
        r"^\s*patient\s*(?:name)?\s*[:\-]\s*\S",
        r"^\s*name\s*[:\-]\s*[A-Z][a-z]",
        r"^\s*(?:mr|mrs|ms|dr)\.?\s+[A-Z][a-z]",
        r"^\s*reg(?:istration)?\s*(?:no|#|id)?\s*[:\-]\s*\w",
        r"^\s*patient\s*id\s*[:\-]\s*\w",
        r"^\s*pid\s*[:\-]\s*\w",
        r"^\s*age\s*[:\-]\s*\d",
        r"^\s*(?:date\s*of\s*birth|dob)\s*[:\-]",
        r"^\s*[sdw]/o\s+\w",
    ]
]

# Patterns that extract the actual patient name value from a line.
# Tried in order; first match wins.
_NAME_EXTRACT_PATTERNS: list[re.Pattern] = [
    # Stop at common field separators: newline, digit run, or keywords like Age/Lab/Gender
    re.compile(
        r"patient\s*(?:name)?\s*[:\-]\s*([A-Z][A-Z\s\.\-]{2,40}?)(?=\s*(?:age|gender|lab|invoice|reg|dob|s/o|d/o|w/o|\d|\n|$))",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*name\s*[:\-]\s*([A-Z][a-zA-Z\s\.\-]{2,40}?)(?=\s*(?:age|gender|lab|invoice|reg|dob|\d|\n|$))",
        re.IGNORECASE | re.MULTILINE,
    ),
]


def _extract_patient_name(text: str) -> str | None:
    """
    Extract and normalise the patient name from a text block.
    Returns None if no name can be found.
    """
    for pat in _NAME_EXTRACT_PATTERNS:
        m = pat.search(text)
        if m:
            name = re.sub(r"\s+", " ", m.group(1).strip()).upper()
            # Reject very short or numeric matches (false positives)
            if len(name) >= 3 and not name.isdigit():
                return name
    return None


def _names_are_different(name_a: str | None, name_b: str | None) -> bool:
    """
    Returns True only when BOTH names are known AND they are clearly different.
    If either name is unknown we conservatively return False (same person).
    """
    if not name_a or not name_b:
        return False
    # Allow small OCR noise (e.g. "GRANTHANA RAHMAN" vs "GRANTHANA RAHIMAN")
    # by requiring at least 4 chars of difference rather than exact mismatch.
    return name_a != name_b and _edit_distance_exceeds(name_a, name_b, threshold=4)


def _edit_distance_exceeds(a: str, b: str, threshold: int) -> bool:
    """
    Rough check: if the strings share a very long common prefix/suffix the
    difference is likely OCR noise, not a different person.
    Uses simple length+prefix heuristic (no full DP needed here).
    """
    if abs(len(a) - len(b)) > threshold:
        return True
    common = 0
    for ca, cb in zip(a, b):
        if ca == cb:
            common += 1
        else:
            break
    # If >80 % of the shorter string matches from the start → same person
    similarity = common / max(len(a), len(b), 1)
    return similarity < 0.80


def _page_has_patient_header(page: str) -> bool:
    """True if any patient-start pattern matches anywhere in this page."""
    return any(pat.search(page) for pat in _PATIENT_START_PATTERNS)


def _find_header_positions(text: str) -> list[int]:
    """
    Return sorted char positions where a new patient header starts.
    Snaps each match to the beginning of its line.
    Deduplicates positions within 5 chars of each other.
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
    Merge chunks that are too short (cover pages, headers-only fragments)
    into the immediately preceding chunk.

    A chunk is only merged away if it is short AND contains no patient-header
    pattern — i.e. it is purely a preamble/footer, not an actual patient record.
    Real patient records (even short ones) are always kept as their own chunk.
    """
    if not chunks:
        return chunks

    def _is_preamble(chunk: str) -> bool:
        return (
            len(chunk.strip()) < _MIN_PATIENT_CHARS
            and not _page_has_patient_header(chunk)
        )

    merged = [chunks[0]]
    for chunk in chunks[1:]:
        if _is_preamble(chunk):
            merged[-1] = merged[-1] + "\n\n" + chunk
        else:
            merged.append(chunk)

    # Edge case: first chunk is a short preamble with no patient header
    if len(merged) > 1 and _is_preamble(merged[0]):
        merged[1] = merged[0] + "\n\n" + merged[1]
        merged = merged[1:]

    return merged


# ══════════════════════════════════════════════════════════════════════════════
# CORE: identify genuine patient boundaries across pages
# ══════════════════════════════════════════════════════════════════════════════

def _find_new_patient_pages(pages: list[str]) -> list[int]:
    """
    Walk through pages and return the indices that start a NEW patient.

    A page starts a new patient only when ALL of the following are true:
      1. It contains a patient-header pattern.
      2. The patient name found on it DIFFERS from the name on the most
         recently seen patient-header page.

    Page index 0 (or the first page with a header) always opens patient #1.
    """
    new_patient_page_indices: list[int] = []
    last_known_name: str | None = None

    for i, page in enumerate(pages):
        if not _page_has_patient_header(page):
            continue  # continuation page — skip

        name = _extract_patient_name(page)

        if last_known_name is None:
            # First header seen → always opens patient #1
            new_patient_page_indices.append(i)
            last_known_name = name
        elif _names_are_different(last_known_name, name):
            # Genuinely different name → new patient
            new_patient_page_indices.append(i)
            last_known_name = name
        else:
            # Same name (or name unknown) → continuation of current patient
            logger.debug(
                "Page %d: same patient ('%s' ≈ '%s'), treating as continuation",
                i, last_known_name, name,
            )

    return new_patient_page_indices


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════════════════

def is_multi_patient(text: str) -> bool:
    """
    Returns True only if the document contains DISTINCT patients
    (different names), not just repeated headers from a multi-page report.
    """
    pages = text.split(_PAGE_BREAK)

    if len(pages) >= 2:
        new_patient_indices = _find_new_patient_pages(pages)
        if len(new_patient_indices) >= 2:
            logger.debug(
                "is_multi_patient=True: %d distinct-patient page boundaries",
                len(new_patient_indices),
            )
            return True

    # Flat-text fallback: look for distinct names at header positions
    positions = _find_header_positions(text)
    if len(positions) >= 2:
        names = set()
        for pos in positions:
            snippet = text[pos: pos + 300]
            name = _extract_patient_name(snippet)
            if name:
                names.add(name)
        if len(names) >= 2:
            # Final check: are they genuinely different?
            name_list = list(names)
            for i in range(len(name_list)):
                for j in range(i + 1, len(name_list)):
                    if _names_are_different(name_list[i], name_list[j]):
                        logger.debug(
                            "is_multi_patient=True: distinct names in flat text: %s",
                            names,
                        )
                        return True

    return False


def split_patients(text: str) -> list[str]:
    """
    Split a (possibly multi-patient) document into per-patient text chunks.

    Only splits on boundaries where the patient NAME changes.
    Pages that belong to the same patient (same name or no name found) are
    merged into one chunk, regardless of how many page-break markers exist.
    """

    # ── Strategy 1: page-break split ─────────────────────────────────────────
    pages = text.split(_PAGE_BREAK)
    if len(pages) >= 2:
        new_patient_indices = _find_new_patient_pages(pages)

        if len(new_patient_indices) >= 2:
            logger.info(
                "split_patients: page-break strategy -> %d pages, %d distinct patients",
                len(pages), len(new_patient_indices),
            )
            boundary_set = set(new_patient_indices)
            chunks: list[str] = []

            for i, page in enumerate(pages):
                if not page.strip():
                    continue
                if i in boundary_set:
                    # New patient — always open a fresh chunk
                    chunks.append(page.strip())
                else:
                    # Continuation page — belongs to the most recent patient
                    if chunks:
                        chunks[-1] = chunks[-1] + "\n\n" + page.strip()
                    else:
                        # Preamble before any patient header
                        chunks.append(page.strip())

            result = _merge_short_chunks(chunks)
            if len(result) >= 2:
                return result
            # Fall through if merging collapsed everything to 1 chunk

    # ── Strategy 2: repeated-header split in flat text (distinct names only) ─
    positions = _find_header_positions(text)
    if len(positions) >= 2:
        # Collect name per position
        named_positions: list[tuple[int, str | None]] = []
        for pos in positions:
            snippet = text[pos: pos + 300]
            named_positions.append((pos, _extract_patient_name(snippet)))

        # Walk positions; only open a new chunk when the name genuinely changes
        boundary_positions: list[int] = []
        last_name: str | None = None
        for pos, name in named_positions:
            if last_name is None:
                boundary_positions.append(pos)
                last_name = name
            elif _names_are_different(last_name, name):
                boundary_positions.append(pos)
                last_name = name
            # else: same patient, skip

        if len(boundary_positions) >= 2:
            logger.info(
                "split_patients: header-position strategy -> %d distinct boundaries",
                len(boundary_positions),
            )
            chunks: list[str] = []
            preamble = text[: boundary_positions[0]].strip()

            for i, start in enumerate(boundary_positions):
                end   = boundary_positions[i + 1] if i + 1 < len(boundary_positions) else len(text)
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