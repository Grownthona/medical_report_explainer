"""
multi_file_processor.py
─────────────────────────────────────────────────────────────────────────────
Handles multi-file uploads where the batch may contain a mix of:
  • Text-bearing files  (PDFs, scanned lab reports, prescriptions)
  • X-ray images        (no extractable text → routed to XRayService)

KEY DESIGN: one file = one patient.
  Each file is assembled independently via assemble_report() and returned
  in a "patients" array — consistent with the multi-patient response shape
  produced by assembler.py's _run_text_pipeline().

  Exception: if there is exactly ONE text file AND exactly ONE x-ray file
  they are merged into a single mixed report
  (sections: { "LAB": [...], "XRAY": [...] }) because they most likely
  belong to the same patient.

Response shapes:

  1 text file, 0 x-ray files
      → standard single-patient assemble_report() response (unchanged shape)

  0 text files, 1 x-ray file
      → assemble_report(xray_result=r, language)
      → { ..., sections: { "XRAY": [...] } }

  1 text file, 1 x-ray file   ← "same patient" heuristic
      → assemble_report(raw, language, xray_result=r)
      → { ..., is_mixed: True, sections: { "LAB": [...], "XRAY": [...] } }

  N files where N > 1 and not the 1+1 case above
      → each file assembled independently
      → {
            is_multi_patient: True,
            total_patients:   N,
            patients: [
                { patient_index: 0, source_file: "a.pdf", ...report... },
                { patient_index: 1, source_file: "b.pdf", ...report... },
                ...
            ]
         }
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

        # ── Read + validate all files ─────────────────────────────────────────
        all_bytes: list[bytes] = []
        for f in files:
            all_bytes.append(await f.read())

        for f in files:
            self._ocr.validate_file_type(f.content_type)

        # ── OCR each file, bucket into text vs x-ray ──────────────────────────
        # text_files : list of (filename, ocr_text)
        # xray_files : list of (filename, raw_bytes)
        text_files: list[tuple[str, str]]   = []
        xray_files: list[tuple[str, bytes]] = []

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

        total_files = len(text_files) + len(xray_files)

        # ── Special case: 1 text + 1 x-ray → single mixed report ─────────────
        # These almost certainly belong to the same patient.
        if len(text_files) == 1 and len(xray_files) == 1:
            fname_text, text      = text_files[0]
            fname_xray, xray_raw  = xray_files[0]

            validation = self._validator.validate(text)
            if not validation.is_medical:
                raise HTTPException(status_code=422, detail=validation.reason)

            try:
                xray_result = self._xray.analyze(xray_raw)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"X-ray analysis failed: {e}")

            logger.info("1 text + 1 x-ray → single mixed report")
            return assemble_report(text, language=language, xray_result=xray_result)

        # ── General case: each file is a separate patient ─────────────────────
        # Build a flat ordered list: text files first (preserving upload order),
        # then x-ray files. Re-sort by original upload index so the patient_index
        # matches the order the user uploaded the files.
        #
        # We rebuild an ordered list of (filename, kind, payload) from the
        # original zip so upload order is honoured.
        ordered: list[tuple[str, str, str | bytes]] = []
        text_iter = iter(text_files)
        xray_iter = iter(xray_files)

        for idx, (f, raw) in enumerate(zip(files, all_bytes)):
            filename = f.filename or f"file_{idx}"
            # Decide which bucket this filename belongs to
            # (text_files / xray_files were built in the same loop order)
            if any(fn == filename for fn, _ in text_files):
                fn, t = next(
                    ((fn, t) for fn, t in text_files if fn == filename),
                    (filename, ""),
                )
                ordered.append((filename, "text", t))
            else:
                fn, rb = next(
                    ((fn, rb) for fn, rb in xray_files if fn == filename),
                    (filename, raw),
                )
                ordered.append((filename, "xray", rb))

        # ── Single file fast-path (shouldn't normally reach here, but safety) ─
        if total_files == 1:
            filename, kind, payload = ordered[0]
            if kind == "text":
                validation = self._validator.validate(payload)          # type: ignore[arg-type]
                if not validation.is_medical:
                    raise HTTPException(status_code=422, detail=validation.reason)
                return assemble_report(payload, language=language)      # type: ignore[arg-type]
            else:
                try:
                    xray_result = self._xray.analyze(payload)           # type: ignore[arg-type]
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"X-ray analysis failed: {e}")
                return assemble_report(xray_result=xray_result, language=language)

        # ── Multi-patient: assemble each file independently ───────────────────
        patients: list[dict] = []

        for patient_index, (filename, kind, payload) in enumerate(ordered):
            try:
                if kind == "text":
                    text = payload  # type: ignore[assignment]
                    validation = self._validator.validate(text)
                    if not validation.is_medical:
                        logger.warning(
                            "File %s rejected as non-medical (score=%d) — skipping",
                            filename, validation.score,
                        )
                        patients.append({
                            "patient_index": patient_index,
                            "source_file":   filename,
                            "error":         validation.reason,
                        })
                        continue

                    report = assemble_report(text, language=language)

                else:  # kind == "xray"
                    xray_raw = payload  # type: ignore[assignment]
                    xray_result = self._xray.analyze(xray_raw)
                    report = assemble_report(xray_result=xray_result, language=language)

                report["patient_index"] = patient_index
                report["source_file"]   = filename
                patients.append(report)
                logger.info(
                    "Patient %d assembled: %s (%s)",
                    patient_index, filename, kind,
                )

            except HTTPException:
                raise
            except Exception as e:
                logger.error("Failed to assemble patient %d (%s): %s", patient_index, filename, e)
                patients.append({
                    "patient_index": patient_index,
                    "source_file":   filename,
                    "error":         str(e),
                })

        if not patients:
            raise HTTPException(
                status_code=422,
                detail="None of the uploaded files could be processed as medical reports.",
            )

        # If every file failed validation / errored, surface a clear error
        successful = [p for p in patients if "error" not in p]
        if not successful:
            reasons = "; ".join(p.get("error", "unknown error") for p in patients)
            raise HTTPException(status_code=422, detail=f"All files rejected: {reasons}")

        return {
            "is_multi_patient": True,
            "total_patients":   len(patients),
            "patients":         patients,
        }