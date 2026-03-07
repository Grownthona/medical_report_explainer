import io
import os
import shutil
import cv2
import base64
import asyncio
import logging
import numpy as np
from typing import Union

from paddleocr import PaddleOCR
from PIL import Image, ImageFilter, ImageEnhance
from fastapi import UploadFile, File, HTTPException
# from paddleocr import PPStructure


logger = logging.getLogger(__name__)
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
                use_gpu=False
            )
            logger.info("✅ PaddleOCR initialized")
        except ImportError:
            logger.warning("PaddleOCR not available, falling back to Tesseract")

    async def extract_text(self, file: UploadFile, file_bytes:bytes) -> str:
        """Main entry point. Returns extracted text string."""

        if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # file_bytes = await file.read()
        loop = asyncio.get_event_loop()

        if file.content_type == "application/pdf":
            return await loop.run_in_executor(None, self._extract_from_pdf, file_bytes)
        else:
            return await loop.run_in_executor(None, self._extract_from_image, file_bytes)


    def _extract_from_image(self, image_bytes: bytes) -> str:

        img = Image.open(io.BytesIO(image_bytes))
        img = self._preprocess_image(image_bytes)
        # file_location = f"app/uploads/{file.filename}"

        # Convert PIL → OpenCV
        processed_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        # processed_path = f"app/processed/processed_{file.filename}"
        # os.makedirs("app/processed", exist_ok=True)
        # cv2.imwrite(processed_path, processed_image)

        if self._paddle_ocr:
            try:
                img_array = np.array(processed_image)
                result = self._paddle_ocr.ocr(img_array, cls=True)

                if not result or result[0] is None or len(result[0]) == 0:
                    logger.warning("PaddleOCR returned no text boxes — image may be blank or unreadable")
                    return ""

                # SORT HERE
                sorted_rows = self.sort_ocr_results(result[0], line_threshold=30)
                # formatted_text = []
                extracted_text = ""

                for box, (text, confidence) in sorted_rows:
                    # formatted_text.append(
                    #     f"<span style='font-weight: bold;'>~ {text}</span> - : {confidence:.2f}"
                    # )
                    extracted_text += text + " "
                    
                    #combined_text = "<br>".join(formatted_text)
                return extracted_text
            except Exception as e:
                logger.error(f"PaddleOCR failed: {e}")

        raise RuntimeError("No OCR engine available. Install paddleocr or pytesseract.")
    

    def _extract_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF - try direct text extraction first, then OCR."""

        import pdfplumber

        text_pages = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                # Try direct text extraction (faster, more accurate for digital PDFs)
                page_text = page.extract_text()
                if page_text and len(page_text.strip()) > 50:
                    text_pages.append(page_text)
                else:
                    # Scanned PDF - render page as image then OCR
                    img = page.to_image(resolution=300).original
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PNG")
                    ocr_text = self._extract_from_image(img_bytes.getvalue())
                    text_pages.append(ocr_text)

        return "\n\n--- PAGE BREAK ---\n\n".join(text_pages)

    def sort_ocr_results(self, lines, line_threshold=10):

        """Group boxes into rows, then sort left-to-right within each row."""
        sorted_lines = sorted(lines, key=lambda x: x[0][0][1])  # sort by y
        rows = []
        current_row = [sorted_lines[0]]

        for line in sorted_lines[1:]:
            y = line[0][0][1]
            if abs(y - current_row[-1][0][0][1]) < line_threshold:
                current_row.append(line)
            else:
                rows.append(sorted(current_row, key=lambda x: x[0][0][0]))  # sort row by x
                current_row = [line]
        rows.append(sorted(current_row, key=lambda x: x[0][0][0]))

        return [item for row in rows for item in row]
    
    def crop_remove_signature(self, img_bytes : bytes):

        nparr = np.frombuffer(img_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Image could not be loaded.")
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            25,
            15
        )

        contours, _ = cv2.findContours(
            thresh,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        height = image.shape[0]

        signature_top = height  # default = no signature found

        for c in contours:
            x, y, w, h = cv2.boundingRect(c)

            area = w * h

            # Ignore tiny noise
            if area < 1000:
                continue

            # If contour is in bottom 10% of image
            if y > height * 0.87:
                signature_top = min(signature_top, y)

        # Crop ABOVE signature
        if signature_top < height:
            cropped = image[:signature_top - 10, :]  # small padding
        else:
            cropped = image

        return cropped
    

    def _preprocess_image(self, image:bytes):
        """Enhance image quality before OCR."""

        # Crop Signature
        cropped_image = self.crop_remove_signature(image)

        # Convert OpenCV (BGR) → RGB
        cropped_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)

        # Convert to PIL Image
        img = Image.fromarray(cropped_image)

        # Convert to RGB if needed
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        # Resize if too small (OCR struggles under 300 DPI equivalent)
        min_dim = 1000
        if max(img.size) < min_dim:
            scale = min_dim / max(img.size)
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, resample=img.LANCZOS if hasattr(img, 'LANCZOS') else 1)

        # Enhance contrast and sharpness
        #img = ImageEnhance.Contrast(img).enhance(1.5)
        # img = ImageEnhance.Sharpness(img).enhance(2.0)

        # Denoise
        #img = img.filter(ImageFilter.MedianFilter(size=3))

        return img

    
    # def _preprocess_image(self,image_path):
        # Read image
        # image = cv2.imread(image_path)
        # print(image)

        # # 1️⃣ Resize (improves OCR detection)
        # height, width = image.shape[:2]
        # image = cv2.resize(image, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)

        # # 2️⃣ Convert to Grayscale
        # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # # # 3️⃣ Increase Contrast using CLAHE
        # # clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        # # contrast = clahe.apply(gray)

        # # # 4️⃣ Denoising
        # # denoised = cv2.fastNlMeansDenoising(contrast, h=35)

        # # # 5️⃣ Thresholding (optional but powerful)
        # # processed = cv2.adaptiveThreshold(
        # #     denoised,
        # #     255,
        # #     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        # #     cv2.THRESH_BINARY,
        # #     11,
        # #     2
        # # )

        # return gray