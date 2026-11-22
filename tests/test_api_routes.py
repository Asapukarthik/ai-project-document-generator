from backend.main import app


def test_api_routes_mounted():
    """Verifies that all specified endpoints are properly mounted in FastAPI."""
    schema = app.openapi()
    paths = schema["paths"].keys()

    assert "/" in paths
    assert "/health" in paths
    assert "/api/documents/upload" in paths
    assert "/api/documents/{document_id}/status" in paths
    assert "/api/documents/{document_id}/result" in paths
    assert "/api/documents/{document_id}/generate" in paths
    assert "/api/documents/{document_id}/download" in paths
    assert "/api/documents" in paths


def test_openapi_schema_generated():
    """Verifies OpenAPI schema generation and document metadata."""
    schema = app.openapi()
    assert schema["info"]["title"] == app.title
    assert "/api/documents/upload" in schema["paths"]
    assert "/health" in schema["paths"]
