# graph_store.py
from __future__ import annotations
import asyncio
import logging
import networkx as nx
from services.web_enricher import fetch_test_knowledge, needs_enrichment

logger = logging.getLogger(__name__)


class MediBotGraph:
    """
    Universal Graph RAG store for MediBot.

    Handles all report formats:
      1. Single patient  + report{}
      2. Single patient  + sections{}
      3. Single patient  + XRAY AI probability findings
      4. Multi-patient   + patients[report{}]
      5. Multi-patient   + patients[sections{}]
      6. Clinical/OPD    + report with no tests_analysis (psychiatric, dental)
    """

    def __init__(self) -> None:
        self.G = nx.DiGraph()

    # ══════════════════════════════════════════════════════════════════
    # Public API
    # ══════════════════════════════════════════════════════════════════

    def build_from_report(self, data: dict) -> None:
        """Clear graph and rebuild from fresh report JSON."""
        self.G.clear()
        for patient in self._normalise(data):
            self._index_patient(patient)

    async def retrieve_context(self, query: str) -> str:
        """
        Traverse the graph and return a context string for the LLM.
        - Enriches abnormal tests with MedlinePlus knowledge when query
          asks for explanation (lazy, cached per test slug).
        - Filters to the named patient if one is mentioned in the query.
        - Always surfaces abnormal tests; shows normal tests only when
          the query explicitly asks for all results.
        """
        query_lower = query.lower()

        # Web enrichment — only when query needs explanation
        await self._enrich_abnormal_tests(query_lower)

        mentioned = self._mentioned_patients(query_lower)
        lines: list[str] = []

        for pid, pdata in self._patients():
            name = (pdata.get("name") or "").strip()

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
        """Return every abnormal test node across all patients."""
        return [
            {"node_id": nid, **d}
            for nid, d in self.G.nodes(data=True)
            if d.get("type") == "Test" and self._is_abnormal(d)
        ]

    # ══════════════════════════════════════════════════════════════════
    # Step 1 — Normalise: every format → list[patient_dict]
    # ══════════════════════════════════════════════════════════════════

    def _normalise(self, data: dict) -> list[dict]:
        if data.get("is_multi_patient") and "patients" in data:
            return [self._normalise_one(p) for p in data["patients"]]
        return [self._normalise_one(data)]

    def _normalise_one(self, p: dict) -> dict:
        info = p.get("patient", {})
        sections: list[dict] = []

        # Format A: flat "report" key
        if "report" in p and p["report"]:
            raw = p["report"]
            sections.append({
                "section_title":  raw.get("section_title", "Report"),
                "section_type":   self._infer_section_type(p, raw),
                "risk_level":     raw.get("risk_level"),
                "advice":         raw.get("advice"),
                "summary":        raw.get("summary"),
                "tests_analysis": raw.get("tests_analysis") or [],
            })

        # Format B: "sections" dict { "LAB": [...], "IMAGING": [...], ... }
        if "sections" in p and p["sections"]:
            for stype, section_list in p["sections"].items():
                if not isinstance(section_list, list):
                    continue
                for sec in section_list:
                    sections.append({
                        "section_title":  sec.get("section_title", stype),
                        "section_type":   stype,
                        "risk_level":     sec.get("risk_level"),
                        "advice":         sec.get("advice"),
                        "summary":        sec.get("summary"),
                        "tests_analysis": sec.get("tests_analysis") or [],
                    })

        return {"info": info, "sections": sections}

    def _infer_section_type(self, p: dict, report: dict) -> str:
        cat = (
            p.get("document_type", {}).get("category") or
            p.get("document_type", {}).get("sub_type") or
            report.get("section_title") or
            "UNKNOWN"
        ).upper()
        if any(k in cat for k in ("LAB", "CBC", "HAEM", "BIO", "BIOCHEM")):
            return "LAB"
        if any(k in cat for k in ("IMAG", "XRAY", "X-RAY", "MRI", "CT", "SCAN")):
            return "IMAGING"
        if any(k in cat for k in ("CLIN", "OPD", "PSYCH", "SPEC", "DENTAL")):
            return "CLINICAL"
        return cat

    # ══════════════════════════════════════════════════════════════════
    # Step 2 — Index: normalised patient → graph nodes
    # ══════════════════════════════════════════════════════════════════

    def _index_patient(self, patient: dict) -> None:
        info = patient["info"]
        name = (info.get("name") or "unknown").strip()
        pid  = f"patient::{name}::{info.get('collection_date', '')}"

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
        title = section["section_title"]
        stype = section["section_type"]
        rid   = f"report::{pid}::{title}"

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

        # Clinical sections with no tests — store summary as pseudo-test
        if not tests and section.get("summary"):
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
    # Step 3 — Web enrichment (async, lazy, cached)
    # ══════════════════════════════════════════════════════════════════

    async def _enrich_abnormal_tests(self, query_lower: str) -> None:
        """
        Fetch MedlinePlus knowledge for abnormal tests and attach as
        KnowledgeBase nodes. Skips tests already enriched. Only runs
        when the query is explanation-type.
        """
        if not needs_enrichment(query_lower):
            return

        # Collect abnormal test nodes that don't yet have a KB child
        to_enrich = [
            (nid, d)
            for nid, d in self.G.nodes(data=True)
            if d.get("type") == "Test"
            and self._is_abnormal(d)
            and not any(
                self.G.nodes[s].get("type") == "KnowledgeBase"
                for s in self.G.successors(nid)
            )
        ]

        if not to_enrich:
            return

        # Fetch all in parallel
        results = await asyncio.gather(
            *[fetch_test_knowledge(d.get("name", "")) for _, d in to_enrich],
            return_exceptions=True,
        )

        for (tid, _), knowledge in zip(to_enrich, results):
            if not knowledge or isinstance(knowledge, Exception):
                continue
            test_name = self.G.nodes[tid].get("name", "unknown")
            kid = f"kb::{test_name}"
            # Add KB node (or update if already exists from a previous slug match)
            self.G.add_node(kid, type="KnowledgeBase", **knowledge)
            self.G.add_edge(tid, kid, rel="HAS_DEFINITION")
            logger.debug("KB node attached: %s → %s", test_name, knowledge.get("url"))

    # ══════════════════════════════════════════════════════════════════
    # Step 4 — Retrieval formatting
    # ══════════════════════════════════════════════════════════════════

    def _format_report_node(
        self, rid: str, rdata: dict, query_lower: str
    ) -> list[str]:
        lines = [
            f"  [{rdata.get('section_type', '?')}] "
            f"{rdata.get('title', 'Report')} — "
            f"risk: {rdata.get('risk_level', '?')}"
        ]

        all_tests = list(self.G.successors(rid))
        abnormal  = [t for t in all_tests if self._is_abnormal(self.G.nodes[t])]
        normal    = [t for t in all_tests if not self._is_abnormal(self.G.nodes[t])]
        want_all  = self._wants_all_tests(query_lower)

        for tid in abnormal + (normal if want_all else []):
            t    = self.G.nodes[tid]
            flag = "⚠️ " if self._is_abnormal(t) else ""
            val  = t.get("value", "")
            unit = t.get("unit", "")
            ref  = t.get("reference_range", "")

            lines.append(
                f"    {flag}{t['name']}: {val} {unit}"
                + (f" (ref: {ref})" if ref and ref not in ("N/A", "") else "")
                + f" → {t.get('status', '?')}"
            )

            # Show report explanation for abnormal tests
            if flag and t.get("explanation"):
                lines.append(f"      ↳ {t['explanation']}")

            # Attach MedlinePlus KB knowledge if available
            for kid in self.G.successors(tid):
                kb = self.G.nodes[kid]
                if kb.get("type") != "KnowledgeBase":
                    continue
                if kb.get("full_name"):
                    lines.append(f"      📚 {kb['full_name']}")
                if kb.get("what_it_measures"):
                    lines.append(f"         Measures: {kb['what_it_measures'][:200]}")
                if kb.get("abnormal_means"):
                    lines.append(f"         Abnormal means: {kb['abnormal_means'][:200]}")
                if kb.get("common_causes"):
                    lines.append(f"         Common causes: {kb['common_causes'][:200]}")
                if kb.get("patient_advice"):
                    lines.append(f"         Note: {kb['patient_advice'][:150]}")
                lines.append(f"         (Source: {kb.get('source', 'MedlinePlus')})")

        if rdata.get("advice"):
            lines.append(f"  Advice: {rdata['advice']}")

        return lines

    # ══════════════════════════════════════════════════════════════════
    # Helpers
    # ══════════════════════════════════════════════════════════════════

    def _patients(self):
        return [
            (nid, d)
            for nid, d in self.G.nodes(data=True)
            if d.get("type") == "Patient"
        ]

    def _mentioned_patients(self, query: str) -> list[str]:
        fragments: set[str] = set()
        for _, d in self._patients():
            full = (d.get("name") or "").lower()
            parts = full.split()
            fragments.add(full)
            if parts:
                fragments.add(parts[0])
                fragments.add(parts[-1])
        return [f for f in fragments if f and f in query]

    @staticmethod
    def _is_abnormal(node: dict) -> bool:
        status = (node.get("status") or "").lower()
        return status in ("high", "low", "abnormal", "critical", "unknown")

    @staticmethod
    def _wants_all_tests(query: str) -> bool:
        keywords = [
            "all", "every", "full", "complete", "list",
            "সব", "সকল", "পুরো", "সম্পূর্ণ",
            "كل", "جميع",
            "सभी", "पूरा",
        ]
        return any(k in query for k in keywords)