import os
import shutil
from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Unified Application Configuration.
    Supports environment variables and .env file loading.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General App Config
    PROJECT_NAME: str = "AI-Powered Project Documentation Generator using OCR, Ollama and Large Language Models"
    API_V1_STR: str = "/api"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    INPUT_DIR: Path = Field(default=Path("./input"))
    OUTPUT_DIR: Path = Field(default=Path("./output"))

    # Database
    DATABASE_URL: str = "sqlite:///./output/app.db"

    # Ollama LLM Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TIMEOUT: int = 120  # seconds

    # Tesseract OCR Settings
    TESSERACT_CMD: Optional[str] = None
    OCR_LANGUAGE: str = "eng"
    MIN_DIGITAL_TEXT_CHARS: int = 50  # Below this threshold, a page is considered scanned

    # Security & Upload Constraints
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [".pdf"]
    ALLOWED_MIME_TYPES: List[str] = ["application/pdf", "application/x-pdf"]

    # Frontend connection URL
    BACKEND_API_URL: str = "http://localhost:8000"

    def setup_directories(self) -> None:
        """Ensure input and output directories exist."""
        self.INPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    def resolve_tesseract_path(self) -> Optional[str]:
        """Find the Tesseract executable path across Windows and Linux."""
        if self.TESSERACT_CMD and Path(self.TESSERACT_CMD).is_file():
            return self.TESSERACT_CMD

        # Common Windows install paths
        windows_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe"
        ]
        for p in windows_paths:
            if Path(p).is_file():
                return str(p)

        # Standard PATH lookup
        found = shutil.which("tesseract")
        return found


@lru_cache()
def get_settings() -> Settings:
    """Provides a singleton instance of application settings."""
    settings = Settings()
    settings.setup_directories()
    return settings
