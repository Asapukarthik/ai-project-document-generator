from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from src.validator import ProjectDocument


class UploadResponse(BaseModel):
    document_id: str
    original_filename: str
    file_size_bytes: int
    processing_status: str
    message: str


class StatusResponse(BaseModel):
    document_id: str
    original_filename: str
    processing_status: str
    extraction_status: str
    generation_status: str
    pdf_type: Optional[str] = None
    total_pages: Optional[int] = 0
    error_message: Optional[str] = None


class ResultResponse(BaseModel):
    document_id: str
    status: str
    extracted_data: Optional[Dict[str, Any]] = None


class GenerateRequest(BaseModel):
    reviewed_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional human-reviewed and edited project data"
    )


class GenerateResponse(BaseModel):
    document_id: str
    output_filename: str
    download_url: str
    status: str


class HealthResponse(BaseModel):
    status: str
    database: str
    ollama: Dict[str, Any]
    tesseract: Dict[str, Any]
