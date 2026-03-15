from __future__ import annotations

import logging
import os
import gc
from typing import Literal, List

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.ocr_service          import OCRService
from services.assembler            import assemble_report
from services.xray_report          import XRayService
from services.multi_file_processor import MultiFileProcessor
from services.tts_service          import TTSService
from services.chat_service         import ChatService, ChatRequest, ChatResponse
from services.report_validator     import ReportValidator

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title       = "Medical Report Processor",
    description = "OCR → NER → LLM pipeline for Bangladeshi medical reports",
    version     = "1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request size limit ────────────────────────────────────────────────────────
@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    max_size = 500 * 1024 * 1024  # 500MB
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > max_size:
        return JSONResponse(
            status_code=413,
            content={"detail": "File too large. Maximum size is 500MB."}
        )
    return await call_next(request)

# ── Service initialization ────────────────────────────────────────────────────
ocr_service      = OCRService()      # Tesseract — ~50MB, loads instantly
chat_service     = ChatService()     # just an OpenAI client, very lightweight
tts_service      = TTSService()      # just HTTP calls, no model loaded
report_validator = ReportValidator()

# XRayService — lazy loaded on first x-ray request
_xray_service: XRayService | None = None

def get_xray_service() -> XRayService:
    global _xray_service
    if _xray_service is None:
        logger.info("Loading XRayService on first use...")
        _xray_service = XRayService()
        logger.info("XRayService loaded")
    return _xray_service

multi_processor = MultiFileProcessor(ocr_service, get_xray_service, report_validator)

SupportedLanguage = Literal["en", "bn", "ar", "hi", "ur"]
_MAX_FILES        = 20


def _is_empty(text: str | None) -> bool:
    if not text:
        return True
    import re
    return len(re.sub(r'[\s\W_]+', '', text)) < 20


# ══════════════════════════════════════════════════════════════════════════════
# ROUTE 1 — FILE(S) UPLOAD
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/extract/file", summary="Upload one or more PDFs/images for processing")
async def extract_from_file(
    files:    List[UploadFile] = File(...),
    language: SupportedLanguage = Form(default="en"),
):
    if not files:
        raise HTTPException(status_code=422, detail="No files provided.")

    if len(files) > _MAX_FILES:
        raise HTTPException(
            status_code=422,
            detail=f"Too many files — maximum is {_MAX_FILES} per request.",
        )

    # ── Single file ───────────────────────────────────────────────────────────
    if len(files) == 1:
        file       = files[0]
        file_bytes = await file.read()

        try:
            text = await ocr_service.extract_text(file, file_bytes)
        except Exception as e:
            logger.error("OCR failed for %s: %s", file.filename, e)
            raise HTTPException(status_code=422, detail=f"OCR failed: {e}")

        # No text → X-ray path
        if _is_empty(text):
            logger.info("No text in %s — routing to X-ray", file.filename)
            try:
                xray_result = get_xray_service().analyze(file_bytes)
                return assemble_report(xray_result=xray_result, language=language)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"X-ray analysis failed: {e}")

        # Text path
        validation = report_validator.validate(text)
        if not validation.is_medical:
            logger.warning(
                "Non-medical document rejected (%s): score=%d",
                file.filename, validation.score,
            )
            raise HTTPException(status_code=422, detail=validation.reason)

        logger.info(
            "Single file accepted (%s): %d chars, score=%d",
            file.filename, len(text), validation.score,
        )
        try:
            return assemble_report(text, language=language)
        except Exception as e:
            logger.error("Report assembly failed: %s", e)
            raise HTTPException(status_code=500, detail=f"Report assembly failed: {e}")

    # ── Multiple files → MultiFileProcessor ──────────────────────────────────
    try:
        return await multi_processor.process(files, language=language)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Multi-file processing failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Multi-file processing failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# ROUTE 2 — RAW TEXT
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/extract/text", summary="Submit raw report text")
async def extract_from_text(
    text:     str = Form(...),
    language: SupportedLanguage = Form(default="en"),
):
    if _is_empty(text):
        raise HTTPException(
            status_code=422,
            detail="Text is empty or too short. Provide at least 20 characters.",
        )

    validation = report_validator.validate(text)
    if not validation.is_medical:
        raise HTTPException(status_code=422, detail=validation.reason)

    try:
        return assemble_report(text, language=language)
    except Exception as e:
        logger.error("Report assembly failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Report assembly failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# ROUTE 3 — TTS
# ══════════════════════════════════════════════════════════════════════════════

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
# ROUTE 4 — CHATBOT (MediBot)
# ══════════════════════════════════════════════════════════════════════════════

@app.post(
    "/chat",
    response_model = ChatResponse,
    summary        = "MediBot chat powered by OpenAI (via ChatService)",
)
async def chat(req: ChatRequest) -> ChatResponse:
    try:
        return await chat_service.chat(req)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH + MEMORY CHECK
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

@app.get("/memory", summary="Current memory usage (MB)")
async def memory_usage():
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_mb  = process.memory_info().rss / 1024 / 1024
        return {
            "used_mb":     round(mem_mb, 2),
            "xray_loaded": _xray_service is not None,
        }
    except ImportError:
        return {"error": "psutil not installed — add it to requirements.txt"}