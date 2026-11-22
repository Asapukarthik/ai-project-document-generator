# AI-Powered Project Documentation Generator using OCR, Ollama, and LLMs

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.39%2B-FF4B4B.svg)](https://streamlit.io/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama%20(Local)-orange.svg)](https://ollama.ai/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

A production-grade, privacy-first software system that automatically extracts unstructured project specifications, Terms of Reference (ToR), Project Charters, and Software Requirements Specifications (SRS) from digital and scanned PDFs, understands requirements using local LLMs (Llama 3 / Qwen 2.5 via Ollama), enforces strict anti-hallucination validation with Pydantic, and generates professional, fully editable Microsoft Word (`.docx`) documents.

---

## 🌟 Resume & Engineering Highlights

- **Intelligent Hybrid Ingestion Pipeline**: Automatically routes pages between **PyMuPDF** (high-speed vector & text extraction) and **Tesseract OCR** (scanned document fallback with contrast and sharpening preprocessing).
- **100% Local Inference & Zero Data Leakage**: Utilizes **Ollama** running local models (`llama3.2`, `llama3.1`, or `qwen2.5`) with configurable request timeouts and retry mechanisms. No third-party cloud APIs are used.
- **Strict Anti-Hallucination & Provenance**: Guaranteed grounded output via **Pydantic** schema enforcement; missing values explicitly fallback to `"Not specified in the source document"`. Tracks page citations for extracted deliverables and milestones.
- **Human-in-the-Loop Review**: Streamlit UI provides an interactive review and editing stage before finalizing documents.
- **Corporate Document Synthesis**: Programmatically generates Microsoft Word documents using **python-docx**, featuring corporate typography, executive cover pages, styled tables with zebra striping, and stakeholder sign-off sections.
- **Decoupled Production Architecture**: Decoupled **FastAPI** backend and **Streamlit** frontend with asynchronous background tasks, SQLite metadata persistence, and Docker multi-container deployment.

---

## 🏛 Architecture Diagram

```
User PDF (Digital / Scanned)
          │
          ▼
   [ Streamlit UI ]
          │  (Multipart Upload)
          ▼
   [ FastAPI Backend ]
          │
          ▼
 ┌────────────────────────────────────────────────────────┐
 │ Extraction & Ingestion Pipeline                        │
 │ ├─ PDF Signature & Security Check (%PDF-, Size, Passwd)│
 │ ├─ PyMuPDF (Digital Text Parsing)                      │
 │ └─ Tesseract OCR (Image Preprocessing & Fallback)      │
 └────────────────────────┬───────────────────────────────┘
                          │ Page-grounded normalized text
                          ▼
 ┌────────────────────────────────────────────────────────┐
 │ Local LLM Intelligence (Ollama: Llama / Qwen)          │
 │ ├─ Grounded System Prompting & Jailbreak Defense       │
 │ ├─ Low Temperature (0.1) Deterministic Extraction      │
 │ └─ Structured JSON Output Mode                         │
 └────────────────────────┬───────────────────────────────┘
                          │
                          ▼
 ┌────────────────────────────────────────────────────────┐
 │ Pydantic Validation & Anti-Hallucination               │
 │ ├─ Project Title, Scope, Objectives, Methodology       │
 │ ├─ Milestone Timeline Table & Durations                │
 │ └─ Missing / Conflicting Information Identification   │
 └────────────────────────┬───────────────────────────────┘
                          │
                          ▼
 ┌────────────────────────────────────────────────────────┐
 │ Human-in-the-Loop Review & Approval (Streamlit UI)     │
 └────────────────────────┬───────────────────────────────┘
                          │ User Confirmed Data
                          ▼
 ┌────────────────────────────────────────────────────────┐
 │ Document Generation Engine (python-docx)               │
 │ ├─ Cover Page & Header / Footer Page Numbers           │
 │ ├─ Section Formatting & Styled Milestone Tables        │
 │ └─ Source References & Sign-off Block                  │
 └────────────────────────┬───────────────────────────────┘
                          │
         ┌────────────────┴────────────────┐
         ▼                                 ▼
[ SQLite Metadata Store ]     [ Downloadable .docx Document ]
```

---

## 📂 Project Structure

```text
AI-Powered Project Documentation Generator/
├── app.py                     # Streamlit frontend dashboard
├── backend/
│   ├── main.py                # FastAPI server entry point and lifespan
│   ├── routes/
│   │   ├── documents.py       # Upload, status, result, generate, download endpoints
│   │   └── health.py          # Service health check (DB, Ollama, Tesseract)
│   └── schemas/
│       └── api.py             # FastAPI request/response schemas
├── src/
│   ├── config.py              # Pydantic Settings and path resolution
│   ├── database.py            # SQLite database models and CRUD operations
│   ├── docx_generator.py      # Professional python-docx Word generator
│   ├── llm_extractor.py       # Ollama client with retry and error handling
│   ├── ocr_processor.py       # Tesseract OCR & image contrast enhancement
│   ├── pdf_processor.py       # PyMuPDF digital parser & security validator
│   ├── pipeline.py            # End-to-end pipeline coordinator
│   ├── prompt_templates.py    # Grounded system prompts & injection boundaries
│   ├── text_cleaner.py        # Text sanitizer preserving structure & citations
│   └── validator.py           # Pydantic schemas (ProjectDocument, Milestone, etc.)
├── tests/
│   ├── test_docx_generator.py # Word document generation tests
│   ├── test_llm_extractor.py  # Mocked Ollama extraction and error tests
│   ├── test_ocr_processor.py  # Image preprocessing & OCR mock tests
│   ├── test_pdf_processor.py  # Digital extraction & corrupted file tests
│   ├── test_pipeline.py       # End-to-end pipeline integration test
│   └── test_validator.py      # Anti-hallucination and schema fallback tests
├── input/                     # Secure upload storage
├── output/                    # Generated Word documents & SQLite database
├── Dockerfile                 # Multi-stage container with Tesseract pre-installed
├── docker-compose.yml         # Container orchestration for backend & frontend
├── requirements.txt           # Python package requirements
├── .env.example               # Environment variable configuration template
└── README.md                  # Comprehensive technical documentation
```

---

## 🛠 Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Streamlit, Pandas |
| **Backend API** | FastAPI, Uvicorn, Python-Multipart |
| **Digital PDF Parsing**| PyMuPDF (`fitz`) |
| **OCR Fallback** | Tesseract OCR, Pytesseract, Pillow |
| **Local LLM Engine** | Ollama (`llama3.2`, `llama3.1`, `qwen2.5:7b`), HTTPX |
| **Schema Validation**| Pydantic v2 |
| **Word Synthesis** | Python-docx, OpenXML |
| **Database** | SQLite, SQLAlchemy 2.0 |
| **DevOps** | Docker, Docker Compose |
| **Testing** | Pytest, Pytest-Asyncio, Unittest Mock |

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Python 3.10+** installed.
- **Ollama** installed: [Download Ollama](https://ollama.ai/)
- **Tesseract OCR** (Optional for digital PDFs, required for scanned PDFs):
  - **Windows**: [Download Tesseract Installer](https://github.com/UB-Mannheim/tesseract/wiki) (Add to PATH or set `TESSERACT_CMD` in `.env`).
  - **Linux / Ubuntu**: `sudo apt install tesseract-ocr tesseract-ocr-eng`
  - **macOS**: `brew install tesseract`

### 2. Install and Start Ollama Model
```bash
# Pull your preferred local model (3.2b is fast and lightweight)
ollama pull llama3.2

# Alternatively, pull Qwen 2.5
ollama pull qwen2.5:7b

# Ensure Ollama server is running
ollama serve
```

### 3. Clone and Setup Environment
```bash
git clone https://github.com/your-username/ai-project-document-generator.git
cd ai-project-document-generator

# Create virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### 4. Run the Application

#### Option A: Running Locally
Open two terminal windows:

**Terminal 1 (FastAPI Backend):**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Swagger UI will be available at: `http://localhost:8000/docs`

**Terminal 2 (Streamlit Frontend):**
```bash
streamlit run app.py
```
Open your browser at: `http://localhost:8501`

#### Option B: Running with Docker Compose
```bash
docker-compose up --build
```
- Streamlit UI: `http://localhost:8501`
- FastAPI Docs: `http://localhost:8000/docs`

---

## 🧪 Running the Automated Test Suite

The test suite includes unit and integration tests with mocked LLM calls:
```bash
pytest tests/ -v
```

Expected output:
```text
tests/test_docx_generator.py::test_docx_generation PASSED
tests/test_llm_extractor.py::test_clean_json_response_strip_markdown PASSED
tests/test_llm_extractor.py::test_clean_json_response_strip_preamble PASSED
tests/test_llm_extractor.py::test_ollama_mock_successful_extraction PASSED
tests/test_llm_extractor.py::test_ollama_mock_connection_error PASSED
tests/test_ocr_processor.py::test_image_preprocessing PASSED
tests/test_ocr_processor.py::test_ocr_processor_graceful_missing_binary PASSED
tests/test_ocr_processor.py::test_ocr_processor_with_mock PASSED
tests/test_pdf_processor.py::test_digital_pdf_extraction PASSED
tests/test_pdf_processor.py::test_corrupted_pdf_rejection PASSED
tests/test_pdf_processor.py::test_empty_pdf_rejection PASSED
tests/test_pdf_processor.py::test_nonexistent_file_rejection PASSED
tests/test_pipeline.py::test_full_pipeline_mocked_llm PASSED
tests/test_validator.py::test_validator_with_full_data PASSED
tests/test_validator.py::test_validator_missing_fields_anti_hallucination_fallbacks PASSED
tests/test_validator.py::test_validator_invalid_type_rejection PASSED
```

---

## 🔒 Security & Privacy Controls

- **Magic Byte Validation**: Uploads are validated by reading initial bytes to ensure they strictly start with `%PDF-`, blocking extension-spoofing attacks.
- **Path Traversal Protection**: Uploaded files are renamed using UUIDs before writing to disk; the user-supplied filename is never used as a filesystem path.
- **Prompt Injection Defense**: Untrusted PDF content is demarcated within explicit tags (`=== BEGIN UNTRUSTED DOCUMENT TEXT ===`) and the system prompt explicitly commands the LLM to ignore embedded execution instructions.
- **No Sensitive Leakage**: Internal server paths and stack traces are suppressed in API responses.
- **Local Sovereignty**: All LLM processing runs entirely on the host via Ollama, preventing confidential project documents from leaving the network.

---

## 📄 License
This project is licensed under the MIT License.
