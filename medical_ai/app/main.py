import os
# os.environ["FLAGS_use_mkldnn"] = "0"
# # or
# os.environ["PADDLE_DISABLE_ONEDNN"] = "1"

from fastapi import FastAPI, File, UploadFile
from services.ocr_service import OCRService;
from services.report_assembler import assemble_report;
from models.schemas import MedicalNERResponse
from models.schemas import MedicalEntityOut
from services.xray_report import XRayService
from services.classifier import classify
app = FastAPI()

from paddleocr import PaddleOCR


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post(
    "/extract/text"
)
async def extract_medical(file: UploadFile = File(...)):

    file_bytes = await file.read()
    text = await OCRService().extract_text(file,file_bytes)
    if text is None or text == "":
        xray = XRayService().analyze(file_bytes)
        return xray    
    
    classification = classify(text)

    return {
        "classification" : classification
    }
    #entities = assemble_report(text)
    # return {
    #     "text": text,
    #     "entities": entities
    # }