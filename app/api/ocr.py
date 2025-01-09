from fastapi import APIRouter, File, UploadFile, HTTPException
from services.ocr_service import process_file
from sse_starlette import EventSourceResponse
from fastapi.responses import FileResponse
import os

router = APIRouter()


@router.post("/ocr/")
async def upload_file(file: UploadFile = File(...), lang="ch"):
    """API to process a file (PDF, DOCX, Image) and stream OCR results."""
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    file_data = await file.read()
    processed_file_path = process_file(file, file_data, lang)

    return {"file_path": processed_file_path}


@router.get("/download/")
async def download_file(file_path: str):
    """
    API to download the processed file.
    """
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(file_path, media_type="application/octet-stream", filename=os.path.basename(file_path))
