from fastapi import APIRouter, File, UploadFile, HTTPException
from services.ocr_service import process_file
from fastapi.responses import Response
from fastapi.responses import FileResponse
from fastapi.concurrency import run_in_threadpool
from concurrent.futures import ThreadPoolExecutor
import os
import json
from typing import List
import uuid

router = APIRouter()
DOWNLOADS_PATH = "downloads"
os.makedirs(f"{DOWNLOADS_PATH}", exist_ok=True)


@router.post("/ocr/")
async def upload_files(
        files: List[UploadFile] = File(...),
        in_lang: str = "ch",
        out_lang: str = "vi",
        use_openai: bool= False
):
    """API to process a list of image files and stream OCR results."""
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    def process_file_sync(index, file, file_data, in_lang, out_lang, use_openai):
        return process_file(index, file, file_data, in_lang, out_lang, use_openai)

    output_images = []
    process_id = str(uuid.uuid4())
    out_file_path = os.path.join(DOWNLOADS_PATH, process_id)
    output_pdf_path = os.path.join(out_file_path, f"{process_id}_trans.pdf")
    os.makedirs(out_file_path, exist_ok=True)

    with ThreadPoolExecutor() as executor:
        futures = [run_in_threadpool(process_file_sync, index, file, await file.read(), in_lang, out_lang, use_openai) for index, file in enumerate(files)]

        for index, future in enumerate(futures):
            processed_image = await future
            output_images.append(processed_image)

    # Merge all processed images into a PDF
    output_images[0].save(output_pdf_path, save_all=True, append_images=output_images[1:])

    response_data = {
        "status": 200,
        "data": {
            "file_path": output_pdf_path
        },
        "message": "All files processed and merged into PDF"
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
