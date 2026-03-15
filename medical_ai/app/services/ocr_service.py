import io
import os
import logging
import asyncio
import numpy as np
import cv2

from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
from fastapi import UploadFile, HTTPException
import pytesseract
#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

logger = logging.getLogger(__name__)

_MAX_OCR_WORKERS  = int(os.getenv("OCR_MAX_WORKERS", "2"))
_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "application/pdf"}


class OCRService:

    def __init__(self):
        logger.info("OCRService created (Tesseract — ~50MB RAM)")

    def validate_file_type(self, content_type: str | None) -> None:
        if content_type not in _ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{content_type}'. Allowed: {', '.join(sorted(_ALLOWED_CONTENT_TYPES))}"
            )

    async def extract_text(self, file: UploadFile, file_bytes: bytes) -> str:
        self.validate_file_type(file.content_type)
        loop = asyncio.get_event_loop()
        if file.content_type == "application/pdf":
            return await loop.run_in_executor(None, self._extract_from_pdf, file_bytes)
        else:
            return await loop.run_in_executor(None, self._extract_from_image, file_bytes)

    async def extract_text_multi(self, files: list[UploadFile]) -> str:
        if not files:
            return ""

        read_tasks  = [file.read() for file in files]
        all_bytes   = await asyncio.gather(*read_tasks)

        for f in files:
            self.validate_file_type(f.content_type)

        loop = asyncio.get_event_loop()

        def _ocr_one(idx):
            try:
                if files[idx].content_type == "application/pdf":
                    text = self._extract_from_pdf(all_bytes[idx])
                else:
                    text = self._extract_from_image(all_bytes[idx])
                logger.info("OCR done: %s (%d chars)", files[idx].filename, len(text))
                return idx, text
            except Exception as e:
                logger.error("OCR failed for %s: %s", files[idx].filename, e)
                return idx, ""

        with ThreadPoolExecutor(max_workers=min(len(files), _MAX_OCR_WORKERS)) as pool:
            futures  = {pool.submit(_ocr_one, i): i for i in range(len(files))}
            results  = {}
            for future in as_completed(futures):
                idx, text = future.result()
                results[idx] = text

        ordered = [results.get(i, "") for i in range(len(files))]
        return "\n\n--- PAGE BREAK ---\n\n".join(t for t in ordered if t.strip())

    def _extract_from_image(self, image_bytes: bytes) -> str:
        img = self._preprocess_image(image_bytes)
        # Tesseract config: treat as single column, preserve layout
        config = "--oem 3 --psm 6 -l eng"
        text   = pytesseract.image_to_string(img, config=config)
        logger.info("Tesseract extracted %d chars", len(text))
        return text.strip()

    def _extract_from_pdf(self, pdf_bytes: bytes) -> str:
        from pdf2image import convert_from_bytes
        #poppler_path = r"C:\poppler\Library\bin"
        pages      = convert_from_bytes(pdf_bytes, dpi=300)
        text_pages = []
        for page_img in pages:
            # Try direct text extraction first via pdfplumber
            text = pytesseract.image_to_string(page_img, config="--oem 3 --psm 6 -l eng")
            text_pages.append(text.strip())
        return "\n\n--- PAGE BREAK ---\n\n".join(t for t in text_pages if t)

    def _preprocess_image(self, image_bytes: bytes) -> Image.Image:
        nparr  = np.frombuffer(image_bytes, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_cv is None:
            raise ValueError("Could not decode image")

        # Upscale if too small
        h, w = img_cv.shape[:2]
        if max(h, w) < 1000:
            scale  = 1000 / max(h, w)
            img_cv = cv2.resize(img_cv, (int(w * scale), int(h * scale)),
                                interpolation=cv2.INTER_CUBIC)

        # Convert to grayscale + denoise
        gray    = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        return Image.fromarray(denoised)

    # backward compat
    @staticmethod
    def _validate_type(content_type):
        if content_type not in _ALLOWED_CONTENT_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported file type '{content_type}'")