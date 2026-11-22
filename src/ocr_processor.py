import io
import logging
from pathlib import Path
from typing import Optional
import fitz  # PyMuPDF
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from src.config import get_settings

logger = logging.getLogger("docgen.ocr")
settings = get_settings()


class OCRProcessor:
    """
    Performs Optical Character Recognition on scanned PDF pages using Tesseract.
    Renders high-DPI images directly from PyMuPDF, avoiding external poppler dependencies.
    """

    def __init__(self):
        tesseract_bin = settings.resolve_tesseract_path()
        if tesseract_bin:
            pytesseract.pytesseract.tesseract_cmd = tesseract_bin
            self.tesseract_available = True
            logger.info(f"Tesseract OCR initialized from: {tesseract_bin}")
        else:
            self.tesseract_available = False
            logger.warning("Tesseract binary not found. Scanned OCR fallback will be limited.")

    @staticmethod
    def preprocess_image(image: Image.Image) -> Image.Image:
        """
        Enhances image for OCR accuracy: converts to grayscale, increases contrast,
        and applies gentle sharpening.
        """
        # Convert to Grayscale
        gray = image.convert("L")

        # Contrast enhancement
        enhancer = ImageEnhance.Contrast(gray)
        enhanced = enhancer.enhance(1.8)

        # Gentle sharpen to make text edges crisp
        sharpened = enhanced.filter(ImageFilter.SHARPEN)
        return sharpened

    def extract_page_ocr(self, file_path: Path, page_number: int) -> tuple[str, float]:
        """
        Renders a specific PDF page to an in-memory 300 DPI image and performs OCR.
        Returns extracted text and average confidence score.
        """
        if not self.tesseract_available:
            return (
                f"[OCR Skipped: Tesseract OCR is not installed or configured on this host for page {page_number}]",
                0.0
            )

        try:
            doc = fitz.open(str(file_path))
            page = doc[page_number - 1]  # 0-indexed in PyMuPDF

            # Render page at 300 DPI (zoom factor 300/72 = ~4.16) for clear OCR recognition
            zoom = 300 / 72
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img_data = pix.tobytes("png")
            doc.close()

            image = Image.open(io.BytesIO(img_data))
            processed_image = self.preprocess_image(image)

            # Perform OCR with custom configuration
            custom_config = r"--oem 3 --psm 6"  # Assume uniform block of text
            text = pytesseract.image_to_string(
                processed_image,
                lang=settings.OCR_LANGUAGE,
                config=custom_config
            ).strip()

            # Estimate confidence using image_to_data
            data = pytesseract.image_to_data(
                processed_image,
                lang=settings.OCR_LANGUAGE,
                output_type=pytesseract.Output.DICT
            )
            confs = [float(c) for c in data.get("conf", []) if float(c) > 0]
            avg_conf = (sum(confs) / len(confs)) / 100.0 if confs else 0.85

            return text, round(avg_conf, 2)

        except Exception as e:
            logger.error(f"OCR failure on page {page_number} of {file_path.name}: {str(e)}")
            return (f"[OCR Error on page {page_number}: {str(e)}]", 0.0)
