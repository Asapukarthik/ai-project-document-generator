from pathlib import Path
from docx import Document
from src.docx_generator import DocxGenerator
from src.validator import (
    MethodologyStep,
    ProjectDocument,
    TimelineMilestone
)


def test_docx_generation(tmp_path):
    """Verifies generation and structural integrity of Microsoft Word document."""
    doc_data = ProjectDocument(
        project_title="Automated Inspection Drone System",
        scope_of_work="Design and fabricate autonomous inspection drones for utility infrastructure.",
        objectives=[
            "Achieve autonomous flight range of 15 km",
            "Thermal anomaly detection accuracy above 95%"
        ],
        methodology=[
            MethodologyStep(
                step_number=1,
                title="Hardware Prototyping",
                description="Assemble airframe, sensor payload, and telemetry transmitter.",
                source_page="Page 4"
            ),
            MethodologyStep(
                step_number=2,
                title="Flight Control Testing",
                description="Calibrate optical flow and GPS waypoint navigation.",
                source_page="Page 6"
            )
        ],
        project_timeline=[
            TimelineMilestone(
                milestone="Design Review",
                description="Engineering CAD models signed off",
                start_date="Month 1",
                end_date="Month 2",
                duration="2 months",
                source_page="Page 2"
            ),
            TimelineMilestone(
                milestone="Field Trial",
                description="Live trial in simulated environment",
                start_date="Month 3",
                end_date="Month 4",
                duration="1 month",
                source_page="Page 5"
            )
        ],
        source_references=["Page 2, Section 1", "Page 4, Table 2"],
        missing_information=["Battery supplier not finalized", "Insurance underwriting criteria missing"],
        conflicting_information=[]
    )

    output_file = tmp_path / "Drone_Specification.docx"
    generator = DocxGenerator(doc_data)
    result_path = generator.generate(output_file)

    assert result_path.exists()
    assert result_path.stat().st_size > 0

    # Read back document with python-docx to verify content
    doc_read = Document(str(result_path))
    doc_text = " ".join([p.text for p in doc_read.paragraphs])

    assert "Automated Inspection Drone System" in doc_text
    assert "Achieve autonomous flight range of 15 km" in doc_text
    assert "Hardware Prototyping" in doc_text
    assert len(doc_read.tables) >= 2  # Metadata table + Timeline table
