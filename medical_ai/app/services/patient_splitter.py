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
# POSSESSIVE STRIPPING
# Prevents "Mrs. Little's family" from being read as a new patient header.
#
# Two-pass strip — longest match first.
# Pass 1: "'s" / "\u2019s" possessives  e.g. "Mrs. Little's"
# Pass 2: bare "'" possessives           e.g. "Dr. Jones'"  (names ending in s)
# A two-pass approach avoids variable-width lookbehinds (rejected by Python
# 3.10's `re` module) and handles both straight (') and curly (\u2019) quotes.
# ══════════════════════════════════════════════════════════════════════════════

_POSSESSIVE_S_RE = re.compile(
    r"((?:mr|mrs|ms|dr)\.?\s{1,2}[A-Z][a-z]{1,20})['\u2019]s(?=\W|$)",
    re.IGNORECASE,
)
_POSSESSIVE_APO_RE = re.compile(
    r"((?:mr|mrs|ms|dr)\.?\s{1,2}[A-Z][a-z]{1,20})['\u2019](?=\W|$)",
    re.IGNORECASE,
)


def _strip_possessives(text: str) -> str:
    """
    Remove possessive suffixes that immediately follow a title+name combo
    so that 'Mrs. Little's family' and 'Dr. Jones' notes' don't generate
    spurious header hits.

    Uses two sequential capturing-group substitutions instead of a
    variable-width lookbehind, which Python 3.10's `re` module rejects.
    Handles straight ('), curly (\u2019), and bare-apostrophe forms.
    """
    text = _POSSESSIVE_S_RE.sub(r"\1", text)    # "Little's" -> "Little"
    text = _POSSESSIVE_APO_RE.sub(r"\1", text)  # "Jones'"   -> "Jones"
    return text


# ══════════════════════════════════════════════════════════════════════════════
# PATIENT BOUNDARY PATTERNS
#
# Key design constraint for the title+name pattern:
#   "Mrs. Little" at the START of a demographic header line is a boundary.
#   "Mrs. Little has no history..." mid-paragraph is NOT a boundary.
#
# We handle this with two mechanisms:
#   1. The title+name pattern requires the line to END shortly after the name
#      (line-end anchor $) — narrative sentences continue past the name.
#   2. _NARRATIVE_LINE_PATTERNS acts as a secondary filter: any candidate
#      position whose line matches a narrative pattern is suppressed.
# ══════════════════════════════════════════════════════════════════════════════

_PATIENT_START_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE | re.MULTILINE)
    for p in [
        # Explicit "Patient Name:" or "Name:" field — strongest signal.
        r"^\s*patient\s*(?:name)?\s*[:\-]\s*\S",
        r"^\s*name\s*[:\-]\s*[A-Z][a-z]",
        # Title + name where the line ends right after the name.
        # The $ anchor means this won't match "Mrs. Little has no history..."
        # because that line continues past the name.
        r"^\s*(?:mr|mrs|ms|dr)\.?\s+[A-Z][a-zA-Z\-]{1,30}\s*$",
        # Structured demographic fields.
        r"^\s*reg(?:istration)?\s*(?:no|#|id)?\s*[:\-]\s*\w",
        r"^\s*patient\s*id\s*[:\-]\s*\w",
        r"^\s*pid\s*[:\-]\s*\w",
        r"^\s*age\s*[:\-]\s*\d",
        r"^\s*(?:date\s*of\s*birth|dob)\s*[:\-]",
        r"^\s*[sdw]/o\s+\w",
    ]
]

# Secondary suppression filter.
# If a candidate header line matches any of these, it is narrative prose —
# not a patient boundary — and must be discarded even if a start pattern fired.
_NARRATIVE_LINE_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        # Title+name immediately followed by a verb or common connector word.
        r"(?:mr|mrs|ms|dr)\.?\s+[A-Z][a-z]+\s+"
        r"(?:is|are|was|were|has|have|had|does|did|do|"
        r"reports|reported|denies|denied|describes|described|"
        r"presents|presented|received|never|not|also|and|or|the|a)\b",
        # Possessive — belt-and-suspenders on top of _strip_possessives.
        r"(?:mr|mrs|ms|dr)\.?\s+[A-Z][a-z]+['\u2019]s?\b",
    ]
]


def _is_narrative_line(line: str) -> bool:
    """Return True if the line looks like prose rather than a header."""
    return any(pat.search(line) for pat in _NARRATIVE_LINE_PATTERNS)


