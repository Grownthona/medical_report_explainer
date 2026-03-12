from __future__ import annotations

import logging
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.ocr_service      import OCRService
from services.assembler        import assemble_report
from services.xray_report      import XRayService
from services.xray_narrator    import narrate_xray   # LLM turns probabilities → text

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
    allow_origins     = ["http://localhost:5173"],   # Vite dev server
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Singletons (initialised once at startup) ──────────────────────────────────

ocr_service  = OCRService()
xray_service = XRayService()


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

SupportedLanguage = Literal["en", "bn", "ar", "hi", "ur"]

def _is_empty(text: str | None) -> bool:
    """True if OCR returned nothing useful (blank / whitespace / noise only)."""
    if not text:
        return True
    # Strip common OCR noise — if fewer than 20 real chars remain, treat as empty
    import re
    cleaned = re.sub(r'[\s\W_]+', '', text)
    return len(cleaned) < 20


async def _handle_xray(file_bytes: bytes, language: str) -> dict:
    """
    Run the X-ray classification model, then ask the LLM to narrate the
    probability predictions into patient-friendly language.
    """
    # Step 1 — image classification model (e.g. CheXNet / custom CNN)
    predictions: list[dict] = xray_service.analyze(file_bytes)
    # predictions shape: [{ "label": "Cardiomegaly", "probability": 0.87 }, ...]

    # Step 2 — LLM narration of the raw probabilities
    narration: dict = narrate_xray(predictions, language=language)
    # narration shape: { findings, voice_explanation, advice }

    return {
        "source":   "xray",
        "language": language,
        "xray": {
            "findings":         narration.get("findings",         ""),
            "predictions":      predictions,
            "voice_explanation":narration.get("voice_explanation",""),
            "advice":           narration.get("advice",           ""),
        },
    }


def _handle_report(text: str, source: str, language: str) -> dict:
    """
    Run the full report assembly pipeline on extracted text.
    Injects language into the result for the frontend.
    """
    # result = assemble_report(text, language=language)
    # return {"source": source, "language": language, **result}

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

    Flow:
      1. OCR  → extract text from the file
      2a. Text found  → assemble_report() → full structured response
      2b. No text     → assumed X-ray image → XRayService + LLM narration
    """
    file_bytes = await file.read()

    # ── Step 1: OCR ───────────────────────────────────────────────────────────
    try:
        text = await ocr_service.extract_text(file, file_bytes)
    except Exception as e:
        logger.error("OCR failed for file %s: %s", file.filename, e)
        raise HTTPException(status_code=422, detail=f"OCR failed: {e}")

    # ── Step 2a: no text → X-ray path ─────────────────────────────────────────
    if _is_empty(text):
        logger.info("No text found in %s — routing to X-ray analysis", file.filename)
        try:
            return await _handle_xray(file_bytes, language=language)
        except Exception as e:
            logger.error("X-ray analysis failed: %s", e)
            raise HTTPException(status_code=500, detail=f"X-ray analysis failed: {e}")

    # ── Step 2b: text found → report pipeline ─────────────────────────────────
    logger.info("Text extracted from %s (%d chars) — assembling report", file.filename, len(text))
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
    Submit raw OCR text directly (no file upload, no OCR step).

    Useful for:
      • Mobile apps that do on-device OCR before sending
      • Copy-pasted report text
      • Re-processing previously extracted text

    Flow:
      text → assemble_report() → full structured response
    """
    if _is_empty(text):
        raise HTTPException(
            status_code=422,
            detail="Text is empty or too short to process. "
                   "Please provide at least 20 characters of report content.",
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
        "languages":["en", "bn", "ar", "hi", "ur"],
    }
