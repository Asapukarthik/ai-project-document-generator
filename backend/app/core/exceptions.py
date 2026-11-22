from typing import Any, Dict, Optional


class AppException(Exception):
    """Base exception class for all domain errors within the application."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ExtractionError(AppException):
    """Raised when text extraction from a digital PDF fails."""
    pass


class OCRError(ExtractionError):
    """Raised when scanned image OCR processing fails."""
    pass


class LLMConnectionError(AppException):
    """Raised when the Ollama service cannot be reached."""
    pass


class LLMInferenceError(AppException):
    """Raised when the Ollama inference fails or produces invalid responses."""
    pass


class SchemaValidationError(AppException):
    """Raised when LLM output violates the required Pydantic structured schema."""
    pass


class DocumentGenerationError(AppException):
    """Raised when python-docx fails to generate the Word document."""
    pass


class DocumentNotFoundError(AppException):
    """Raised when a requested document ID does not exist in the database."""
    pass
