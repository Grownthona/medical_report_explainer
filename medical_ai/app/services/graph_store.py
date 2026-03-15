# graph_store.py
from __future__ import annotations
import networkx as nx


class MediBotGraph:
    """
    Universal Graph RAG store for MediBot.

    Handles all 6 report formats:
      1. Single patient  + report{}           (is_multi_patient=false, has "report")
      2. Single patient  + sections{}         (is_multi_patient=false, has "sections")
      3. Single patient  + report{} + XRAY    (AI probability tests, status="High"/"Low")
      4. Multi-patient   + patients[report{}] (each patient has "report")
      5. Multi-patient   + patients[sections{}] (each patient has "sections")
      6. Clinical/OPD    + report, no tests[] (psychiatric, dental — tests_analysis=[])
    """

    def __init__(self) -> None:
        self.G = nx.DiGraph()

    # ══════════════════════════════════════════════════════════════════
    # Public API
    # ══════════════════════════════════════════════════════════════════

    def build_from_report(self, data: dict) -> None:
        self.G.clear()
        for patient in self._normalise(data):
            self._index_patient(patient)

    def retrieve_context(self, query: str) -> str:
        """
        Traverse the graph and return relevant context string.
        Prioritises abnormal/high-risk findings.
        Filters by patient name if one is mentioned in the query.
        """
        query_lower = query.lower()
        mentioned   = self._mentioned_patients(query_lower)
        lines: list[str] = []

        for pid, pdata in self._patients():
            name = (pdata.get("name") or "").strip()

            # Name filter: skip if query names a different patient
            if mentioned and not any(m in name.lower() for m in mentioned):
                continue

            lines.append(
                f"Patient: {name} | "
                f"Age: {pdata.get('age')} | "
                f"Gender: {pdata.get('gender')} | "
                f"Date: {pdata.get('collection_date') or 'N/A'}"
            )

            for rid in self.G.successors(pid):
                rdata = self.G.nodes[rid]
                if rdata.get("type") != "Report":
                    continue
                lines += self._format_report_node(rid, rdata, query_lower)

        return "\n".join(lines) or "No relevant patient data found."

    def get_all_abnormal(self) -> list[dict]:
        """Return every abnormal/high test across all patients."""
        return [
            {"node_id": nid, **d}
            for nid, d in self.G.nodes(data=True)
            if d.get("type") == "Test" and self._is_abnormal(d)
        ]

    # ══════════════════════════════════════════════════════════════════
    # Step 1 — Normalise: every format → list[patient_dict]
    # ══════════════════════════════════════════════════════════════════

    def _normalise(self, data: dict) -> list[dict]:
        """
        Always returns a list of normalised patient dicts:
          {
            "info":     { name, age_years, gender, collection_date, ... },
            "sections": [ { section_title, section_type, risk_level,
                            advice, tests_analysis: [...] }, ... ]
          }
        """
        # ── Multi-patient wrapper ──────────────────────────────────────
        if data.get("is_multi_patient") and "patients" in data:
            return [self._normalise_one(p) for p in data["patients"]]

        # ── Single patient ─────────────────────────────────────────────
        return [self._normalise_one(data)]

    def _normalise_one(self, p: dict) -> dict:
        info = p.get("patient", {})

        sections: list[dict] = []

        # Format A: flat "report" key  (single-section)
        if "report" in p and p["report"]:
            raw = p["report"]
            section_type = self._infer_section_type(p, raw)
            sections.append({
                "section_title": raw.get("section_title", "Report"),
                "section_type":  section_type,
                "risk_level":    raw.get("risk_level"),
                "advice":        raw.get("advice"),
                "summary":       raw.get("summary"),
                "tests_analysis": raw.get("tests_analysis") or [],
            })

        # Format B: "sections" dict  { "LAB": [...], "IMAGING": [...], "XRAY": [...], ... }
        if "sections" in p and p["sections"]:
            for stype, section_list in p["sections"].items():
                if not isinstance(section_list, list):
                    continue
                for sec in section_list:
                    sections.append({
                        "section_title": sec.get("section_title", stype),
                        "section_type":  stype,
                        "risk_level":    sec.get("risk_level"),
                        "advice":        sec.get("advice"),
                        "summary":       sec.get("summary"),
                        "tests_analysis": sec.get("tests_analysis") or [],
                    })

        return {"info": info, "sections": sections}

    def _infer_section_type(self, p: dict, report: dict) -> str:
        """Best-guess section type when using flat 'report' format."""
        cat = (
            p.get("document_type", {}).get("category") or
            p.get("document_type", {}).get("sub_type") or
            report.get("section_title") or
            "UNKNOWN"
        ).upper()
        if "LAB" in cat or "CBC" in cat or "HAEM" in cat or "BIO" in cat:
            return "LAB"
        if "IMAG" in cat or "XRAY" in cat or "X-RAY" in cat or "MRI" in cat:
            return "IMAGING"
        if "CLIN" in cat or "OPD" in cat or "PSYCH" in cat or "SPEC" in cat:
            return "CLINICAL"
        return cat

    # ══════════════════════════════════════════════════════════════════
    # Step 2 — Index: normalised patient → graph nodes
    # ══════════════════════════════════════════════════════════════════

    def _index_patient(self, patient: dict) -> None:
        info = patient["info"]
        name = (info.get("name") or "unknown").strip()
        pid  = f"patient::{name}::{info.get('collection_date','')}"

        self.G.add_node(pid,
            type            = "Patient",
            name            = name,
            age             = info.get("age_years"),
            gender          = info.get("gender"),
            collection_date = info.get("collection_date"),
            referred_by     = info.get("referred_by"),
        )

        for section in patient["sections"]:
            self._index_section(pid, section)

    def _index_section(self, pid: str, section: dict) -> None:
        title   = section["section_title"]
        stype   = section["section_type"]
        rid     = f"report::{pid}::{title}"

        self.G.add_node(rid,
            type         = "Report",
            title        = title,
            section_type = stype,
            risk_level   = section.get("risk_level"),
            advice       = section.get("advice"),
            summary      = section.get("summary"),
        )
        self.G.add_edge(pid, rid, rel="HAS_REPORT")

        tests = section.get("tests_analysis") or []
        for test in tests:
            self._index_test(pid, rid, test)

        # Clinical/OPD sections often have no tests — still indexed via the
        # Report node so advice + summary are retrievable
        if not tests and section.get("summary"):
            # Store summary as a pseudo-test so it surfaces in retrieval
            self._index_pseudo_test(rid, section)

    def _index_test(self, pid: str, rid: str, test: dict) -> None:
        name   = test.get("test_name", "unknown")
        tid    = f"test::{rid}::{name}"
        status = (test.get("status") or "Unknown").strip()

        self.G.add_node(tid,
            type            = "Test",
            name            = name,
            value           = test.get("value"),
            unit            = test.get("unit"),
            reference_range = test.get("reference_range"),
            status          = status,
            explanation     = test.get("result_explanation"),
        )
        self.G.add_edge(rid, tid, rel="HAS_TEST")

        # Shortcut edge for fast abnormal lookup
        if self._is_abnormal(self.G.nodes[tid]):
            self.G.add_edge(pid, tid, rel="ABNORMAL_IN")

    def _index_pseudo_test(self, rid: str, section: dict) -> None:
        """For clinical notes with no tests_analysis, store the summary as a node."""
        tid = f"test::{rid}::clinical_summary"
        self.G.add_node(tid,
            type        = "Test",
            name        = "Clinical summary",
            value       = section.get("summary", ""),
            unit        = "",
            status      = "Info",
            explanation = section.get("advice", ""),
        )
        self.G.add_edge(rid, tid, rel="HAS_TEST")

    # ══════════════════════════════════════════════════════════════════
    # Step 3 — Retrieval helpers
    # ══════════════════════════════════════════════════════════════════

    def _format_report_node(
        self, rid: str, rdata: dict, query_lower: str
    ) -> list[str]:
        lines = [
            f"  [{rdata.get('section_type','?')}] "
            f"{rdata.get('title','Report')} — "
            f"risk: {rdata.get('risk_level','?')}"
        ]

        all_tests  = list(self.G.successors(rid))
        abnormal   = [t for t in all_tests if self._is_abnormal(self.G.nodes[t])]
        normal     = [t for t in all_tests if not self._is_abnormal(self.G.nodes[t])]
        want_all   = self._wants_all_tests(query_lower)

        for tid in abnormal + (normal if want_all else []):
            t    = self.G.nodes[tid]
            flag = "⚠️ " if self._is_abnormal(t) else ""
            val  = t.get("value", "")
            unit = t.get("unit", "")
            ref  = t.get("reference_range", "")
            lines.append(
                f"    {flag}{t['name']}: {val} {unit}"
                + (f" (ref: {ref})" if ref and ref != "N/A" else "")
                + f" → {t.get('status','?')}"
            )
            # Always show explanation for abnormal tests
            if flag and t.get("explanation"):
                lines.append(f"      ↳ {t['explanation']}")

        if rdata.get("advice"):
            lines.append(f"  Advice: {rdata['advice']}")

        return lines

    def _patients(self):
        return [
            (nid, d)
            for nid, d in self.G.nodes(data=True)
            if d.get("type") == "Patient"
        ]

    def _mentioned_patients(self, query: str) -> list[str]:
        """Return lowercase name fragments found in the query."""
        all_names = [
            d["name"].lower()
            for _, d in self._patients()
            if d.get("name")
        ]
        # Also try first names only
        fragments = set()
        for full in all_names:
            parts = full.split()
            fragments.add(full)
            if parts:
                fragments.add(parts[0])   # first name
                fragments.add(parts[-1])  # last name

        return [f for f in fragments if f in query]

    @staticmethod
    def _is_abnormal(node: dict) -> bool:
        status = (node.get("status") or "").lower()
        return status in ("high", "low", "abnormal", "critical", "unknown")
        # Note: "Unknown" is included — imaging AI findings & ungraded results
        # should surface so the LLM can flag them rather than silently ignore

    @staticmethod
    def _wants_all_tests(query: str) -> bool:
        keywords = [
            "all", "every", "full", "complete", "list",
            "সব", "সকল", "পুরো", "সম্পূর্ণ",         # Bengali
            "كل", "جميع",                              # Arabic
            "सभी", "पूरा",                             # Hindi
        ]
        return any(k in query for k in keywords)