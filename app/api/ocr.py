from fastapi import APIRouter, File, UploadFile, HTTPException
from services.ocr_service import process_file
from sse_starlette import EventSourceResponse

router = APIRouter()


@router.post("/ocr/")
async def upload_file(file: UploadFile = File(...)):
    """API to process a file (PDF, DOCX, Image) and stream OCR results."""
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    file_data = await file.read()

    # Process file using the OCR service
    return EventSourceResponse(
        process_file(file, file_data),
        media_type="application/json"
    )
