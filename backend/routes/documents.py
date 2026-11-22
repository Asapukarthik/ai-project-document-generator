import json
import logging
import uuid
from pathlib import Path
from typing import List
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from src.config import get_settings
from src.database import (
    create_document_record,
    get_document_record,
    list_all_documents,
    update_document_status
)
from src.pdf_processor import PDFValidationError
from src.pipeline import ExtractionPipeline
from backend.schemas.api import (
    GenerateRequest,
    GenerateResponse,
    ResultResponse,
    StatusResponse,
    UploadResponse
)

logger = logging.getLogger("docgen.api")
settings = get_settings()
router = APIRouter(prefix="/api/documents", tags=["Documents"])
pipeline = ExtractionPipeline()


def run_pipeline_task(file_path: Path, filename: str, doc_id: str):
    """Background execution task for document extraction."""
    try:
        pipeline.process_pdf(file_path, filename)
    except Exception as e:
        logger.error(f"Background task failed for document {doc_id}: {e}")


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Securely uploads and validates a PDF, then initiates processing in the background.
    """
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file extension '{ext}'. Only .pdf files are accepted."
        )

    # Read initial bytes to validate PDF magic signature
    header_bytes = await file.read(5)
    if not header_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file signature. File is not a valid PDF document."
        )

    # Read rest of file
    rest_of_bytes = await file.read()
    file_bytes = header_bytes + rest_of_bytes
    file_size = len(file_bytes)

    # Validate size limit
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB."
        )

    # Save to secure temporary location with UUID to prevent path traversal
    safe_filename = f"{uuid.uuid4().hex}.pdf"
    destination = settings.INPUT_DIR / safe_filename
    with open(destination, "wb") as f:
        f.write(file_bytes)

    # Create initial database record
    record = create_document_record(
        filename=file.filename,
        stored_path=str(destination),
        file_size=file_size
    )

    # Enqueue background pipeline task
    background_tasks.add_task(run_pipeline_task, destination, file.filename, record.document_id)

    return UploadResponse(
        document_id=record.document_id,
        original_filename=file.filename,
        file_size_bytes=file_size,
        processing_status="PENDING",
        message="PDF uploaded successfully. Extraction pipeline enqueued."
    )


@router.get("/{document_id}/status", response_model=StatusResponse)
def get_status(document_id: str):
    """Returns the current processing status of a document."""
    record = get_document_record(document_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    return StatusResponse(
        document_id=record.document_id,
        original_filename=record.original_filename,
        processing_status=record.processing_status,
        extraction_status=record.extraction_status,
        generation_status=record.generation_status,
        pdf_type=record.pdf_type,
        total_pages=record.total_pages or 0,
        error_message=record.error_message
    )


@router.get("/{document_id}/result", response_model=ResultResponse)
def get_result(document_id: str):
    """Returns the structured project data extracted from the document."""
    record = get_document_record(document_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    data = None
    if record.extracted_data_json:
        data = json.loads(record.extracted_data_json)

    return ResultResponse(
        document_id=record.document_id,
        status=record.processing_status,
        extracted_data=data
    )


@router.post("/{document_id}/generate", response_model=GenerateResponse)
def generate_docx(document_id: str, payload: GenerateRequest):
    """Generates the editable Word document from extracted or human-reviewed data."""
    record = get_document_record(document_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    try:
        pipeline.generate_docx(document_id, reviewed_data=payload.reviewed_data)
        updated = get_document_record(document_id)
        return GenerateResponse(
            document_id=document_id,
            output_filename=updated.output_filename or "",
            download_url=f"/api/documents/{document_id}/download",
            status="COMPLETED"
        )
    except Exception as e:
        logger.error(f"Word generation failed for {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Generation error: {str(e)}")


@router.get("/{document_id}/download")
def download_docx(document_id: str):
    """Streams the generated Word document (.docx) to the client."""
    record = get_document_record(document_id)
    if not record or not record.output_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generated document not found.")

    file_path = Path(record.output_path)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file missing from storage.")

    return FileResponse(
        path=file_path,
        filename=record.output_filename or f"Project_Document_{document_id[:8]}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@router.get("", response_model=List[StatusResponse])
def list_history():
    """Lists document processing history."""
    records = list_all_documents()
    return [
        StatusResponse(
            document_id=r.document_id,
            original_filename=r.original_filename,
            processing_status=r.processing_status,
            extraction_status=r.extraction_status,
            generation_status=r.generation_status,
            pdf_type=r.pdf_type,
            total_pages=r.total_pages or 0,
            error_message=r.error_message
        )
        for r in records
    ]
