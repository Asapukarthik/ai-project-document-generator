import pytest
from src.validator import (
    MethodologyStep,
    ProjectDocument,
    TimelineMilestone,
    validate_project_data
)


def test_validator_with_full_data():
    """Verifies validation with complete and compliant project data."""
    raw = {
        "project_title": "Enterprise Data Warehouse",
        "scope_of_work": "Ingest and process 10 TB of daily telemetry.",
        "objectives": ["Standardize schema", "Enable real-time reporting"],
        "methodology": [
            {
                "step_number": 1,
                "title": "Ingestion Setup",
                "description": "Deploy Kafka brokers.",
                "source_page": "Page 3"
            }
        ],
        "project_timeline": [
            {
                "milestone": "MVP Release",
                "description": "Telemetry pipeline functional",
                "start_date": "2025-01-01",
                "end_date": "2025-03-31",
                "duration": "3 months",
                "source_page": "Page 5"
            }
        ],
        "source_references": ["Page 3", "Page 5"],
        "missing_information": [],
        "conflicting_information": []
    }
    doc = validate_project_data(raw)
    assert doc.project_title == "Enterprise Data Warehouse"
    assert len(doc.objectives) == 2
    assert len(doc.methodology) == 1
    assert len(doc.project_timeline) == 1


def test_validator_missing_fields_anti_hallucination_fallbacks():
    """Verifies that missing sections fallback to standardized non-hallucinatory placeholders."""
    raw = {
        "project_title": "   ",  # Blank title
        "scope_of_work": "Basic project scope."
        # Missing objectives, methodology, timeline
    }
    doc = validate_project_data(raw)
    # Title fallback
    assert "Title Not Specified in Source Document" in doc.project_title
    # Objectives fallback
    assert doc.objectives == ["Not specified in the source document"]
    # Methodology fallback
    assert len(doc.methodology) == 1
    assert doc.methodology[0].description == "Methodology was not specified in the source document."
    # Timeline fallback
    assert len(doc.project_timeline) == 1
    assert doc.project_timeline[0].description == "Timeline schedule was not specified in the source document."


def test_validator_invalid_type_rejection():
    """Verifies that non-dict payloads raise ValueError."""
    with pytest.raises(ValueError, match="must be a JSON object"):
        validate_project_data(["not", "a", "dict"])
