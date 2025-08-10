"""
Tests for the ADK service implementation.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.services.adk_service import (
    ADKService, 
    ChatRequest, 
    ChatResponse,
    SessionCreateRequest,
    SessionCreateResponse
)


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
            # Session ID should now include timestamp for proper session management
            assert response.session_id.startswith("test_user_session_")
            assert len(response.session_id) > len("test_user_session_")
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

    @pytest.mark.asyncio
    async def test_create_session_success(self):
        """Test successful session creation"""
        with patch("app.services.adk_service.Agent") as mock_agent, patch(
            "app.services.adk_service.InMemoryRunner"
        ) as mock_runner_class:
            
            # Setup agent mock
            mock_agent_instance = Mock()
            mock_agent_instance.name = "system_design_agent"
            mock_agent.return_value = mock_agent_instance

            # Setup runner and session mocks
            mock_session = Mock()
            mock_session.user_id = "test_user"
            mock_session.id = "test_user_session_123456789"

            mock_session_service = Mock()
            mock_session_service.create_session = AsyncMock(return_value=mock_session)

            mock_runner_instance = Mock()
            mock_runner_instance.session_service = mock_session_service
            mock_runner_class.return_value = mock_runner_instance

            # Test the service
            service = ADKService()
            request = SessionCreateRequest(
                user_id="test_user",
                initial_state={"skill_level": "advanced"}
            )
            response = await service.create_session(request)

            # Assertions
            assert isinstance(response, SessionCreateResponse)
            assert response.success is True
            assert response.user_id == "test_user"
            assert "test_user_session_" in response.session_id
            assert response.state["skill_level"] == "advanced"
            assert "preferences" in response.state
            assert response.error is None

    @pytest.mark.asyncio
    async def test_create_session_failure(self):
        """Test session creation failure"""
        with patch("app.services.adk_service.Agent") as mock_agent, patch(
            "app.services.adk_service.InMemoryRunner"
        ) as mock_runner_class:
            
            # Setup agent mock
            mock_agent_instance = Mock()
            mock_agent_instance.name = "system_design_agent"
            mock_agent.return_value = mock_agent_instance

            # Setup runner to raise exception
            mock_runner_class.side_effect = Exception("Session creation error")

            # Test the service
            service = ADKService()
            request = SessionCreateRequest(user_id="test_user")
            response = await service.create_session(request)

            # Assertions
            assert isinstance(response, SessionCreateResponse)
            assert response.success is False
            assert response.user_id == "test_user"
            assert response.session_id == ""
            assert response.state == {}
            assert "Session creation error" in response.error

    def test_get_user_sessions(self):
        """Test getting user sessions"""
        with patch("app.services.adk_service.Agent") as mock_agent:
            mock_agent_instance = Mock()
            mock_agent_instance.name = "system_design_agent"
            mock_agent.return_value = mock_agent_instance

            service = ADKService()
            
            # Simulate some session data
            test_session_id = "test_user_session_123"
            service._session_states[test_session_id] = {"skill_level": "intermediate"}
            service._session_creation_time[test_session_id] = 1234567890.0

            # Get sessions
            sessions_info = service.get_user_sessions("test_user")

            # Assertions
            assert "user_id" in sessions_info
            assert "sessions" in sessions_info
            assert "total_sessions" in sessions_info
            assert "active_sessions" in sessions_info
            assert sessions_info["user_id"] == "test_user"

    def test_session_expiry(self):
        """Test session expiry functionality"""
        with patch("app.services.adk_service.Agent") as mock_agent, patch(
            "time.time", return_value=2000000000.0
        ):  # Mock current time
            mock_agent_instance = Mock()
            mock_agent_instance.name = "system_design_agent"
            mock_agent.return_value = mock_agent_instance

            service = ADKService()
            
            # Create an expired session (very old timestamp)
            expired_session_id = "test_user_session_expired"
            service._session_creation_time[expired_session_id] = 1000000000.0  # Very old
            
            # Create a fresh session
            fresh_session_id = "test_user_session_fresh"
            service._session_creation_time[fresh_session_id] = 1999999000.0  # Recent
            
            # Test expiry check
            assert service._is_session_expired(expired_session_id) is True
            assert service._is_session_expired(fresh_session_id) is False

    @pytest.mark.asyncio
    async def test_chat_with_session_state_persistence(self):
        """Test that chat maintains session state across calls"""
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

            # Setup live events mock
            mock_event = Mock()
            mock_event.turn_complete = True
            mock_event.content = None

            async def mock_live_events():
                yield mock_event

            mock_runner_instance.run_live.return_value = mock_live_events()

            # Setup queue mock
            mock_queue_instance = Mock()
            mock_queue_class.return_value = mock_queue_instance

            # Test the service
            service = ADKService()
            
            # Pre-populate session state
            session_id = "test_user_session"
            test_state = {
                "skill_level": "advanced",
                "learning_progress": {"completed_topics": ["scalability"]},
                "preferences": {"difficulty": "hard", "focus_areas": ["databases"]}
            }
            service._session_states[session_id] = test_state
            service._session_creation_time[session_id] = 1999999999.0  # Recent timestamp
            
            # Make chat request with existing session
            request = ChatRequest(
                message="Continue our discussion",
                user_id="test_user",
                session_id=session_id
            )
            await service.chat(request)

            # Verify session state was used (check call to create_session with state)
            create_session_call = mock_session_service.create_session.call_args
            assert create_session_call is not None
            assert create_session_call.kwargs["state"] == test_state
