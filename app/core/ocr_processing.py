import json
import os
import numpy as np
import docx
import io
import fitz
from googletrans import Translator
from PIL import Image, ImageDraw, ImageFont
import uuid
import openai
from dotenv import load_dotenv
import asyncio

translator = Translator()
DOWNLOADS_PATH = "downloads"
os.makedirs(f"{DOWNLOADS_PATH}", exist_ok=True)


def translate_text(text, out_language):
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    # Construct the prompt to instruct the model to translate the text
    prompt = f"Translate the following text to {out_language}: {text}"

    # Request the translation from OpenAI's GPT model
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.2,
    )
    # Extract and return the content
    return response.choices[0].message.content.strip()


def ocr_image_processing(ocr, img: np.array, page_number, out_lang):
    """Perform OCR on image and yield results."""
    translated_texts = []
    try:
        result = ocr.ocr(img, cls=True)
        for res in result:
            if res is None:  # Skip when empty result detected to avoid TypeError:NoneType
                print(f"[DEBUG] Empty page {page_number} detected, skip it.")
                continue
            for line in res:
                print(line[1][0])
                translated_text = translator.translate(line[1][0], dest=f'{out_lang}').text
                translated_texts.append((line[0], translated_text))
    except Exception as e:
        print(f"OCR processing failed for page {page_number}: {e}")
    return translated_texts


def transparent_image(image: Image) -> Image:
    trans_image = image.convert("RGBA")
    data = trans_image.getdata()
    new_data = []
    for item in data:
        # Replace (255, 255, 255) with the color you want to make transparent
        if item[:3] == (255, 255, 255):  # Check for white background
            new_data.append((255, 255, 255, 0))  # Set alpha to 0 (transparent)
        else:
            new_data.append(item)

    trans_image.putdata(new_data)
    return trans_image


def ocr_process(ocr, in_image, index, out_lang, use_openai: bool = False):
    async def translate_sentences(sentence):
        translator = Translator()
        translated_sentence = await translator.translate(sentence, dest=out_lang)
        return translated_sentence.text
    if out_lang == "vi":
        font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "doc/fonts/latin.ttf"))
    else:
        font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "doc/fonts/simfang.ttf"))
    translated_texts = []
    try:
        result = ocr.ocr(in_image, cls=True)
        for res in result:
            if res is None:  # Skip when empty result detected to avoid TypeError:NoneType
                print(f"[DEBUG] Empty page {index} detected, skip it.")
                continue
            for line in res:
                if use_openai:
                    translated_text = translate_text(line[1][0], out_lang)
                else:
                    translated_text = asyncio.run(translate_sentences(line[1][0]))

                translated_texts.append((line[0], translated_text))
    except Exception as e:
        print(f"OCR processing failed for page {index}: {e}")

    image = Image.fromarray(in_image)
    if translated_texts:
        draw = ImageDraw.Draw(image)
        margin = 1
        for box, translated_text in translated_texts:
            # Extract box coordinates
            top_left, _, bottom_right, _ = box
            x1, y1 = map(int, top_left)
            x2, y2 = map(int, bottom_right)
            x1 = max(0, x1 - margin)
            y1 = max(0, y1 - margin)

            # Calculate average color using NumPy
            cropped_region = np.array(image.crop((x1, y1, x2, y2)))
            avg_color = tuple(cropped_region.mean(axis=(0, 1)).astype(int))

            # Draw rectangle with background color
            draw.rectangle([x1, y1, x2, y2], fill=avg_color)

            # Generate text image with dynamic font size
            rect_width, rect_height = x2 - x1, y2 - y1
            font_size = max(3, int(rect_height * 0.7))
            calculated_font = ImageFont.truetype(font=font_path, size=font_size)

            while True:
                text_bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), translated_text,
                                                                              font=calculated_font)
                if text_bbox[2] <= rect_width or font_size <= 3:
                    break
                font_size -= 1
                calculated_font = ImageFont.truetype(font=font_path, size=font_size)

            # Center text within the rectangle
            text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
            text_x, text_y = x1 + (rect_width - text_width) // 2, y1 + (rect_height - text_height) // 2
            draw.text((text_x, text_y), translated_text, fill="black", font=calculated_font)

    return image


def ocr_pdf_processing(ocr, file_path: str, out_lang: str):
    """Process PDF and yield OCR results page by page."""
    font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "doc/fonts/latin.ttf"))
    process_id = str(uuid.uuid4())
    out_file_path = os.path.join(DOWNLOADS_PATH, process_id)
    os.makedirs(out_file_path, exist_ok=True)
    output_images = []

    with fitz.open(file_path) as pdf:
        print("=======================")
        print(f"Total pages: {pdf.page_count}")
        print("=======================")

        for pg in range(pdf.page_count):
            page = pdf[pg]
            print(f"Processing page {pg + 1}")

            # Render page as image
            mat = fitz.Matrix(2, 2)
            pm = page.get_pixmap(matrix=mat, alpha=False)
            if pm.width > 2000 or pm.height > 2000:
                pm = page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)

            img = Image.frombytes("RGB", [pm.width, pm.height], pm.samples)
            img = np.array(img)

            translated_texts = ocr_image_processing(ocr, img, pg + 1, out_lang)
            image = Image.fromarray(img)
            draw = ImageDraw.Draw(image)

            for box, translated_text in translated_texts:
                # Extract box coordinates
                top_left, _, bottom_right, _ = box
                x1, y1 = map(int, top_left)
                x2, y2 = map(int, bottom_right)

                # Calculate average color using NumPy
                cropped_region = np.array(image.crop((x1, y1, x2, y2)))
                avg_color = tuple(cropped_region.mean(axis=(0, 1)).astype(int))

                # Draw rectangle with background color
                draw.rectangle([x1, y1, x2, y2], fill=avg_color)

                # Generate text image with dynamic font size
                rect_width, rect_height = x2 - x1, y2 - y1
                font_size = max(3, int(rect_height * 0.7))
                calculated_font = ImageFont.truetype(font=font_path, size=font_size)

                while True:
                    text_bbox = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), translated_text,
                                                                                  font=calculated_font)
                    if text_bbox[2] <= rect_width or font_size <= 3:
                        break
                    font_size -= 1
                    calculated_font = ImageFont.truetype(font=font_path, size=font_size)

                # Center text within the rectangle
                text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
                text_x, text_y = x1 + (rect_width - text_width) // 2, y1 + (rect_height - text_height) // 2
                draw.text((text_x, text_y), translated_text, fill="black", font=calculated_font)

            output_images.append(image)

        # Save processed images as a PDF
        output_pdf_path = os.path.join(out_file_path, f"{process_id}_{os.path.basename(file_path)}")
        output_images[0].save(output_pdf_path, save_all=True, append_images=output_images[1:])

    return output_pdf_path


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