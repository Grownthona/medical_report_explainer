import os
# os.environ["FLAGS_use_mkldnn"] = "0"
# # or
# os.environ["PADDLE_DISABLE_ONEDNN"] = "1"

from fastapi import FastAPI, File, UploadFile
from services.ocr_service import OCRService;
from services.report_assembler import assemble_report;
from models.schemas import MedicalNERResponse
from models.schemas import MedicalEntityOut
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post(
    "/extract/text"
)
async def extract_medical(file: UploadFile = File(...)):
    text = await OCRService().extract_text(file)

    entities = assemble_report(text)
    return {
        "text": text,
        "entities": entities
    }