# ══════════════════════════════════════════════════════════════════════════════
# NAME EXTRACTION & NORMALISATION
#
# Problem: the same patient's name may appear in multiple formats:
#   "Patient Name: Little, Aimee"  -> raw extracted value: "LITTLE, AIMEE"
#   Narrative reference: "Mrs. Little"  -> if somehow extracted: "LITTLE"
#   Another record field: "Name: Aimee Little" -> "AIMEE LITTLE"
#
# We normalise all of these to "FIRSTNAME LASTNAME" (space-separated, upper)
# so that _names_are_different can compare them reliably.
#
# Additionally _names_are_different uses a last-name containment check so
# that "LITTLE" and "AIMEE LITTLE" are recognised as the SAME person rather
# than two different patients.
# ══════════════════════════════════════════════════════════════════════════════

# Patterns that extract the raw name value from a structured field line.
# Tried in order; first match wins.
_NAME_EXTRACT_PATTERNS: list[re.Pattern] = [
    # "Patient Name: Little, Aimee"  or  "Patient Name: JOHN DOE"
    re.compile(
        r"patient\s*(?:name)?\s*[:\-]\s*([A-Za-z][A-Za-z\s\.,\-]{2,40}?)"
        r"(?=\s*(?:age|gender|lab|invoice|reg|dob|s/o|d/o|w/o|\d|\n|$))",
        re.IGNORECASE,
    ),
    # "Name: John Doe"  or  "Name: Doe, John"
    re.compile(
        r"^\s*name\s*[:\-]\s*([A-Za-z][A-Za-z\s\.,\-]{2,40}?)"
        r"(?=\s*(?:age|gender|lab|invoice|reg|dob|\d|\n|$))",
        re.IGNORECASE | re.MULTILINE,
    ),
]

# Detects "Last, First" format (comma present between two name parts).
_LAST_FIRST_RE = re.compile(
    r"^([A-Za-z\-]{2,30}),\s*([A-Za-z\-]{2,30})$"
)


def _normalise_name(raw: str) -> str:
    """
    Normalise a raw extracted name string to "FIRSTNAME LASTNAME" upper-case.

    Handles:
      "Little, Aimee"   -> "AIMEE LITTLE"   (Last, First format)
      "LITTLE, AIMEE"   -> "AIMEE LITTLE"
      "Aimee Little"    -> "AIMEE LITTLE"
      "JOHN DOE"        -> "JOHN DOE"
      "Little"          -> "LITTLE"          (single token — returned as-is)
    """
    raw = re.sub(r"\s+", " ", raw.strip()).upper()
    m = _LAST_FIRST_RE.match(raw)
    if m:
        # Reverse "LAST, FIRST" -> "FIRST LAST"
        return f"{m.group(2).strip()} {m.group(1).strip()}"
    return raw


def _extract_patient_name(text: str) -> str | None:
    """
    Extract and normalise the patient name from a text block.
    Returns None if no structured name field can be found.

    Always returns the name in "FIRSTNAME LASTNAME" order so that names
    extracted from "Last, First" formatted fields compare correctly with
    names extracted from "First Last" formatted fields.
    """
    for pat in _NAME_EXTRACT_PATTERNS:
        m = pat.search(text)
        if m:
            raw  = m.group(1).strip()
            name = _normalise_name(raw)
            # Reject very short or purely numeric matches (false positives)
            if len(name) >= 3 and not name.replace(" ", "").isdigit():
                return name
    return None


def _names_are_different(name_a: str | None, name_b: str | None) -> bool:
    """
    Returns True only when BOTH names are known AND they are clearly different
    people.

    Conservative rules (any of these -> same person, return False):
      - Either name is None.
      - The names are identical.
      - One name is a substring of the other (handles "LITTLE" vs "AIMEE LITTLE"
        where only the last name was extractable from one snippet).
      - The names share a common last-name token (last space-separated word).
      - The edit-distance heuristic says they are close (OCR noise tolerance).
    """
    if not name_a or not name_b:
        return False
    if name_a == name_b:
        return False

    # Substring containment: "LITTLE" in "AIMEE LITTLE" -> same person.
    if name_a in name_b or name_b in name_a:
        return False

    # Shared last-name token: "AIMEE LITTLE" and "LITTLE" share "LITTLE".
    tokens_a = set(name_a.split())
    tokens_b = set(name_b.split())
    if tokens_a & tokens_b:                 # non-empty intersection
        return False

    # Edit-distance / prefix heuristic for OCR noise.
    return _edit_distance_exceeds(name_a, name_b, threshold=4)


def _edit_distance_exceeds(a: str, b: str, threshold: int) -> bool:
    """
    Rough check: if the strings share a very long common prefix the
    difference is likely OCR noise, not a different person.
    """
    if abs(len(a) - len(b)) > threshold:
        return True
    common = 0
    for ca, cb in zip(a, b):
        if ca == cb:
            common += 1
        else:
            break
    similarity = common / max(len(a), len(b), 1)
    return similarity < 0.80


