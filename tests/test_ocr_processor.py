from unittest.mock import MagicMock, patch
from PIL import Image
from src.ocr_processor import OCRProcessor


def test_image_preprocessing():
    """Verifies OCR image contrast enhancement and grayscale conversion."""
    # Create sample RGB image
    img = Image.new("RGB", (200, 100), color=(240, 240, 240))
    processed = OCRProcessor.preprocess_image(img)
    # Ensure converted to grayscale mode L
    assert processed.mode == "L"
    assert processed.size == (200, 100)


def test_ocr_processor_graceful_missing_binary(tmp_path):
    """Verifies graceful handling when Tesseract binary is not installed."""
    processor = OCRProcessor()
    processor.tesseract_available = False

    fake_pdf = tmp_path / "test.pdf"
    text, conf = processor.extract_page_ocr(fake_pdf, 1)
    assert "OCR Skipped" in text
    assert conf == 0.0


@patch("pytesseract.image_to_string")
@patch("pytesseract.image_to_data")
def test_ocr_processor_with_mock(mock_data, mock_string, tmp_path):
    """Verifies Tesseract image-to-string execution when binary is available."""
    processor = OCRProcessor()
    processor.tesseract_available = True

    mock_string.return_value = "Extracted Scanned Text via OCR"
    mock_data.return_value = {"conf": ["90", "95", "92"]}

    # Create dummy single page PDF
    import fitz
    pdf_path = tmp_path / "ocr_test.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(pdf_path))
    doc.close()

    text, conf = processor.extract_page_ocr(pdf_path, 1)
    assert text == "Extracted Scanned Text via OCR"
    assert conf > 0.8
