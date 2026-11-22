from pathlib import Path
from unittest.mock import MagicMock, patch
import fitz  # PyMuPDF
import pytest
from src.pdf_processor import PDFProcessor, PDFValidationError


@pytest.fixture
def sample_digital_pdf(tmp_path) -> Path:
    """Generates a valid digital PDF with known text."""
    pdf_path = tmp_path / "sample_digital.pdf"
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text((50, 50), "PROJECT SPECIFICATION\nTitle: Autonomous Analytics Platform\nScope: Build enterprise data pipeline.")
    page2 = doc.new_page()
    page2.insert_text((50, 50), "Timeline: Phase 1 starts Jan 2025. Deliverable due in 3 months.")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def empty_pdf(tmp_path) -> Path:
    """Generates a dummy 1-page PDF for page_count mocking."""
    pdf_path = tmp_path / "empty.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def corrupted_file(tmp_path) -> Path:
    """Generates a file with .pdf extension but invalid header bytes."""
    corrupted_path = tmp_path / "corrupted.pdf"
    with open(corrupted_path, "wb") as f:
        f.write(b"NOT_A_REAL_PDF_HEADER_123456789")
    return corrupted_path


def test_digital_pdf_extraction(sample_digital_pdf):
    """Verifies PyMuPDF page-by-page digital extraction."""
    pages, pdf_type = PDFProcessor.extract_digital_text(sample_digital_pdf)
    assert pdf_type == "DIGITAL"
    assert len(pages) == 2
    assert "Autonomous Analytics Platform" in pages[0].text
    assert "Timeline: Phase 1" in pages[1].text
    assert pages[0].char_count > 0


def test_corrupted_pdf_rejection(corrupted_file):
    """Verifies that non-PDF headers are rejected with PDFValidationError."""
    with pytest.raises(PDFValidationError, match="Invalid PDF signature"):
        PDFProcessor.validate_pdf_file(corrupted_file)


def test_empty_pdf_rejection(empty_pdf):
    """Verifies that zero-page PDFs raise a meaningful validation error."""
    with patch("fitz.open") as mock_open:
        mock_doc = MagicMock()
        mock_doc.is_encrypted = False
        mock_doc.page_count = 0
        mock_open.return_value = mock_doc

        with pytest.raises(PDFValidationError, match="contains no pages"):
            PDFProcessor.extract_digital_text(empty_pdf)


def test_nonexistent_file_rejection(tmp_path):
    """Verifies error handling when file path does not exist."""
    fake_path = tmp_path / "nonexistent.pdf"
    with pytest.raises(PDFValidationError, match="File not found"):
        PDFProcessor.validate_pdf_file(fake_path)
