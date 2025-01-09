from core.ocr_processing import ocr_pdf_processing, ocr_docx_processing, ocr_image_processing
from PIL import Image
import io
import numpy as np
from datetime import datetime
from paddleocr import PaddleOCR


# Singleton to manage PaddleOCR instance
class PaddleOCRManager:
    _instances = {}

    @classmethod
    def get_instance(cls, lang):
        """Retrieve a PaddleOCR instance for a specific language"""
        if lang not in cls._instances:
            cls._instances[lang] = PaddleOCR(
                use_angle_cls=True,
                lang=lang,
                type="structure",
                recovery=True,
                output="../output/"
            )
        return cls._instances[lang]


def process_file(file, file_data: bytes, lang):
    """Determine file type and process accordingly."""
    file_extension = file.filename.split('.')[-1].lower()
    file_name = file.filename.split('.')[0].lower()

    ocr = PaddleOCRManager.get_instance(lang)

    if file_extension == "pdf":
        now = datetime.now()
        date_str = now.strftime("%Y%m%d%H%M%S")
        # Save the file temporarily
        temp_file = f"{date_str}_{file_name}.pdf"
        with open(temp_file, "wb") as f:
            f.write(file_data)
        return ocr_pdf_processing(ocr, temp_file)

    elif file_extension == "docx":
        return ocr_docx_processing(file_data)

    elif file.content_type.startswith("image/"):
        image = Image.open(io.BytesIO(file_data))
        img = np.array(image)
        return ocr_image_processing(img)

    else:
        raise ValueError("Unsupported file type. Please upload PDF, DOCX, or image files.")
