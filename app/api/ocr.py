from fastapi import APIRouter, File, UploadFile, HTTPException
from services.ocr_service import process_file
from fastapi.responses import Response
from fastapi.responses import FileResponse
import os
import json

router = APIRouter()


@router.post("/ocr/")
async def upload_file(file: UploadFile = File(...), in_lang="ch", out_lang="vi"):
    """API to process a file (PDF, DOCX, Image) and stream OCR results."""
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    file_data = await file.read()
    processed_file_path = process_file(file, file_data, in_lang, out_lang)
    response_data = {
        "status": 200,
        "data": {
            "file_path": processed_file_path
        },
        "message": "Done"
    }

    return Response(content=json.dumps(response_data, ensure_ascii=False), media_type="application/json")


@router.get("/downloads/{process_id}/{filename}")
async def download_file(process_id: str, filename: str):
    file_path = f"downloads/{process_id}/{filename}"  # Ensure this folder contains your PDFs
    print(file_path)
    # Check if the file exists
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/pdf', filename=filename)
    else:
        return {"error": "File not found"}
