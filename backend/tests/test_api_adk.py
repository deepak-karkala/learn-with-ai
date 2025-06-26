"""
Tests for API endpoints with ADK integration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.adk_service import ChatResponse


class TestADKAPIIntegration:
    """Test cases for API endpoints with ADK service"""

    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)

    @patch('app.main.adk_service')
    def test_api_health_endpoint(self, mock_adk_service):
        """Test API health endpoint with ADK integration"""
        # Mock ADK service health check
        mock_adk_service.health_check.return_value = {
            "configured": True,
            "agent_name": "system_design_agent",
            "status": "ready",
            "architecture": "streaming"
        }
        
        response = self.client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["services"]["adk"] == "ready"
        assert data["adk_info"]["configured"] is True
        assert data["adk_info"]["agent_name"] == "system_design_agent"

    @patch('app.main.adk_service')
    def test_api_health_endpoint_adk_not_ready(self, mock_adk_service):
        """Test API health endpoint when ADK is not ready"""
        # Mock ADK service not ready
        mock_adk_service.health_check.return_value = {
            "configured": False,
            "status": "not_configured"
        }
        
        response = self.client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"  # API is still healthy
        assert data["services"]["adk"] == "not_configured"
        assert data["adk_info"]["configured"] is False

    @patch('app.main.adk_service')
    @pytest.mark.asyncio
    async def test_chat_endpoint_success(self, mock_adk_service):
        """Test successful chat endpoint"""
        # Mock successful ADK response
        mock_response = ChatResponse(
            message="Hello! I can help you with system design interviews.",
            success=True,
            session_id="test_user_session",
            error=None
        )
        mock_adk_service.chat = AsyncMock(return_value=mock_response)
        
        chat_request = {
            "message": "Hello, can you help me with system design?",
            "user_id": "test_user",
            "session_id": "test_session"
        }
        
        response = self.client.post("/api/chat", json=chat_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["message"] == "Hello! I can help you with system design interviews."
        assert data["session_id"] == "test_user_session"
        assert data["error"] is None
        
        # Verify the service was called correctly
        mock_adk_service.chat.assert_called_once()
        call_args = mock_adk_service.chat.call_args[0][0]
        assert call_args.message == "Hello, can you help me with system design?"
        assert call_args.user_id == "test_user"
        assert call_args.session_id == "test_session"

    @patch('app.main.adk_service')
    @pytest.mark.asyncio
    async def test_chat_endpoint_adk_error(self, mock_adk_service):
        """Test chat endpoint when ADK returns error"""
        # Mock ADK error response
        mock_response = ChatResponse(
            message="I'm experiencing technical difficulties. Please try again in a moment.",
            success=False,
            session_id="test_user_session",
            error="Internal error"
        )
        mock_adk_service.chat = AsyncMock(return_value=mock_response)
        
        chat_request = {
            "message": "Hello",
            "user_id": "test_user"
        }
        
        response = self.client.post("/api/chat", json=chat_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert "technical difficulties" in data["message"]
        assert data["error"] == "Internal error"

    @patch('app.main.adk_service')
    @pytest.mark.asyncio
    async def test_chat_endpoint_exception(self, mock_adk_service):
        """Test chat endpoint with unexpected exception"""
        # Mock ADK service exception
        mock_adk_service.chat = AsyncMock(side_effect=Exception("Unexpected error"))
        
        chat_request = {
            "message": "Hello",
            "user_id": "test_user"
        }
        
        response = self.client.post("/api/chat", json=chat_request)
        
        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data["detail"]

    def test_chat_endpoint_invalid_request(self):
        """Test chat endpoint with invalid request data"""
        # Missing required message field
        invalid_request = {
            "user_id": "test_user"
            # Missing required message field
        }
        
        response = self.client.post("/api/chat", json=invalid_request)
        
        assert response.status_code == 422  # Validation error

    @patch('app.main.adk_service')
    def test_get_session_info_endpoint(self, mock_adk_service):
        """Test get session info endpoint"""
        # Mock session info response
        mock_session_info = {
            "user_id": "test_user",
            "session_id": "test_session",
            "app_name": "systemdesign-ai-platform",
            "service_type": "InMemorySessionService",
            "architecture": "streaming",
            "note": "Sessions are created per-chat in the streaming architecture"
        }
        mock_adk_service.get_session_info.return_value = mock_session_info
        
        response = self.client.get("/api/sessions/test_user/test_session")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == "test_user"
        assert data["session_id"] == "test_session"
        assert data["app_name"] == "systemdesign-ai-platform"
        assert data["architecture"] == "streaming"
        
        # Verify the service was called correctly
        mock_adk_service.get_session_info.assert_called_once_with("test_user", "test_session")

    @patch('app.main.adk_service')
    def test_get_session_info_endpoint_error(self, mock_adk_service):
        """Test get session info endpoint with error"""
        # Mock service exception
        mock_adk_service.get_session_info.side_effect = Exception("Session error")
        
        response = self.client.get("/api/sessions/test_user/test_session")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to get session info" in data["detail"]

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = self.client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "AI System Design Learning Platform API" in data["message"]

    def test_health_endpoint(self):
        """Test basic health endpoint"""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"