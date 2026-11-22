from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration managed through Pydantic Settings.
    Loads values from environment variables or a .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General App Config
    PROJECT_NAME: str = "AI-Powered Project Documentation Generator"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    STORAGE_DIR: Path = Field(default=Path("./storage"))

    # Database
    DATABASE_URL: str = "sqlite:///./storage/app.db"

    # Ollama LLM Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    OLLAMA_TIMEOUT: int = 120  # seconds

    # Tesseract OCR Settings
    TESSERACT_CMD: Optional[str] = None

    # File Upload Constraints
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [".pdf"]

    # Frontend connection URL
    BACKEND_API_URL: str = "http://localhost:8000"

    @property
    def UPLOAD_DIR(self) -> Path:
        """Directory for uploaded PDF files."""
        path = self.STORAGE_DIR / "uploads"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def OUTPUT_DIR(self) -> Path:
        """Directory for generated .docx documents."""
        path = self.STORAGE_DIR / "outputs"
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache()
def get_settings() -> Settings:
    """
    Provides a cached singleton instance of application settings.
    """
    settings = Settings()
    # Ensure root storage directories exist
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return settings
