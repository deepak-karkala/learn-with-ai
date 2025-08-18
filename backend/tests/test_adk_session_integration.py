"""
Integration tests for ADK service session persistence.

Tests the integration between ADK service and session persistence service
for Issue #24: Persistent Session Storage with ADK Artifacts
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.adk_service import ADKService, ChatRequest, SessionCreateRequest
from app.services.session_persistence_service import SessionPersistenceService


@pytest.fixture
def mock_session_persistence_service():
    """Mock session persistence service for testing."""
    mock_service = MagicMock(spec=SessionPersistenceService)
    mock_service.save_session_state = AsyncMock(return_value=True)
    mock_service.load_session_state = AsyncMock(return_value=None)
    mock_service.delete_session = AsyncMock(return_value=True)
    mock_service.get_user_sessions = AsyncMock(return_value=[])
    mock_service.get_most_recent_session = AsyncMock(return_value=None)
    mock_service.migrate_in_memory_session = AsyncMock(return_value=True)
    mock_service.cleanup_expired_sessions = AsyncMock(return_value=0)
    mock_service.schedule_session_backup = AsyncMock()
    return mock_service


@pytest.fixture
def mock_adk_components():
    """Mock ADK components for testing."""
    mock_agent = MagicMock()
    mock_agent.name = "test_agent"
    
    mock_runner = MagicMock()
    mock_session_service = MagicMock()
    mock_session_service.create_session = AsyncMock()
    mock_runner.session_service = mock_session_service
    
    mock_session = MagicMock()
    mock_session_service.create_session.return_value = mock_session
    
    mock_live_queue = MagicMock()
    mock_live_queue.send_content = MagicMock()
    mock_live_queue.close = MagicMock()
    
    # Mock live events generator
    async def mock_live_events():
        # Simulate a simple response event
        mock_event = MagicMock()
        mock_event.turn_complete = False
        mock_event.partial = False
        mock_event.content = MagicMock()
        mock_event.content.parts = [MagicMock()]
        mock_event.content.parts[0].text = "Test response from agent"
        yield mock_event
        
        # Simulate turn complete event
        mock_complete_event = MagicMock()
        mock_complete_event.turn_complete = True
        yield mock_complete_event
    
    mock_runner.run_live = MagicMock(return_value=mock_live_events())
    
    return {
        'agent': mock_agent,
        'runner': mock_runner,
        'session': mock_session,
        'live_queue': mock_live_queue,
        'session_service': mock_session_service
    }


@pytest.mark.external_deps
class TestADKSessionPersistenceIntegration:
    """Test integration between ADK service and session persistence."""
    
    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_session_creation_with_persistence(self, mock_session_persistence_service, mock_adk_components):
        """Test that new sessions are saved to persistent storage."""
        with patch('app.services.adk_service.get_session_persistence_service', return_value=mock_session_persistence_service):
            with patch('app.services.adk_service.Agent', return_value=mock_adk_components['agent']):
                with patch('app.services.adk_service.InMemoryRunner', return_value=mock_adk_components['runner']):
                    with patch('app.services.adk_service.LiveRequestQueue', return_value=mock_adk_components['live_queue']):
                        
                        # Create ADK service
                        adk_service = ADKService()
                        
                        # Create a session
                        request = SessionCreateRequest(
                            user_id="test_user",
                            initial_state={"skill_level": "advanced"}
                        )
                        
                        response = await adk_service.create_session(request)
                        
                        assert response.success is True
                        assert response.session_id.startswith("test_user_session_")
                        
                        # Verify persistence service was called
                        mock_session_persistence_service.save_session_state.assert_called_once()
                        
                        call_args = mock_session_persistence_service.save_session_state.call_args
                        assert call_args[1]['user_id'] == "test_user"
                        assert call_args[1]['state_data']['skill_level'] == "advanced"

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_session_restoration_on_chat(self, mock_session_persistence_service, mock_adk_components):
        """Test that sessions are restored from persistent storage during chat."""
        # Mock restored session data
        restored_session_data = {
            "session_state": {
                "skill_level": "expert",
                "learning_progress": {"twitter": "completed"},
                "preferences": {"difficulty": "hard"}
            },
            "conversation_history": [
                {"role": "user", "content": "Previous message", "timestamp": time.time() - 100},
                {"role": "assistant", "content": "Previous response", "timestamp": time.time() - 90}
            ],
            "metadata": {"restored_at": "2025-01-01T00:00:00"}
        }
        
        mock_session_persistence_service.load_session_state.return_value = restored_session_data
        
        with patch('app.services.adk_service.get_session_persistence_service', return_value=mock_session_persistence_service):
            with patch('app.services.adk_service.Agent', return_value=mock_adk_components['agent']):
                with patch('app.services.adk_service.InMemoryRunner', return_value=mock_adk_components['runner']):
                    with patch('app.services.adk_service.LiveRequestQueue', return_value=mock_adk_components['live_queue']):
                        
                        adk_service = ADKService()
                        
                        # Chat with existing session ID
                        request = ChatRequest(
                            message="Continue our conversation",
                            user_id="test_user",
                            session_id="test_user_session_123"
                        )
                        
                        response = await adk_service.chat(request)
                        
                        assert response.success is True
                        assert response.session_id == "test_user_session_123"
                        
                        # Verify session was loaded from persistence
                        mock_session_persistence_service.load_session_state.assert_called_once_with(
                            "test_user_session_123", "test_user"
                        )
                        
                        # Verify session state was restored
                        assert "test_user_session_123" in adk_service._session_states
                        restored_state = adk_service._session_states["test_user_session_123"]
                        assert restored_state["skill_level"] == "expert"
                        assert restored_state["learning_progress"]["twitter"] == "completed"

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_conversation_history_preservation(self, mock_session_persistence_service, mock_adk_components):
        """Test that conversation history is preserved across multiple messages."""
        with patch('app.services.adk_service.get_session_persistence_service', return_value=mock_session_persistence_service):
            with patch('app.services.adk_service.Agent', return_value=mock_adk_components['agent']):
                with patch('app.services.adk_service.InMemoryRunner', return_value=mock_adk_components['runner']):
                    with patch('app.services.adk_service.LiveRequestQueue', return_value=mock_adk_components['live_queue']):
                        
                        adk_service = ADKService()
                        
                        # First message
                        request1 = ChatRequest(
                            message="Hello, I want to learn system design",
                            user_id="test_user",
                            session_id="test_user_session_123"
                        )
                        
                        response1 = await adk_service.chat(request1)
                        assert response1.success is True
                        
                        # Second message
                        request2 = ChatRequest(
                            message="What should I start with?",
                            user_id="test_user", 
                            session_id="test_user_session_123"
                        )
                        
                        response2 = await adk_service.chat(request2)
                        assert response2.success is True
                        
                        # Verify conversation history was tracked
                        assert "test_user_session_123" in adk_service._conversation_history
                        history = adk_service._conversation_history["test_user_session_123"]
                        
                        # Should have 4 entries: user1, assistant1, user2, assistant2
                        assert len(history) == 4
                        assert history[0]["role"] == "user"
                        assert history[0]["content"] == "Hello, I want to learn system design"
                        assert history[1]["role"] == "assistant"
                        assert history[2]["role"] == "user" 
                        assert history[2]["content"] == "What should I start with?"
                        assert history[3]["role"] == "assistant"
                        
                        # Verify session state was saved multiple times
                        assert mock_session_persistence_service.save_session_state.call_count >= 2

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_session_cleanup_with_persistence(self, mock_session_persistence_service, mock_adk_components):
        """Test that expired sessions are cleaned up from both memory and persistent storage."""
        with patch('app.services.adk_service.get_session_persistence_service', return_value=mock_session_persistence_service):
            with patch('app.services.adk_service.Agent', return_value=mock_adk_components['agent']):
                
                adk_service = ADKService()
                
                # Create an expired session
                expired_session_id = "test_user_session_expired"
                adk_service._session_states[expired_session_id] = {"test": "data"}
                adk_service._session_creation_time[expired_session_id] = time.time() - (adk_service._session_expiry_seconds + 100)
                
                # Trigger cleanup
                await adk_service._cleanup_expired_sessions()
                
                # Verify session was removed from memory
                assert expired_session_id not in adk_service._session_states
                assert expired_session_id not in adk_service._session_creation_time
                
                # Verify persistence service was called to delete session
                mock_session_persistence_service.delete_session.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_user_sessions_from_persistence(self, mock_session_persistence_service, mock_adk_components):
        """Test getting user sessions includes both memory and persistent storage."""
        # Mock persistent sessions
        mock_session_metadata = MagicMock()
        mock_session_metadata.session_id = "persistent_session_123"
        mock_session_metadata.created_at.timestamp.return_value = time.time() - 1000
        mock_session_metadata.last_accessed.timestamp.return_value = time.time() - 100
        mock_session_metadata.conversation_count = 10
        
        mock_session_persistence_service.get_user_sessions.return_value = [mock_session_metadata]
        
        with patch('app.services.adk_service.get_session_persistence_service', return_value=mock_session_persistence_service):
            with patch('app.services.adk_service.Agent', return_value=mock_adk_components['agent']):
                
                adk_service = ADKService()
                
                # Add a session in memory
                memory_session_id = "test_user_session_memory"
                adk_service._session_states[memory_session_id] = {"test": "memory"}
                adk_service._session_creation_time[memory_session_id] = time.time()
                
                # Get user sessions
                user_sessions = await adk_service.get_user_sessions("test_user")
                
                assert user_sessions["user_id"] == "test_user"
                assert "memory_sessions" in user_sessions
                assert "persistent_sessions" in user_sessions
                
                # Should include both memory and persistent sessions
                session_ids = [s["session_id"] for s in user_sessions["sessions"]]
                assert memory_session_id in session_ids
                assert "persistent_session_123" in session_ids

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_conversation_history_retrieval(self, mock_session_persistence_service, mock_adk_components):
        """Test retrieving conversation history from both memory and persistent storage."""
        # Mock persistent conversation history
        persistent_history = [
            {"role": "user", "content": "Old message", "timestamp": time.time() - 1000},
            {"role": "assistant", "content": "Old response", "timestamp": time.time() - 990}
        ]
        
        mock_session_persistence_service.load_session_state.return_value = {
            "conversation_history": persistent_history
        }
        
        with patch('app.services.adk_service.get_session_persistence_service', return_value=mock_session_persistence_service):
            with patch('app.services.adk_service.Agent', return_value=mock_adk_components['agent']):
                
                adk_service = ADKService()
                
                # Test getting conversation history from memory
                memory_session_id = "memory_session"
                adk_service._conversation_history[memory_session_id] = [
                    {"role": "user", "content": "Memory message", "timestamp": time.time()}
                ]
                
                memory_history = await adk_service.get_session_conversation_history(memory_session_id, "test_user")
                assert len(memory_history) == 1
                assert memory_history[0]["content"] == "Memory message"
                
                # Test getting conversation history from persistent storage
                persistent_session_id = "persistent_session"
                persistent_history_result = await adk_service.get_session_conversation_history(persistent_session_id, "test_user")
                
                assert len(persistent_history_result) == 2
                assert persistent_history_result[0]["content"] == "Old message"

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_graceful_degradation_without_persistence(self, mock_adk_components):
        """Test that ADK service works gracefully when persistence service is unavailable."""
        # Mock persistence service to fail initialization
        with patch('app.services.adk_service.get_session_persistence_service', side_effect=Exception("Persistence unavailable")):
            with patch('app.services.adk_service.Agent', return_value=mock_adk_components['agent']):
                with patch('app.services.adk_service.InMemoryRunner', return_value=mock_adk_components['runner']):
                    with patch('app.services.adk_service.LiveRequestQueue', return_value=mock_adk_components['live_queue']):
                        
                        adk_service = ADKService()
                        
                        # Should still be able to chat without persistence
                        request = ChatRequest(
                            message="Test message",
                            user_id="test_user"
                        )
                        
                        response = await adk_service.chat(request)
                        
                        # Should work but only use in-memory storage
                        assert response.success is True
                        assert response.session_id.startswith("test_user_session_")

    @pytest.mark.asyncio 
    @pytest.mark.external_deps
    async def test_session_migration_on_startup(self, mock_session_persistence_service, mock_adk_components):
        """Test migration of existing in-memory sessions to persistent storage."""
        with patch('app.services.adk_service.get_session_persistence_service', return_value=mock_session_persistence_service):
            with patch('app.services.adk_service.Agent', return_value=mock_adk_components['agent']):
                
                adk_service = ADKService()
                
                # Simulate existing in-memory sessions
                session_id1 = "user1_session_123"
                session_id2 = "user1_session_456"
                
                adk_service._session_states[session_id1] = {"skill_level": "beginner"}
                adk_service._session_states[session_id2] = {"skill_level": "intermediate"}
                adk_service._session_creation_time[session_id1] = time.time() - 100
                adk_service._session_creation_time[session_id2] = time.time() - 50
                
                adk_service._conversation_history[session_id1] = [
                    {"role": "user", "content": "Hello", "timestamp": time.time() - 90}
                ]
                
                # Manually trigger migration (in real implementation this could be done during initialization)
                for session_id, state_data in adk_service._session_states.items():
                    user_id = session_id.split('_session_')[0]
                    conversation_history = adk_service._conversation_history.get(session_id, [])
                    await mock_session_persistence_service.migrate_in_memory_session(
                        session_id=session_id,
                        user_id=user_id,
                        state_data=state_data,
                        conversation_history=conversation_history
                    )
                
                # Verify migration was called for both sessions
                assert mock_session_persistence_service.migrate_in_memory_session.call_count == 2

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_concurrent_session_access(self, mock_session_persistence_service, mock_adk_components):
        """Test concurrent access to the same session with persistence."""
        with patch('app.services.adk_service.get_session_persistence_service', return_value=mock_session_persistence_service):
            with patch('app.services.adk_service.Agent', return_value=mock_adk_components['agent']):
                with patch('app.services.adk_service.InMemoryRunner', return_value=mock_adk_components['runner']):
                    with patch('app.services.adk_service.LiveRequestQueue', return_value=mock_adk_components['live_queue']):
                        
                        adk_service = ADKService()
                        
                        # Simulate concurrent chat requests to the same session
                        session_id = "concurrent_session_123"
                        tasks = []
                        
                        for i in range(3):
                            request = ChatRequest(
                                message=f"Concurrent message {i}",
                                user_id="test_user",
                                session_id=session_id
                            )
                            task = adk_service.chat(request)
                            tasks.append(task)
                        
                        # Execute concurrently
                        responses = await asyncio.gather(*tasks, return_exceptions=True)
                        
                        # All should succeed
                        successful_responses = [r for r in responses if hasattr(r, 'success') and r.success]
                        assert len(successful_responses) == 3
                        
                        # Verify conversation history includes all messages
                        assert session_id in adk_service._conversation_history
                        history = adk_service._conversation_history[session_id]
                        # Should have 6 entries (3 user + 3 assistant messages)
                        assert len(history) == 6


@pytest.mark.external_deps
class TestSessionPersistenceFailures:
    """Test handling of persistence service failures."""

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_persistence_save_failure(self, mock_adk_components):
        """Test handling when persistence save fails."""
        mock_persistence = MagicMock()
        mock_persistence.save_session_state = AsyncMock(return_value=False)  # Simulate failure
        mock_persistence.load_session_state = AsyncMock(return_value=None)
        
        with patch('app.services.adk_service.get_session_persistence_service', return_value=mock_persistence):
            with patch('app.services.adk_service.Agent', return_value=mock_adk_components['agent']):
                with patch('app.services.adk_service.InMemoryRunner', return_value=mock_adk_components['runner']):
                    with patch('app.services.adk_service.LiveRequestQueue', return_value=mock_adk_components['live_queue']):
                        
                        adk_service = ADKService()
                        
                        # Should still work even if persistence fails
                        request = ChatRequest(
                            message="Test message",
                            user_id="test_user"
                        )
                        
                        response = await adk_service.chat(request)
                        
                        # Chat should still succeed even if persistence fails
                        assert response.success is True
                        
                        # Session should still be in memory
                        assert response.session_id in adk_service._session_states

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_persistence_load_failure(self, mock_adk_components):
        """Test handling when persistence load fails."""
        mock_persistence = MagicMock()
        mock_persistence.save_session_state = AsyncMock(return_value=True)
        mock_persistence.load_session_state = AsyncMock(side_effect=Exception("Load failed"))
        
        with patch('app.services.adk_service.get_session_persistence_service', return_value=mock_persistence):
            with patch('app.services.adk_service.Agent', return_value=mock_adk_components['agent']):
                with patch('app.services.adk_service.InMemoryRunner', return_value=mock_adk_components['runner']):
                    with patch('app.services.adk_service.LiveRequestQueue', return_value=mock_adk_components['live_queue']):
                        
                        adk_service = ADKService()
                        
                        # Should create new session if load fails
                        request = ChatRequest(
                            message="Test message",
                            user_id="test_user",
                            session_id="failed_load_session"
                        )
                        
                        response = await adk_service.chat(request)
                        
                        # Should still succeed by creating new session
                        assert response.success is True
                        assert "failed_load_session" in adk_service._session_states


if __name__ == "__main__":
    pytest.main([__file__, "-v"])