import json
from paddleocr import PPStructure
import numpy as np
from PIL import Image
import docx
import io

ocr_engine = PPStructure(table=False, ocr=True, show_log=True)


def ocr_image_processing(img: np.array):
    """Perform OCR on image and yield results."""
    result = ocr_engine(img)
    ocr_result = ""
    for res in result:
        for item in res['res']:
            ocr_result += f"{item['text']}\n"
    yield json.dumps({"page": 1, "text": ocr_result.strip()}, ensure_ascii=False)


def ocr_pdf_processing(file_path: str):
    """Process PDF and yield OCR results page by page."""
    import fitz
    with fitz.open(file_path) as pdf:
        for pg in range(0, pdf.page_count):
            page = pdf[pg]
            mat = fitz.Matrix(2, 2)
            pm = page.get_pixmap(matrix=mat, alpha=False)

            if pm.width > 2000 or pm.height > 2000:
                pm = page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)

            img = Image.frombytes("RGB", [pm.width, pm.height], pm.samples)
            img = np.array(img)
            yield from ocr_image_processing(img)


def ocr_docx_processing(file_data: bytes):
    """Process DOCX file and yield OCR results."""
    doc = docx.Document(io.BytesIO(file_data))
    ocr_result = ""
    page = 1  # Treat each paragraph as a "page"
    for para in doc.paragraphs:
        ocr_result += para.text + "\n"
        yield json.dumps({"page": page, "text": ocr_result.strip()}, ensure_ascii=False)
        page += 1
        ocr_result = ""