# ══════════════════════════════════════════════════════════════════════════════
# HEADER DETECTION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _page_has_patient_header(page: str) -> bool:
    """True if the page contains at least one genuine patient-header line."""
    page = _strip_possessives(page)
    for pat in _PATIENT_START_PATTERNS:
        for m in pat.finditer(page):
            line_start = page.rfind("\n", 0, m.start()) + 1
            line_end   = page.find("\n", m.end())
            line = page[line_start: line_end if line_end != -1 else len(page)]
            if not _is_narrative_line(line):
                return True
    return False


def _find_header_positions(text: str) -> list[int]:
    """
    Return sorted char positions where a NEW patient header starts.

    Rules (applied in order):
      1. Strip possessives from the text before matching.
      2. Reject any candidate line that looks like narrative prose.
      3. Deduplicate by resolved patient name — same name = same patient,
         skip the position.
      4. If no name can be extracted from a position, SKIP it (unknown name
         means we cannot confirm a new patient — conservative is correct).
         The old proximity-guard fallback is intentionally absent.
    """
    normalized = _strip_possessives(text)

    raw_positions: set[int] = set()
    for pattern in _PATIENT_START_PATTERNS:
        for m in pattern.finditer(normalized):
            line_start = normalized.rfind("\n", 0, m.start()) + 1
            line_end   = normalized.find("\n", m.end())
            line = normalized[line_start: line_end if line_end != -1 else len(normalized)]
            if not _is_narrative_line(line):
                raw_positions.add(line_start)

    sorted_pos = sorted(raw_positions)

    # Deduplicate by resolved name.
    # Unknown name (None) -> skip; we cannot confirm a new patient.
    seen_names: list[str] = []   # list to preserve insertion order for token checks
    deduped: list[int] = []

    for pos in sorted_pos:
        snippet = normalized[pos: pos + 300]
        name = _extract_patient_name(snippet)

        if name:
            # Check against every already-seen name, not just the last one,
            # because a document may have preamble + patient A + patient B.
            if not any(not _names_are_different(name, seen) for seen in seen_names):
                seen_names.append(name)
                deduped.append(pos)
            else:
                logger.debug(
                    "_find_header_positions: skipping pos %d, "
                    "name '%s' matches an already-recorded patient", pos, name,
                )
        else:
            logger.debug(
                "_find_header_positions: skipping pos %d, "
                "no extractable name (narrative reference assumed)", pos,
            )

    return deduped


def _merge_short_chunks(chunks: list[str]) -> list[str]:
    """
    Merge chunks that are too short (cover pages, header-only fragments)
    into the immediately preceding chunk.
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
      1. It contains a genuine patient-header line (not narrative prose).
      2. The patient name found on it DIFFERS from the most recently seen name.
    """
    new_patient_page_indices: list[int] = []
    last_known_name: str | None = None

    for i, page in enumerate(pages):
        if not _page_has_patient_header(page):
            continue

        name = _extract_patient_name(_strip_possessives(page))

        if last_known_name is None:
            new_patient_page_indices.append(i)
            last_known_name = name
        elif _names_are_different(last_known_name, name):
            new_patient_page_indices.append(i)
            last_known_name = name
        else:
            logger.debug(
                "Page %d: same patient ('%s' ~ '%s'), treating as continuation",
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

    positions = _find_header_positions(text)
    if len(positions) >= 2:
        names = set()
        for pos in positions:
            snippet = _strip_possessives(text[pos: pos + 300])
            name = _extract_patient_name(snippet)
            if name:
                names.add(name)
        if len(names) >= 2:
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
                    chunks.append(page.strip())
                else:
                    if chunks:
                        chunks[-1] = chunks[-1] + "\n\n" + page.strip()
                    else:
                        chunks.append(page.strip())

            result = _merge_short_chunks(chunks)
            if len(result) >= 2:
                return result

    # ── Strategy 2: repeated-header split in flat text (distinct names only) ─
    positions = _find_header_positions(text)
    if len(positions) >= 2:
        named_positions: list[tuple[int, str | None]] = []
        for pos in positions:
            snippet = _strip_possessives(text[pos: pos + 300])
            named_positions.append((pos, _extract_patient_name(snippet)))

        boundary_positions: list[int] = []
        last_name: str | None = None
        for pos, name in named_positions:
            if last_name is None:
                boundary_positions.append(pos)
                last_name = name
            elif _names_are_different(last_name, name):
                boundary_positions.append(pos)
                last_name = name

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