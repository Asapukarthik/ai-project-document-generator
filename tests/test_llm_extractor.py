import json
import pytest
from unittest.mock import patch, MagicMock
from src.llm_extractor import OllamaExtractor, LLMInferenceError
from src.validator import ProjectDocument


def test_clean_json_response_strip_markdown():
    """Tests stripping of markdown code blocks from LLM output."""
    raw = "```json\n{\"project_title\": \"Enterprise Core System\"}\n```"
    cleaned = OllamaExtractor._clean_json_response(raw)
    assert cleaned == "{\"project_title\": \"Enterprise Core System\"}"


def test_clean_json_response_strip_preamble():
    """Tests extraction of JSON enclosed within conversational text."""
    raw = "Sure! Here is the JSON you requested:\n{\"project_title\": \"AI System\"}\nHope this helps!"
    cleaned = OllamaExtractor._clean_json_response(raw)
    assert cleaned == "{\"project_title\": \"AI System\"}"


@patch("httpx.Client.post")
def test_ollama_mock_successful_extraction(mock_post):
    """Tests end-to-end Ollama response parsing and Pydantic validation."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_payload = {
        "project_title": "Cloud Migration Initiative",
        "scope_of_work": "Migrate on-premise infrastructure to Kubernetes.",
        "objectives": ["Reduce latency by 30%", "Ensure 99.99% uptime"],
        "methodology": [
            {
                "step_number": 1,
                "title": "Discovery Phase",
                "description": "Catalog dependencies and microservices.",
                "source_page": "Page 1"
            }
        ],
        "project_timeline": [
            {
                "milestone": "Phase 1 Assessment",
                "description": "Architecture blueprint approved",
                "start_date": "Jan 2025",
                "end_date": "Feb 2025",
                "duration": "1 month",
                "source_page": "Page 2"
            }
        ],
        "source_references": ["Page 1, Paragraph 2"],
        "missing_information": ["Total infrastructure budget not mentioned"],
        "conflicting_information": []
    }
    mock_response.json.return_value = {"response": json.dumps(mock_payload)}
    mock_post.return_value = mock_response

    extractor = OllamaExtractor()
    result = extractor.extract_project_info("Sample Document Text")

    assert isinstance(result, ProjectDocument)
    assert result.project_title == "Cloud Migration Initiative"
    assert len(result.objectives) == 2
    assert result.methodology[0].title == "Discovery Phase"
    assert result.project_timeline[0].milestone == "Phase 1 Assessment"
    assert "budget" in result.missing_information[0]


@patch("httpx.Client.post")
def test_ollama_mock_connection_error(mock_post):
    """Tests error handling when Ollama server cannot be reached."""
    import httpx
    mock_post.side_effect = httpx.ConnectError("Connection refused")

    extractor = OllamaExtractor()
    with pytest.raises(LLMInferenceError, match="Connection refused"):
        extractor.extract_project_info("Sample Text")
