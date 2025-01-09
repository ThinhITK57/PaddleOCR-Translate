import json
import os
import numpy as np
import docx
import io
import fitz
from googletrans import Translator
from PIL import Image, ImageDraw, ImageFont
import uuid
translator = Translator()


def ocr_image_processing(ocr, img: np.array, page_number):
    """Perform OCR on image and yield results."""
    translated_texts = []
    try:
        result = ocr.ocr(img, cls=True)
        ocr_result = ""
        for res in result:
            if res is None:  # Skip when empty result detected to avoid TypeError:NoneType
                print(f"[DEBUG] Empty page {page_number} detected, skip it.")
                # yield json.dumps({"page": page_number, "text": ""}, ensure_ascii=False)
                continue
            for line in res:
                translated_text = translator.translate(line[1][0], src='en', dest='vi').text
                translated_texts.append((line[0], translated_text))
                ocr_result += f"{line[1][0]}\n"
        # yield json.dumps({"page": page_number, "text": ocr_result.strip()}, ensure_ascii=False)
    except Exception as e:
        print(f"OCR processing failed for page {page_number}: {e}")
        # yield json.dumps({"page": page_number, "text": "", "error": str(e)}, ensure_ascii=False)

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


# def fake_text_image(generated_text, text_size, text_width):
#     text_image = FakeTextDataGenerator.generate(
#         0,
#         f"{generated_text}",
#         "trdg/fonts/vi/RobotoSlab-Black.ttf",
#         None,
#         text_size,
#         "jpg",
#         0,
#         False,
#         0,
#         False,
#         1,
#         0,
#         0,
#         False,
#         0,
#         -1,
#         width=text_width,
#         text_color="#010101",
#         orientation=0,
#         space_width=1,
#         character_spacing=0,
#         alignment=0,
#         fit=False,
#         word_split=False,
#         output_mask=False,
#         margins=(1, 1, 1, 1),
#         image_dir=os.path.join(os.path.split(os.path.realpath(__file__))[0], "./trdg/images"),
#     )
#
#     return text_image

def images_to_pdf(image_list, output_pdf):
    """
    Merge a list of images into a single PDF file.

    :param image_list: List of image file paths
    :param output_pdf: Output PDF file path
    """
    # Open the images
    images = [Image.open(image).convert("RGB") for image in image_list]

    # Save the first image with the rest as additional pages
    images[0].save(output_pdf, save_all=True, append_images=images[1:])
    print(f"PDF created successfully at {output_pdf}")


def ocr_pdf_processing(ocr, file_path: str):
    """Process PDF and yield OCR results page by page."""
    font_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "doc/fonts/latin.ttf"))
    process_id = str(uuid.uuid4())
    os.makedirs(process_id, exist_ok=True)
    output_images = []
    with fitz.open(file_path) as pdf:
        print("=======================")
        print(f"Total pages: {pdf.page_count}")
        print("=======================")
        # for pg in range(0, pdf.page_count):
        for pg in range(0, 1):
            page = pdf[pg]
            print(f"Processing page {pg + 1}")
            mat = fitz.Matrix(2, 2)
            pm = page.get_pixmap(matrix=mat, alpha=False)
            if pm.width > 2000 or pm.height > 2000:
                pm = page.get_pixmap(matrix=fitz.Matrix(1, 1), alpha=False)

            img = Image.frombytes("RGB", [pm.width, pm.height], pm.samples)
            img = np.array(img)
            translated_texts = ocr_image_processing(ocr, img, pg + 1)
            image = Image.fromarray(img)
            draw = ImageDraw.Draw(image)
            for box, translated_text in translated_texts:
                # Lấy tọa độ box
                top_left, top_right, bottom_right, bottom_left = box
                x1, y1 = map(int, top_left)
                x2, y2 = map(int, bottom_right)
                print(x1, y1, x2, y2)
                # Cropped image to calculate background
                cropped_region = image.crop((x1, y1, x2, y2))
                pixels = list(cropped_region.getdata())
                num_pixels = len(pixels)
                if image.mode == "RGB":
                    avg_color = tuple(sum(c[i] for c in pixels) // num_pixels for i in range(3))
                else:
                    avg_color = (255, 255, 255)

                # Vẽ hình chữ nhật (tùy chọn)
                draw.rectangle([x1, y1, x2, y2], fill=avg_color)
                # generate_text_image = generate_text_image(translated_text, )
                rect_width = x2 - x1
                rect_height = y2 - y1
                rect_image = Image.new("RGB", (rect_width, rect_height), avg_color)
                draw_rect = ImageDraw.Draw(rect_image)
                scaling_factor = 0.7
                font_size = int(rect_height * scaling_factor)
                calculated_font = ImageFont.truetype(font=font_path, size=font_size)

                text_bbox = draw_rect.textbbox((0, 0), translated_text, font=calculated_font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]

                while text_width > rect_width:
                    font_size -= 1
                    calculated_font = ImageFont.truetype(font=font_path, size=font_size)
                    text_bbox = draw_rect.textbbox((0, 0), translated_text, font=calculated_font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]

                text_x = (rect_width - text_width) // 2
                text_y = (rect_height - text_height) // 2

                text_x += x1
                text_y += y1
                print(f"Text x: {text_x} -- Text y: {text_y}")
                # Chọn màu chữ dựa trên màu nền
                luminance = 0.299 * avg_color[0] + 0.587 * avg_color[1] + 0.114 * avg_color[2]
                text_color = (0, 0, 0) if luminance > 128 else (255, 255, 255)

                print("===============================================")
                # Vẽ chữ vào ảnh
                draw.text((text_x, text_y), translated_text, fill="black", font=calculated_font)

            output_image_path = f"{process_id}/output_page_{pg + 1}.jpg"
            image.save(output_image_path)
            output_images.append(output_image_path)

        output_pdf_path = f"{process_id}/{process_id}_{file_path}"
        images_to_pdf(output_images, output_pdf_path)
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

