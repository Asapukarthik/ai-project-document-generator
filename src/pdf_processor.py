from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
import fitz  # PyMuPDF
from src.config import get_settings

settings = get_settings()


@dataclass
class ExtractedPage:
    """Represents a single page extracted from a PDF document."""
    page_number: int
    text: str
    char_count: int
    has_images: bool
    is_scanned_candidate: bool
    extraction_method: str = "DIGITAL"
    confidence: float = 1.0


class PDFValidationError(Exception):
    """Raised when PDF file security or integrity checks fail."""
    pass


class PDFProcessor:
    """
    Handles PDF validation and digital text extraction using PyMuPDF.
    """

    @staticmethod
    def validate_pdf_file(file_path: Path) -> None:
        """
        Validates file existence, extension, size limit, and PDF magic byte signature.
        """
        if not file_path.exists():
            raise PDFValidationError(f"File not found: {file_path.name}")

        # Check extension
        if file_path.suffix.lower() not in settings.ALLOWED_EXTENSIONS:
            raise PDFValidationError(
                f"Unsupported file extension '{file_path.suffix}'. Only .pdf files are accepted."
            )

        # Check file size limit
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
            raise PDFValidationError(
                f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB."
            )

        # Validate PDF magic header signature (%PDF-)
        with open(file_path, "rb") as f:
            header = f.read(5)
            if not header.startswith(b"%PDF-"):
                raise PDFValidationError(
                    "Invalid PDF signature. The uploaded file is not a valid PDF document or is corrupted."
                )

    @classmethod
    def extract_digital_text(cls, file_path: Path) -> Tuple[List[ExtractedPage], str]:
        """
        Extracts digital text page-by-page from a PDF using PyMuPDF.
        Classifies overall document type as DIGITAL, SCANNED, or MIXED.
        """
        cls.validate_pdf_file(file_path)

        try:
            doc = fitz.open(str(file_path))
        except Exception as e:
            raise PDFValidationError(f"Corrupted or unreadable PDF: {str(e)}")

        if doc.is_encrypted:
            doc.close()
            raise PDFValidationError("Password-protected PDFs are not supported. Please remove encryption and retry.")

        if doc.page_count == 0:
            doc.close()
            raise PDFValidationError("The uploaded PDF document contains no pages.")

        pages: List[ExtractedPage] = []
        scanned_count = 0

        for idx, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            char_count = len(text)
            images = page.get_images()
            has_images = len(images) > 0

            # Page is considered scanned if digital text is below threshold and images are present (or text is empty)
            is_scanned = (char_count < settings.MIN_DIGITAL_TEXT_CHARS) and (has_images or char_count == 0)

            if is_scanned:
                scanned_count += 1
                method = "PENDING_OCR"
            else:
                method = "DIGITAL"

            pages.append(
                ExtractedPage(
                    page_number=idx,
                    text=text,
                    char_count=char_count,
                    has_images=has_images,
                    is_scanned_candidate=is_scanned,
                    extraction_method=method,
                    confidence=1.0 if not is_scanned else 0.0
                )
            )

        doc.close()

        # Classify overall PDF type
        total = len(pages)
        if scanned_count == 0:
            pdf_type = "DIGITAL"
        elif scanned_count == total:
            pdf_type = "SCANNED"
        else:
            pdf_type = "MIXED"

        return pages, pdf_type
