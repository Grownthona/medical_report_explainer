from __future__ import annotations

import logging
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from services.ocr_service      import OCRService
from services.assembler        import assemble_report
from services.xray_report      import XRayService
from services.xray_narrator    import narrate_xray

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "Medical Report Processor",
    description = "OCR → NER → LLM pipeline for Bangladeshi medical reports",
    version     = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:5173"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

ocr_service  = OCRService()
xray_service = XRayService()

SupportedLanguage = Literal["en", "bn", "ar", "hi", "ur"]


def _is_empty(text: str | None) -> bool:
    if not text:
        return True
    import re
    cleaned = re.sub(r'[\s\W_]+', '', text)
    return len(cleaned) < 20


async def _handle_xray(file_bytes: bytes, language: str) -> dict:
    predictions: list[dict] = xray_service.analyze(file_bytes)
    narration: dict = narrate_xray(predictions, language=language)
    return {
        "source":           "xray",
        "is_multi_patient": False,
        "language":         language,
        "xray": {
            "findings":          narration.get("findings",          ""),
            "predictions":       predictions,
            "voice_explanation": narration.get("voice_explanation", ""),
            "advice":            narration.get("advice",            ""),
        },
    }


def _handle_report(text: str, source: str, language: str) -> dict:
    return assemble_report(text, language=language)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTE 1 — FILE UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/extract/file", summary="Upload a PDF or image for processing")
async def extract_from_file(
    file:     UploadFile = File(...),
    language: SupportedLanguage = Form(default="en"),
):
    """
    Upload a medical report file (PDF, JPG, PNG, TIFF).

    Handles single-patient, multi-patient, and X-ray files.

    Response shape — single patient:
        { is_multi_patient: false, patient: {...}, report: {...}, ... }

    Response shape — multi-patient:
        { is_multi_patient: true, total_patients: N, patients: [ {...}, ... ] }

    Response shape — X-ray:
        { source: "xray", is_multi_patient: false, xray: {...} }
    """
    file_bytes = await file.read()

    try:
        text = await ocr_service.extract_text(file, file_bytes)
    except Exception as e:
        logger.error("OCR failed for %s: %s", file.filename, e)
        raise HTTPException(status_code=422, detail=f"OCR failed: {e}")

    if _is_empty(text):
        logger.info("No text in %s — routing to X-ray", file.filename)
        try:
            return await _handle_xray(file_bytes, language=language)
        except Exception as e:
            logger.error("X-ray analysis failed: %s", e)
            raise HTTPException(status_code=500, detail=f"X-ray analysis failed: {e}")

    logger.info(
        "Text extracted from %s (%d chars) — assembling report",
        file.filename, len(text),
    )
    try:
        return _handle_report(text, source="file", language=language)
    except Exception as e:
        logger.error("Report assembly failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Report assembly failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# ROUTE 2 — RAW TEXT
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/extract/text", summary="Submit raw report text for processing")
async def extract_from_text(
    text:     str = Form(...),
    language: SupportedLanguage = Form(default="en"),
):
    """
    Submit raw OCR text directly.

    Supports single-patient and multi-patient text input.
    The response shape is identical to /extract/file.
    """
    if _is_empty(text):
        raise HTTPException(
            status_code=422,
            detail="Text is empty or too short. Please provide at least 20 characters.",
        )

    logger.info("Processing raw text (%d chars, lang=%s)", len(text), language)
    try:
        return _handle_report(text, source="text", language=language)
    except Exception as e:
        logger.error("Report assembly failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Report assembly failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", summary="Health check")
async def root():
    return {
        "status":   "ok",
        "service":  "Medical Report Processor",
        "routes":   ["/extract/file", "/extract/text"],
        "languages": ["en", "bn", "ar", "hi", "ur"],
    }