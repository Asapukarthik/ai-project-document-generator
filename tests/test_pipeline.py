import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import fitz
from src.pipeline import ExtractionPipeline
from src.database import get_document_record
from src.validator import ProjectDocument, MethodologyStep, TimelineMilestone


def test_full_pipeline_mocked_llm(tmp_path):
    """
    End-to-end integration test:
    Creates synthetic PDF -> Runs Pipeline -> Checks DB status -> Generates DOCX.
    """
    # 1. Create a synthetic test PDF
    pdf_path = tmp_path / "test_tor.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "TERMS OF REFERENCE\nProject: Smart Grid IoT Infrastructure\nScope: Deploy 500 smart sensors across substation network.")
    doc.save(str(pdf_path))
    doc.close()

    # 2. Mock Ollama extraction
    mocked_project_doc = ProjectDocument(
        project_title="Smart Grid IoT Infrastructure",
        scope_of_work="Deploy 500 smart sensors across substation network with encrypted mesh communication.",
        objectives=["Sub-second telemetry latency", "Tamper-evident sensor hardware"],
        methodology=[
            MethodologyStep(
                step_number=1,
                title="Sensor Installation",
                description="Install gateways on distribution poles.",
                source_page="Page 1"
            )
        ],
        project_timeline=[
            TimelineMilestone(
                milestone="Sensor Deployment",
                description="Initial 100 sensors deployed",
                start_date="Q1 2025",
                end_date="Q2 2025",
                duration="3 months",
                source_page="Page 1"
            )
        ],
        source_references=["Page 1"],
        missing_information=["Cellular backhaul carrier unstated"],
        conflicting_information=[]
    )

    with patch("src.llm_extractor.OllamaExtractor.extract_project_info", return_value=mocked_project_doc):
        pipeline = ExtractionPipeline()
        result = pipeline.process_pdf(pdf_path, "test_tor.pdf")

        assert result["status"] == "READY_FOR_REVIEW"
        assert result["extracted_data"]["project_title"] == "Smart Grid IoT Infrastructure"

        doc_id = result["document_id"]
        record = get_document_record(doc_id)
        assert record is not None
        assert record.processing_status == "READY_FOR_REVIEW"
        assert record.pdf_type == "DIGITAL"

        # 3. Test Word Document Generation
        docx_path = pipeline.generate_docx(doc_id)
        assert docx_path.exists()
        assert docx_path.stat().st_size > 0

        updated_record = get_document_record(doc_id)
        assert updated_record.processing_status == "COMPLETED"
        assert updated_record.output_filename.endswith(".docx")
