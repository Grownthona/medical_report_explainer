import os
import shutil
import cv2
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
from fastapi import UploadFile, File, HTTPException
from paddleocr import PaddleOCR
# from paddleocr import PPStructure

class OCRService:
    def __init__(self):
        self.ocr = PaddleOCR(
                    use_angle_cls=True,
                    lang='en',
                    det_db_thresh=0.5,
                    det_db_box_thresh=0.6,
                    det_db_unclip_ratio=1.5,
                    rec_algorithm='SVTR_LCNet',
                    use_gpu=False
                )
        
    async def _extract_from_image(self, file: UploadFile = File(...)):
        if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        file_location = f"uploads/{file.filename}"

        os.makedirs("uploads", exist_ok=True)

        # copying file into uploads folder
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        image = cv2.imread(file_location)

        processed_image = self._preprocess_image(file_location)

        # Convert PIL → OpenCV
        processed_image = cv2.cvtColor(np.array(processed_image), cv2.COLOR_RGB2BGR)
        processed_path = f"processed_{file.filename}"
        cv2.imwrite(processed_path, processed_image)

        # table_engine = PPStructure(show_log=False)
        result = self.ocr.ocr(processed_path, cls=True)
        print("Sample result:", result[:3]) 
        # SORT HERE
        sorted_rows = self.sort_ocr_results(result[0], line_threshold=30)

        formatted_text = []
        extracted_text = ""

        for box, (text, confidence) in sorted_rows:
            formatted_text.append(
                f"<span style='font-weight: bold;'>~ {text}</span> - : {confidence:.2f}"
            )
            extracted_text += text + " "


        os.remove(file_location)
        combined_text = "<br>".join(formatted_text)
        
        return combined_text
    
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
    
    def crop_remove_signature(self, image_path):
        image = cv2.imread(image_path)
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

            # If contour is in bottom 15% of image
            if y > height * 0.85:
                signature_top = min(signature_top, y)

        # Crop ABOVE signature
        if signature_top < height:
            cropped = image[:signature_top - 10, :]  # small padding
        else:
            cropped = image

        return cropped
    

    def _preprocess_image(self, image_path):
        """Enhance image quality before OCR."""

        # Crop Signature
        cropped_image = self.crop_remove_signature(image_path)

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