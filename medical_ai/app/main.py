from __future__ import annotations

import logging
from typing import Literal, List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


from services.ocr_service      import OCRService
from services.assembler        import assemble_report
from services.xray_report      import XRayService
from services.xray_narrator    import narrate_xray
from services.tts_service      import TTSService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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
tts_service  = TTSService()

SupportedLanguage = Literal["en", "bn", "ar", "hi", "ur"]
_MAX_FILES        = 20


def _is_empty(text: str | None) -> bool:
    if not text:
        return True
    import re
    return len(re.sub(r'[\s\W_]+', '', text)) < 20


async def _handle_xray(file_bytes: bytes, language: str) -> dict:
    predictions: list[dict] = xray_service.analyze(file_bytes)
    narration:   dict       = narrate_xray(predictions, language=language)
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


# ══════════════════════════════════════════════════════════════════════════════
# ROUTE 1 — FILE(S) UPLOAD
# Accepts one or more files. Single file retains the X-ray fallback path.
# Multiple files are OCR'd in parallel then merged before assembly.
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/extract/file", summary="Upload one or more PDFs/images for processing")
async def extract_from_file(
    files:    List[UploadFile] = File(...),
    language: SupportedLanguage = Form(default="en"),
):
    """
    Upload one **or more** medical report files (PDF, JPG, PNG).

    Single file flow:
      1. OCR the file.
      2a. No text found → X-ray analysis path.
      2b. Text found    → assemble_report().

    Multi-file flow:
      1. All files OCR'd in parallel.
      2. Texts joined with PAGE BREAK markers → one combined string.
      3. assemble_report() runs once on the combined text.
         patient_splitter handles per-patient splitting automatically.

    Limits: up to 20 files per request.

    Response shape — single patient:
        { is_multi_patient: false, patient, report, summary, ... }
    Response shape — multiple patients:
        { is_multi_patient: true, total_patients: N, patients: [...] }
    Response shape — X-ray (single file only):
        { source: "xray", xray: {...} }
    """
    if not files:
        raise HTTPException(status_code=422, detail="No files provided.")

    if len(files) > _MAX_FILES:
        raise HTTPException(
            status_code=422,
            detail=f"Too many files — maximum is {_MAX_FILES} per request.",
        )

    # ── Single file: preserve X-ray fallback path ─────────────────────────────
    if len(files) == 1:
        file       = files[0]
        file_bytes = await file.read()

        try:
            text = await ocr_service.extract_text(file, file_bytes)
        except Exception as e:
            logger.error("OCR failed for %s: %s", file.filename, e)
            raise HTTPException(status_code=422, detail=f"OCR failed: {e}")

        # No text → try X-ray classifier
        if _is_empty(text):
            logger.info("No text in %s — routing to X-ray", file.filename)
            try:
                return await _handle_xray(file_bytes, language=language)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"X-ray analysis failed: {e}")

        logger.info("Single file OCR: %s (%d chars)", file.filename, len(text))
        try:
            return assemble_report(text, language=language)
        except Exception as e:
            logger.error("Report assembly failed: %s", e)
            raise HTTPException(status_code=500, detail=f"Report assembly failed: {e}")

    # ── Multiple files: parallel OCR → merge → single assembly pass ───────────
    logger.info("Multi-file upload: %d files, lang=%s", len(files), language)

    try:
        combined_text = await ocr_service.extract_text_multi(files)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Multi-file OCR failed: %s", e)
        raise HTTPException(status_code=422, detail=f"OCR failed: {e}")

    if _is_empty(combined_text):
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted from the uploaded files. "
                   "For X-ray images please upload them one at a time.",
        )

    logger.info("Multi-file OCR complete: %d chars total", len(combined_text))

    try:
        return assemble_report(combined_text, language=language)
    except Exception as e:
        logger.error("Report assembly failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Report assembly failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# ROUTE 2 — RAW TEXT
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/extract/text", summary="Submit raw report text")
async def extract_from_text(
    text:     str = Form(...),
    language: SupportedLanguage = Form(default="en"),
):
    """Submit raw OCR text directly. Supports single and multi-patient input."""
    if _is_empty(text):
        raise HTTPException(
            status_code=422,
            detail="Text is empty or too short. Provide at least 20 characters.",
        )
    try:
        return assemble_report(text, language=language)
    except Exception as e:
        logger.error("Report assembly failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Report assembly failed: {e}")


@app.post("/tts", summary="Convert text to speech")
async def text_to_speech(
    text:     str = Form(...),
    language: SupportedLanguage = Form(default="en"),
):
    if _is_empty(text):
        raise HTTPException(status_code=422, detail="Text too short.")
    try:
        audio_b64 = tts_service.synthesize(text, language=language)
        return JSONResponse({"audio_base64": audio_b64, "format": "mp3"})
    except Exception as e:
        logger.error("TTS failed: %s", e)
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", summary="Health check")
async def root():
    return {
        "status":    "ok",
        "service":   "Medical Report Processor",
        "routes":    ["/extract/file", "/extract/text"],
        "languages": ["en", "bn", "ar", "hi", "ur"],
        "limits":    {"max_files_per_request": _MAX_FILES},
    }