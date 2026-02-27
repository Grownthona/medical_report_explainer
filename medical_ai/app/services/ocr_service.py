import os
import shutil
import cv2
import numpy as np
from fastapi import UploadFile, File, HTTPException
from paddleocr import PaddleOCR

class OCRService:
    async def _extract_from_image(self, file: UploadFile = File(...)):
        if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        file_location = f"uploads/{file.filename}"

        os.makedirs("uploads", exist_ok=True)

        # copying file into uploads folder
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        processed_image = self._preprocess_image(file_location)

        processed_path = f"processed_{file.filename}"
        cv2.imwrite(processed_path, processed_image)

        ocr = PaddleOCR(use_angle_cls=True,lang='en', det_db_thresh=0.3,rec_algorithm='CRNN',use_gpu=False)

        result = ocr.ocr(file_location)
        formatted_text = []

        extracted_text = ""
        for line in result[0]:
            extracted_text += line[1][0] + "\n"
            confidence = line[1][1]

            # Format the text for display
            formatted_text.append(f"<span style='font-weight: bold;'>~ {line[1][0]}</span> - : {confidence:.2f}")


        os.remove(file_location)
        combined_text = "<br>".join(formatted_text)
        
        return combined_text
    
    def _preprocess_image(self,image_path):
        # Read image
        image = cv2.imread(image_path)

        # 1️⃣ Resize (improves OCR detection)
        height, width = image.shape[:2]
        image = cv2.resize(image, (width * 2, height * 2), interpolation=cv2.INTER_CUBIC)

        # 2️⃣ Convert to Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # # 3️⃣ Increase Contrast using CLAHE
        # clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        # contrast = clahe.apply(gray)

        # # 4️⃣ Denoising
        # denoised = cv2.fastNlMeansDenoising(contrast, h=35)

        # # 5️⃣ Thresholding (optional but powerful)
        # processed = cv2.adaptiveThreshold(
        #     denoised,
        #     255,
        #     cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        #     cv2.THRESH_BINARY,
        #     11,
        #     2
        # )

        return gray