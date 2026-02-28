import os
# os.environ["FLAGS_use_mkldnn"] = "0"
# # or
# os.environ["PADDLE_DISABLE_ONEDNN"] = "1"

from fastapi import FastAPI, File, UploadFile
from services.ocr_service import OCRService;

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/extract/text/")
async def create_upload_file(file: UploadFile = File(...)):
    ocr_service = OCRService()
    ocr_result = await ocr_service._extract_from_image(file)
    return {"result": ocr_result}
