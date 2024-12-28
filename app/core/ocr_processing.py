import json
from paddleocr import PPStructure, PaddleOCR
import numpy as np
from PIL import Image
import docx
import io
import fitz

ocr_engine = PPStructure(table=True, ocr=True, show_log=True)
ocr_paddle = PaddleOCR(use_angle_cls=True, lang="ch")


def ocr_image_processing(img: np.array, page_number):
    """Perform OCR on image and yield results."""
    try:
        result = ocr_engine(img)
        if not result[0]['res']:
            print(f"[DEBUG] Single box detected on page {page_number}, using ocr_paddle.")
            paddle_result = ocr_paddle.ocr(img, cls=True)
            ocr_result = ""
            for line in paddle_result[0]:
                ocr_result += f"{line[1][0]}\n"
            yield json.dumps({"page": page_number, "text": ocr_result.strip()}, ensure_ascii=False)
            return

        ocr_result = ""
        for res in result:
            for item in res['res']:
                ocr_result += f"{item['text']}\n"
        yield json.dumps({"page": page_number, "text": ocr_result.strip()}, ensure_ascii=False)
    except Exception as e:
        print(f"OCR processing failed for page {page_number}: {e}")
        yield json.dumps({"page": page_number, "text": "", "error": str(e)}, ensure_ascii=False)


def ocr_pdf_processing(file_path: str):
    """Process PDF and yield OCR results page by page."""
    with fitz.open(file_path) as pdf:
        print("=======================")
        print(f"Total pages: {pdf.page_count}")
        print("=======================")

        for pg in range(0, pdf.page_count):
            page = pdf[pg]
            print(f"Processing page {pg + 1}")
            mat = fitz.Matrix(2, 2)
            pm = page.get_pixmap(matrix=mat, alpha=False)
            if pm.width > 2000 or pm.height > 2000:
                pm = page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)

            img = Image.frombytes("RGB", [pm.width, pm.height], pm.samples)
            img = np.array(img)
            yield from ocr_image_processing(img, pg + 1)


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

