import io
import os
import asyncio
import logging
import numpy as np
import cv2

from typing import Union
from concurrent.futures import ThreadPoolExecutor, as_completed

from paddleocr import PaddleOCR
from PIL import Image, ImageFilter, ImageEnhance
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

# Max parallel OCR workers (each PaddleOCR call is CPU-bound)
_MAX_OCR_WORKERS = int(os.getenv("OCR_MAX_WORKERS", "4"))


class OCRService:

    def __init__(self):
        self._paddle_ocr = None
        self._init_engines()

    def _init_engines(self):
        try:
            self._paddle_ocr = PaddleOCR(
                use_angle_cls=True,
                lang='en',
                det_db_thresh=0.5,
                det_db_box_thresh=0.6,
                det_db_unclip_ratio=1.5,
                rec_algorithm='SVTR_LCNet',
                use_gpu=False,
            )
            logger.info("PaddleOCR initialized")
        except ImportError:
            logger.warning("PaddleOCR not available")

    # ══════════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ══════════════════════════════════════════════════════════════════════════

    async def extract_text(self, file: UploadFile, file_bytes: bytes) -> str:
        """
        Single-file entry point (unchanged signature — existing callers unaffected).
        Returns extracted text string.
        """
        self._validate_type(file.content_type)
        loop = asyncio.get_event_loop()

        if file.content_type == "application/pdf":
            return await loop.run_in_executor(None, self._extract_from_pdf, file_bytes)
        else:
            return await loop.run_in_executor(None, self._extract_from_image, file_bytes)

    async def extract_text_multi(self, files: list[UploadFile]) -> str:
        """
        Multi-file entry point.

        Reads all files, OCRs them in parallel (ThreadPoolExecutor), then joins
        the per-file texts with PAGE BREAK markers so the rest of the pipeline
        (patient splitting, section splitting, LLM extraction) sees one unified
        text stream — exactly as if it had come from a single multi-page PDF.

        File order is preserved in the output (file 0 text first, file N last).

        Args:
            files: list of UploadFile objects from the FastAPI multipart request.

        Returns:
            Single string with all files' text joined by PAGE BREAK markers.
        """
        if not files:
            return ""

        # ── Step 1: read all files concurrently (I/O bound) ──────────────────
        read_tasks = [file.read() for file in files]
        all_bytes: list[bytes] = await asyncio.gather(*read_tasks)

        # Validate types after reading so we give a useful error
        for file, content_type in zip(files, [f.content_type for f in files]):
            self._validate_type(content_type)

        # ── Step 2: OCR all files in parallel (CPU bound → thread pool) ──────
        loop = asyncio.get_event_loop()

        def _ocr_one(idx: int) -> tuple[int, str]:
            """OCR a single file. Returns (original_index, text)."""
            content_type = files[idx].content_type
            file_bytes   = all_bytes[idx]
            filename     = files[idx].filename or f"file_{idx}"
            try:
                if content_type == "application/pdf":
                    text = self._extract_from_pdf(file_bytes)
                else:
                    text = self._extract_from_image(file_bytes)
                logger.info("OCR done: %s (%d chars)", filename, len(text))
                return idx, text
            except Exception as e:
                logger.error("OCR failed for %s: %s", filename, e)
                return idx, ""  # keep slot so order is preserved

        with ThreadPoolExecutor(max_workers=min(len(files), _MAX_OCR_WORKERS)) as pool:
            futures = {pool.submit(_ocr_one, i): i for i in range(len(files))}
            results: dict[int, str] = {}
            for future in as_completed(futures):
                idx, text = future.result()
                results[idx] = text

        # ── Step 3: join in original file order ───────────────────────────────
        ordered_texts = [results.get(i, "") for i in range(len(files))]
        combined = "\n\n--- PAGE BREAK ---\n\n".join(
            t for t in ordered_texts if t.strip()
        )
        logger.info(
            "Multi-file OCR complete: %d files → %d chars total",
            len(files), len(combined),
        )
        return combined

    # ══════════════════════════════════════════════════════════════════════════
    # INTERNAL — image extraction
    # ══════════════════════════════════════════════════════════════════════════

    def _extract_from_image(self, image_bytes: bytes) -> str:
        img = self._preprocess_image(image_bytes)
        processed_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        if self._paddle_ocr:
            try:
                img_array = np.array(processed_image)
                result    = self._paddle_ocr.ocr(img_array, cls=True)

                if not result or result[0] is None or len(result[0]) == 0:
                    logger.warning("PaddleOCR returned no text boxes")
                    return ""

                sorted_rows    = self.sort_ocr_results(result[0], line_threshold=30)
                extracted_text = ""
                for box, (text, confidence) in sorted_rows:
                    extracted_text += text + " "
                return extracted_text

            except Exception as e:
                logger.error("PaddleOCR failed: %s", e)

        raise RuntimeError("No OCR engine available. Install paddleocr or pytesseract.")

    # ══════════════════════════════════════════════════════════════════════════
    # INTERNAL — PDF extraction
    # ══════════════════════════════════════════════════════════════════════════

    def _extract_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF.
        Tries direct text extraction first (fast, accurate for digital PDFs).
        Falls back to image OCR for scanned pages.
        Pages are joined with PAGE BREAK markers so the downstream splitter
        can use them as patient/section boundaries.
        """
        import pdfplumber

        text_pages = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text and len(page_text.strip()) > 50:
                    text_pages.append(page_text)
                else:
                    img       = page.to_image(resolution=300).original
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PNG")
                    ocr_text  = self._extract_from_image(img_bytes.getvalue())
                    text_pages.append(ocr_text)

        return "\n\n--- PAGE BREAK ---\n\n".join(text_pages)

    # ══════════════════════════════════════════════════════════════════════════
    # INTERNAL — helpers
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _validate_type(content_type: str | None) -> None:
        allowed = {"image/jpeg", "image/png", "application/pdf"}
        if content_type not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{content_type}'. "
                       f"Allowed: {', '.join(sorted(allowed))}",
            )

    def sort_ocr_results(self, lines, line_threshold=10):
        """Group boxes into rows, then sort left-to-right within each row."""
        sorted_lines = sorted(lines, key=lambda x: x[0][0][1])
        rows         = []
        current_row  = [sorted_lines[0]]

        for line in sorted_lines[1:]:
            y = line[0][0][1]
            if abs(y - current_row[-1][0][0][1]) < line_threshold:
                current_row.append(line)
            else:
                rows.append(sorted(current_row, key=lambda x: x[0][0][0]))
                current_row = [line]
        rows.append(sorted(current_row, key=lambda x: x[0][0][0]))

        return [item for row in rows for item in row]

    def crop_remove_signature(self, img_bytes: bytes):
        nparr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Image could not be loaded.")

        gray   = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 25, 15,
        )
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        height        = image.shape[0]
        signature_top = height

        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if w * h < 1000:
                continue
            if y > height * 0.87:
                signature_top = min(signature_top, y)

        cropped = image[:signature_top - 10, :] if signature_top < height else image
        return cropped

    def _preprocess_image(self, image: bytes):
        """Enhance image quality before OCR."""
        cropped_image = self.crop_remove_signature(image)
        cropped_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)
        img           = Image.fromarray(cropped_image)

        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        min_dim = 1000
        if max(img.size) < min_dim:
            scale    = min_dim / max(img.size)
            new_size = (int(img.width * scale), int(img.height * scale))
            img      = img.resize(
                new_size,
                resample=img.LANCZOS if hasattr(img, 'LANCZOS') else 1,
            )

        return img