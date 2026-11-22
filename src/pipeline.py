import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from src.config import get_settings
from src.database import (
    create_document_record,
    get_document_record,
    update_document_status,
    save_extracted_data,
    save_generation_result
)
from src.pdf_processor import PDFProcessor, ExtractedPage
from src.ocr_processor import OCRProcessor
from src.text_cleaner import TextCleaner
from src.llm_extractor import OllamaExtractor
from src.validator import validate_project_data, ProjectDocument
from src.docx_generator import DocxGenerator

logger = logging.getLogger("docgen.pipeline")
settings = get_settings()


class ExtractionPipeline:
    """
    Orchestrates the entire document ingestion, extraction, grounding,
    and Word document generation pipeline.
    """

    def __init__(self):
        self.ocr_processor = OCRProcessor()
        self.llm_extractor = OllamaExtractor()

    def process_pdf(self, file_path: Path, original_filename: str) -> Dict[str, Any]:
        """
        Executes stages:
        1. Validation & Record creation
        2. Digital text extraction (PyMuPDF)
        3. OCR fallback for scanned pages (Tesseract)
        4. Text cleaning and page structuring
        5. Grounded extraction with Ollama
        6. Pydantic schema validation
        7. Database persistence
        """
        file_size = file_path.stat().st_size
        record = create_document_record(
            filename=original_filename,
            stored_path=str(file_path),
            file_size=file_size
        )
        doc_id = record.document_id

        try:
            # Stage 1: Digital Extraction
            update_document_status(doc_id, processing_status="EXTRACTING")
            pages, pdf_type = PDFProcessor.extract_digital_text(file_path)
            total_pages = len(pages)
            update_document_status(doc_id, pdf_type=pdf_type, total_pages=total_pages)

            # Stage 2: OCR Fallback for scanned pages
            for page in pages:
                if page.is_scanned_candidate:
                    ocr_text, conf = self.ocr_processor.extract_page_ocr(file_path, page.page_number)
                    page.text = ocr_text
                    page.extraction_method = "OCR"
                    page.confidence = conf

            # Stage 3: Text Normalization & Page Grounding
            cleaned_doc_text = TextCleaner.format_document_with_page_citations(pages)

            # Stage 4: Local LLM Extraction with Ollama
            update_document_status(doc_id, processing_status="ANALYZING")
            project_doc: ProjectDocument = self.llm_extractor.extract_project_info(cleaned_doc_text)

            # Stage 5: Save Structured Data
            update_document_status(doc_id, processing_status="VALIDATING")
            doc_dict = project_doc.model_dump()
            save_extracted_data(doc_id, doc_dict)
            update_document_status(doc_id, processing_status="READY_FOR_REVIEW")

            return {
                "document_id": doc_id,
                "status": "READY_FOR_REVIEW",
                "pdf_type": pdf_type,
                "total_pages": total_pages,
                "extracted_data": doc_dict
            }

        except Exception as e:
            logger.error(f"Pipeline failure on {original_filename}: {str(e)}", exc_info=True)
            update_document_status(
                doc_id,
                processing_status="FAILED",
                extraction_status="FAILED",
                error_message=str(e)
            )
            raise e

    def generate_docx(self, document_id: str, reviewed_data: Optional[Dict[str, Any]] = None) -> Path:
        """
        Generates Word document from validated or human-reviewed data.
        """
        record = get_document_record(document_id)
        if not record:
            raise ValueError(f"Document ID '{document_id}' not found.")

        update_document_status(document_id, processing_status="GENERATING")

        # Use reviewed data if provided, else fall back to stored extracted data
        if reviewed_data:
            project_doc = validate_project_data(reviewed_data)
        elif record.extracted_data_json:
            import json
            stored_dict = json.loads(record.extracted_data_json)
            project_doc = validate_project_data(stored_dict)
        else:
            raise ValueError("No extracted data available to generate document.")

        # Build Word Document
        safe_name = f"Project_Doc_{document_id[:8]}.docx"
        output_file = settings.OUTPUT_DIR / safe_name

        builder = DocxGenerator(project_doc)
        generated_path = builder.generate(output_file)

        save_generation_result(document_id, str(generated_path), safe_name)
        return generated_path
