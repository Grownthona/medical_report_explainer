import os
# os.environ["FLAGS_use_mkldnn"] = "0"
# # or
# os.environ["PADDLE_DISABLE_ONEDNN"] = "1"

from fastapi import FastAPI, File, UploadFile
from services.ocr_service import OCRService;
from services.report_assembler import assemble_report
from models.schemas import MedicalNERResponse
from models.schemas import MedicalEntityOut
from services.xray_report import XRayService
from services.classifier import classify
from services.assembler import assemble_report
from services.llm_extractor import split_by_category,extract_multi_section,extract_report
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # your Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post(
    "/extract/text"
)
async def extract_medical(file: UploadFile = File(...)):

    file_bytes = await file.read()
    text = await OCRService().extract_text(file,file_bytes)
    # if text is None or text == "":
    #     xray = XRayService().analyze(file_bytes)
    #     return xray    
    
    assembler = assemble_report(text)
    # split_category = split_by_category(text)

    return assembler
    #entities = assemble_report(text)
    # return {
    #     "text": text,
    #     "entities": entities
    # }