import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from src.config import get_settings

settings = get_settings()

Base = declarative_base()


class DocumentRecord(Base):
    """
    SQLAlchemy ORM model storing document processing lifecycle metadata.
    """
    __tablename__ = "document_records"

    document_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename = Column(String(255), nullable=False)
    safe_stored_path = Column(String(512), nullable=False)
    upload_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    file_size_bytes = Column(Integer, default=0)

    # Extraction characteristics
    pdf_type = Column(String(50), default="UNKNOWN")  # DIGITAL, SCANNED, MIXED
    total_pages = Column(Integer, default=0)

    # Lifecycle statuses
    processing_status = Column(String(50), default="PENDING")  # PENDING, EXTRACTING, ANALYZING, VALIDATING, GENERATING, COMPLETED, FAILED
    extraction_status = Column(String(50), default="PENDING")  # PENDING, SUCCESS, FAILED
    generation_status = Column(String(50), default="PENDING")  # PENDING, SUCCESS, FAILED

    # Output artifact
    output_filename = Column(String(255), nullable=True)
    output_path = Column(String(512), nullable=True)

    # Grounded structured data (JSON string)
    extracted_data_json = Column(Text, nullable=True)

    # Diagnostics
    error_message = Column(Text, nullable=True)


# Database engine and session factory
# connect_args={"check_same_thread": False} allows multi-threaded access for SQLite in FastAPI
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initializes tables in the SQLite database."""
    Base.metadata.create_all(bind=engine)


def get_db_session() -> Session:
    """Yields a database session instance."""
    db = SessionLocal()
    try:
        return db
    finally:
        pass


def create_document_record(
    filename: str,
    stored_path: str,
    file_size: int
) -> DocumentRecord:
    """Creates a new document record in the database."""
    init_db()
    db = SessionLocal()
    try:
        record = DocumentRecord(
            document_id=str(uuid.uuid4()),
            original_filename=filename,
            safe_stored_path=str(stored_path),
            file_size_bytes=file_size,
            processing_status="PENDING",
            extraction_status="PENDING",
            generation_status="PENDING"
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    finally:
        db.close()


def get_document_record(document_id: str) -> Optional[DocumentRecord]:
    """Retrieves a document record by ID."""
    db = SessionLocal()
    try:
        return db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
    finally:
        db.close()


def update_document_status(
    document_id: str,
    processing_status: Optional[str] = None,
    extraction_status: Optional[str] = None,
    generation_status: Optional[str] = None,
    pdf_type: Optional[str] = None,
    total_pages: Optional[int] = None,
    error_message: Optional[str] = None
) -> Optional[DocumentRecord]:
    """Updates status indicators for a document record."""
    db = SessionLocal()
    try:
        record = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
        if not record:
            return None

        if processing_status:
            record.processing_status = processing_status
        if extraction_status:
            record.extraction_status = extraction_status
        if generation_status:
            record.generation_status = generation_status
        if pdf_type:
            record.pdf_type = pdf_type
        if total_pages is not None:
            record.total_pages = total_pages
        if error_message is not None:
            record.error_message = error_message

        db.commit()
        db.refresh(record)
        return record
    finally:
        db.close()


def save_extracted_data(document_id: str, data: Dict[str, Any]) -> Optional[DocumentRecord]:
    """Persists extracted structured JSON data."""
    db = SessionLocal()
    try:
        record = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
        if record:
            record.extracted_data_json = json.dumps(data)
            record.extraction_status = "SUCCESS"
            db.commit()
            db.refresh(record)
        return record
    finally:
        db.close()


def save_generation_result(document_id: str, output_path: str, output_filename: str) -> Optional[DocumentRecord]:
    """Persists generated Word document file paths."""
    db = SessionLocal()
    try:
        record = db.query(DocumentRecord).filter(DocumentRecord.document_id == document_id).first()
        if record:
            record.output_path = str(output_path)
            record.output_filename = output_filename
            record.generation_status = "SUCCESS"
            record.processing_status = "COMPLETED"
            db.commit()
            db.refresh(record)
        return record
    finally:
        db.close()


def list_all_documents() -> List[DocumentRecord]:
    """Retrieves all document history sorted newest first."""
    init_db()
    db = SessionLocal()
    try:
        return db.query(DocumentRecord).order_by(DocumentRecord.upload_timestamp.desc()).all()
    finally:
        db.close()
