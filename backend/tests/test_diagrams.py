import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from app.main import app, lifespan
from app.services.diagram_service import DiagramService
from app.services.adk_service import ADKService
from app.services.whiteboard_service import WhiteboardService
from app.models.diagram import DiagramGenerationResponse
from app.models.whiteboard import PNGUploadResponse

@pytest.fixture
def mock_adk_service():
    service = AsyncMock(spec=ADKService)
    service.generate_mermaid_code.return_value = ("graph TD; A-->B;", "mock_model", 10, 0.001)
    return service

@pytest.fixture
def mock_whiteboard_service():
    service = AsyncMock(spec=WhiteboardService)
    service.upload_png.return_value = PNGUploadResponse(
        artifact_id="mock_png_artifact_id",
        file_size=1234,
        status="success",
        user_id="test_user",
        message="Upload successful",
        created_at="2025-01-01T12:00:00Z",
    )
    return service

@pytest.fixture
def test_client(mock_adk_service, mock_whiteboard_service):
    app.state.adk_service = mock_adk_service
    app.state.whiteboard_service = mock_whiteboard_service
    app.state.diagram_service = DiagramService(mock_adk_service, mock_whiteboard_service)
    
    from app.api.diagrams import get_diagram_service
    app.dependency_overrides[get_diagram_service] = lambda: app.state.diagram_service

    client = TestClient(app)
    yield client
    
    # Clean up
    app.dependency_overrides.clear()


def test_generate_diagram_success(test_client):
    """Test successful diagram generation with mock PNG fallback."""
    response = test_client.post(
        "/api/diagrams/generate",
        json={
            "system_description": "a test system",
            "diagram_type": "architecture",
            "user_id": "test_user",
        },
    )

    assert response.status_code == 200
    data = DiagramGenerationResponse(**response.json())
    assert data.status == "success"
    assert data.mermaid_code == "graph TD; A-->B;"
    assert data.png_artifact_id == "mock_png_artifact_id"
    assert data.model_used == "mock_model"

@patch.object(DiagramService, 'initialize_mcp')
def test_generate_diagram_mcp_initialization_fails(mock_init_mcp, test_client):
    """Test diagram generation when MCP initialization fails - should fall back to mock."""
    # Simulate MCP initialization failure
    mock_init_mcp.side_effect = Exception("MCP initialization failed")

    response = test_client.post(
        "/api/diagrams/generate",
        json={
            "system_description": "a test system",
            "diagram_type": "architecture",
            "user_id": "test_user",
        },
    )

    # Should still succeed with mock PNG fallback
    assert response.status_code == 200
    data = DiagramGenerationResponse(**response.json())
    assert data.status == "success"
    assert data.mermaid_code == "graph TD; A-->B;"
    assert data.png_artifact_id == "mock_png_artifact_id"
