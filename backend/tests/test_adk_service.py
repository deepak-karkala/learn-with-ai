"""
Tests for the ADK service implementation.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.adk_service import ADKService, ChatRequest, ChatResponse


class TestADKService:
    """Test cases for ADKService"""

    def test_init_success(self):
        """Test successful ADK service initialization"""
        with patch("app.services.adk_service.Agent") as mock_agent:
            mock_agent_instance = Mock()
            mock_agent_instance.name = "system_design_agent"
            mock_agent.return_value = mock_agent_instance

            service = ADKService()

            assert service.agent == mock_agent_instance
            assert service.app_name == "systemdesign-ai-platform"
            mock_agent.assert_called_once()

    def test_init_exception(self):
        """Test ADK service initialization with exception"""
        with patch(
            "app.services.adk_service.Agent", side_effect=Exception("Init error")
        ):
            with pytest.raises(Exception, match="Init error"):
                ADKService()

    def test_health_check_configured(self):
        """Test health check when service is properly configured"""
        with patch("app.services.adk_service.Agent") as mock_agent:
            mock_agent_instance = Mock()
            mock_agent_instance.name = "system_design_agent"
            mock_agent.return_value = mock_agent_instance

            service = ADKService()
            health = service.health_check()

            expected = {
                "configured": True,
                "agent_name": "system_design_agent",
                "model_info": {"type": "Gemini", "model": "gemini-2.0-flash-exp"},
                "architecture": "streaming",
                "session_management": "per-chat (InMemoryRunner + InMemorySessionService)",
                "app_name": "systemdesign-ai-platform",
                "status": "ready",
                "capabilities": [
                    "text_streaming",
                    "live_request_queue",
                    "bidirectional_communication",
                ],
            }
            assert health == expected

    def test_health_check_not_configured(self):
        """Test health check when agent is not initialized"""
        with patch("app.services.adk_service.Agent") as mock_agent:
            # Don't call ADKService() constructor to avoid initialization
            mock_agent_instance = Mock()
            mock_agent_instance.name = "system_design_agent"
            mock_agent.return_value = mock_agent_instance

            service = ADKService()
            service.agent = None  # Simulate failed initialization

            health = service.health_check()

            assert health["configured"] is False
            assert health["status"] == "not_configured"
            assert health["agent_name"] is None
            assert health["capabilities"] == []

    def test_health_check_exception(self):
        """Test health check with exception"""
        with patch("app.services.adk_service.Agent") as mock_agent:
            mock_agent_instance = Mock()
            mock_agent_instance.name = "system_design_agent"
            mock_agent.return_value = mock_agent_instance

            service = ADKService()
            # Make getattr fail to simulate exception in health check
            with patch("builtins.getattr", side_effect=Exception("Health check error")):
                health = service.health_check()

            assert health["configured"] is False
            assert health["status"] == "error"
            assert "error" in health

    @pytest.mark.asyncio
    async def test_chat_agent_not_initialized(self):
        """Test chat when agent is not initialized"""
        with patch("app.services.adk_service.Agent") as mock_agent:
            mock_agent_instance = Mock()
            mock_agent_instance.name = "system_design_agent"
            mock_agent.return_value = mock_agent_instance

            service = ADKService()
            service.agent = None  # Simulate failed initialization

            request = ChatRequest(message="Hello", user_id="test_user")
            response = await service.chat(request)

            assert isinstance(response, ChatResponse)
            assert not response.success
            assert response.error == "Agent not initialized"
            assert "Service not available" in response.message

    @pytest.mark.asyncio
    async def test_chat_success_with_mocked_streaming(self):
        """Test successful chat with mocked ADK streaming"""
        # Mock ADK components
        with (
            patch("app.services.adk_service.Agent") as mock_agent,
            patch("app.services.adk_service.InMemoryRunner") as mock_runner_class,
            patch("app.services.adk_service.LiveRequestQueue") as mock_queue_class,
            patch("app.services.adk_service.RunConfig"),
        ):

            # Setup agent mock
            mock_agent_instance = Mock()
            mock_agent_instance.name = "system_design_agent"
            mock_agent.return_value = mock_agent_instance

            # Setup runner and session mocks
            mock_session = Mock()
            mock_session.user_id = "test_user"
            mock_session.id = "test_user_session"

            mock_session_service = Mock()
            mock_session_service.create_session = AsyncMock(return_value=mock_session)

            mock_runner_instance = Mock()
            mock_runner_instance.session_service = mock_session_service
            mock_runner_class.return_value = mock_runner_instance

            # Setup live events mock - final event with content (no turn_complete)
            # then a turn_complete event to signal end
            mock_event1 = Mock()
            mock_event1.turn_complete = False
            mock_event1.partial = False  # Final complete response
            mock_part1 = Mock()
            mock_part1.text = "Hello! I can help you with system design."
            mock_event1.content = Mock()
            mock_event1.content.parts = [mock_part1]

            mock_event2 = Mock()
            mock_event2.turn_complete = True
            mock_event2.content = None

            async def mock_live_events():
                yield mock_event1
                yield mock_event2

            mock_runner_instance.run_live.return_value = mock_live_events()

            # Setup queue mock
            mock_queue_instance = Mock()
            mock_queue_class.return_value = mock_queue_instance

            # Test the service
            service = ADKService()
            request = ChatRequest(message="Hello", user_id="test_user")
            response = await service.chat(request)

            # Assertions
            assert isinstance(response, ChatResponse)
            assert response.success
            assert response.message == "Hello! I can help you with system design."
            assert response.session_id == "test_user_session"
            assert response.error is None

            # Verify calls
            mock_session_service.create_session.assert_called_once()
            mock_queue_instance.send_content.assert_called_once()
            mock_queue_instance.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_empty_response(self):
        """Test chat with empty response from agent"""
        with (
            patch("app.services.adk_service.Agent") as mock_agent,
            patch("app.services.adk_service.InMemoryRunner") as mock_runner_class,
            patch("app.services.adk_service.LiveRequestQueue") as mock_queue_class,
        ):

            # Setup agent mock
            mock_agent_instance = Mock()
            mock_agent_instance.name = "system_design_agent"
            mock_agent.return_value = mock_agent_instance

            # Setup runner and session mocks
            mock_session = Mock()
            mock_session.user_id = "test_user"
            mock_session.id = "test_user_session"

            mock_session_service = Mock()
            mock_session_service.create_session = AsyncMock(return_value=mock_session)

            mock_runner_instance = Mock()
            mock_runner_instance.session_service = mock_session_service
            mock_runner_class.return_value = mock_runner_instance

            # Setup empty live events
            async def mock_empty_events():
                # No events yielded
                return
                yield  # This won't be reached

            mock_runner_instance.run_live.return_value = mock_empty_events()

            # Setup queue mock
            mock_queue_instance = Mock()
            mock_queue_class.return_value = mock_queue_instance

            # Test the service
            service = ADKService()
            request = ChatRequest(message="Hello", user_id="test_user")
            response = await service.chat(request)

            # Assertions
            assert isinstance(response, ChatResponse)
            assert not response.success
            assert response.error == "Empty response from agent"
            assert "couldn't generate a response" in response.message

    @pytest.mark.asyncio
    async def test_chat_exception_handling(self):
        """Test chat exception handling"""
        with (
            patch("app.services.adk_service.Agent") as mock_agent,
            patch("app.services.adk_service.InMemoryRunner") as mock_runner_class,
        ):

            # Setup agent mock
            mock_agent_instance = Mock()
            mock_agent_instance.name = "system_design_agent"
            mock_agent.return_value = mock_agent_instance

            # Setup runner to raise exception
            mock_runner_class.side_effect = Exception("ADK Error")

            # Test the service
            service = ADKService()
            request = ChatRequest(message="Hello", user_id="test_user")
            response = await service.chat(request)

            # Assertions
            assert isinstance(response, ChatResponse)
            assert not response.success
            assert response.error == "Internal error"
            assert "technical difficulties" in response.message

    def test_get_session_info(self):
        """Test get session info functionality"""
        with patch("app.services.adk_service.Agent") as mock_agent:
            mock_agent_instance = Mock()
            mock_agent_instance.name = "system_design_agent"
            mock_agent.return_value = mock_agent_instance

            service = ADKService()
            session_info = service.get_session_info("test_user", "test_session")

            expected_keys = [
                "user_id",
                "session_id",
                "app_name",
                "service_type",
                "architecture",
                "note",
            ]
            for key in expected_keys:
                assert key in session_info

            assert session_info["user_id"] == "test_user"
            assert session_info["session_id"] == "test_session"
            assert session_info["app_name"] == "systemdesign-ai-platform"
            assert session_info["architecture"] == "streaming"
