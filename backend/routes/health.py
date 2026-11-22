import os
from fastapi import APIRouter
from sqlalchemy import text
from src.config import get_settings
from src.llm_extractor import OllamaExtractor
from src.database import get_db_session
from backend.schemas.api import HealthResponse

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
def check_health():
    """
    Checks operational status of Database, Ollama LLM, and Tesseract OCR.
    """
    # 1. Check Database
    db_status = "healthy"
    try:
        session = get_db_session()
        session.execute(text("SELECT 1"))
        session.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # 2. Check Ollama
    ollama_client = OllamaExtractor()
    ollama_info = ollama_client.check_health()

    # 3. Check Tesseract
    tesseract_path = settings.resolve_tesseract_path()
    tesseract_info = {
        "installed": tesseract_path is not None,
        "path": tesseract_path if tesseract_path else "Not found in PATH or standard directories",
        "ocr_language": settings.OCR_LANGUAGE
    }

    overall_status = "healthy" if db_status == "healthy" and ollama_info.get("status") in ["healthy", "ready"] else "degraded"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        ollama=ollama_info,
        tesseract=tesseract_info
    )
