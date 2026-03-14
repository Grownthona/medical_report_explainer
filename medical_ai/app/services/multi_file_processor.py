"""
multi_file_processor.py
─────────────────────────────────────────────────────────────────────────────
Handles multi-file uploads where the batch may contain a mix of:
  • Text-bearing files  (PDFs, scanned lab reports, prescriptions)
  • X-ray images        (no extractable text → routed to XRayService)

All assembly is delegated to assemble_report() which now handles all cases:
  A) Text only    → assemble_report(raw, language)
  B) X-ray only   → assemble_report(xray_result=result, language)
                    sections: { "XRAY": [...] }
  C) Text + xray  → assemble_report(raw, language, xray_result=result)
                    sections: { "LAB": [...], "XRAY": [...] }

Multiple X-ray files: each is returned as a separate top-level entry under
"xray_reports" since assemble_report() handles one xray_result at a time.
"""

from __future__ import annotations

import logging
from fastapi import HTTPException, UploadFile

from services.ocr_service      import OCRService
from services.xray_report      import XRayService
from services.assembler        import assemble_report
from services.report_validator import ReportValidator

logger = logging.getLogger(__name__)


def _is_empty(text: str | None) -> bool:
    if not text:
        return True
    import re
    return len(re.sub(r'[\s\W_]+', '', text)) < 20


class MultiFileProcessor:

    def __init__(
        self,
        ocr_service:      OCRService,
        xray_service:     XRayService,
        report_validator: ReportValidator,
    ):
        self._ocr       = ocr_service
        self._xray      = xray_service
        self._validator = report_validator

    async def process(self, files: list[UploadFile], language: str) -> dict:
        """
        Route a multi-file batch through assemble_report().

        Response shapes (all from assemble_report — consistent with single-file):
          A) All text files
             → standard assemble_report() response (unchanged shape)

          B) Single X-ray file
             → assemble_report(xray_result=r, language)
             → { ..., sections: { "XRAY": [...] } }

          C) Text + single X-ray
             → assemble_report(raw, language, xray_result=r)
             → { ..., is_mixed: True, sections: { "LAB": [...], "XRAY": [...] } }

          D) Multiple X-ray files (with or without text)
             → first xray paired with text (if any), rest xray-only
             → { is_multi_xray: True, total: N, reports: [...] }
        """
        # ── Read + validate all files ─────────────────────────────────────────
        all_bytes: list[bytes] = []
        for f in files:
            all_bytes.append(await f.read())

        for f in files:
            self._ocr.validate_file_type(f.content_type)

        # ── OCR each file, bucket into text vs xray ───────────────────────────
        text_files: list[tuple[str, str]]   = []  # (filename, ocr_text)
        xray_files: list[tuple[str, bytes]] = []  # (filename, raw_bytes)

        for idx, (f, raw) in enumerate(zip(files, all_bytes)):
            filename = f.filename or f"file_{idx}"
            try:
                text = await self._ocr.extract_text(f, raw)
            except Exception as e:
                logger.error("OCR failed for %s: %s", filename, e)
                text = ""

            if _is_empty(text):
                logger.info("%s → no text, routing to X-ray", filename)
                xray_files.append((filename, raw))
            else:
                logger.info("%s → text (%d chars)", filename, len(text))
                text_files.append((filename, text))

        # ── Validate + merge text ─────────────────────────────────────────────
        combined_text = ""

        if text_files:
            merged     = "\n\n--- PAGE BREAK ---\n\n".join(t for _, t in text_files)
            validation = self._validator.validate(merged)
            if not validation.is_medical:
                logger.warning("Text files rejected (score=%d)", validation.score)
                if not xray_files:
                    # Nothing left to process — hard reject
                    raise HTTPException(status_code=422, detail=validation.reason)
                # X-ray files still present — proceed without text
                logger.info("Continuing with X-ray files only (text rejected)")
            else:
                combined_text = merged
                logger.info("Text accepted: %d chars, score=%d", len(combined_text), validation.score)

        # ── Case A: text only, no X-ray files ────────────────────────────────
        if combined_text and not xray_files:
            return assemble_report(combined_text, language=language)

        # ── Process X-ray files ───────────────────────────────────────────────
        # First X-ray is paired with combined_text (may be "") so assemble_report
        # can merge them into sections: { "LAB": [...], "XRAY": [...] }.
        # Subsequent X-ray files are always xray-only.
        reports: list[dict] = []
        text_consumed = False

        for filename, raw in xray_files:
            try:
                xray_result = self._xray.analyze(raw)
                raw_text    = combined_text if not text_consumed else ""
                response    = assemble_report(
                    raw         = raw_text,
                    language    = language,
                    xray_result = xray_result,
                )
                response["source_file"] = filename
                reports.append(response)
                text_consumed = True
                logger.info("X-ray processed: %s", filename)
            except Exception as e:
                logger.error("X-ray failed for %s: %s", filename, e)
                reports.append({
                    "source_file": filename,
                    "error":       f"X-ray analysis failed: {e}",
                })

        # ── Case B/C: single report (text+xray or xray-only) ─────────────────
        if len(reports) == 1:
            return reports[0]

        # ── Case D: multiple X-ray files ──────────────────────────────────────
        return {
            "is_multi_xray": True,
            "total":         len(reports),
            "reports":       reports,
        }