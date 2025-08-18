"""
Test suite for session persistence functionality with ADK artifacts.

This test suite covers Issue #24: Persistent Session Storage with ADK Artifacts
"""

import asyncio
import json
import os
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.session_persistence_service import (
    SessionPersistenceService,
    SessionMetadata,
    SessionBackup,
    SessionState,
    get_session_persistence_service,
)


@pytest.fixture
async def persistence_service():
    """Create a session persistence service for testing."""
    service = SessionPersistenceService()
    await service.initialize()
    yield service
    await service.shutdown()


@pytest.fixture
def mock_redis_service():
    """Mock Redis service for testing."""
    mock_redis = MagicMock()
    mock_redis.is_available.return_value = True
    mock_redis.set_cache = AsyncMock()
    mock_redis.get_cache = AsyncMock()
    mock_redis.delete_cache = AsyncMock()
    mock_redis.sadd = AsyncMock()
    mock_redis.srem = AsyncMock()
    mock_redis.smembers = AsyncMock(return_value=["session_1", "session_2"])
    mock_redis.scan_keys = AsyncMock(return_value=["session_metadata:session_1", "session_metadata:session_2"])
    return mock_redis


@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        "session_id": "user123_session_1234567890",
        "user_id": "user123",
        "state_data": {
            "skill_level": "advanced",
            "learning_progress": {
                "completed": ["twitter", "instagram"],
                "current": "facebook"
            },
            "preferences": {
                "difficulty": "hard",
                "focus_areas": ["scalability", "performance"]
            }
        },
        "conversation_history": [
            {
                "role": "user",
                "content": "I want to design Twitter",
                "timestamp": time.time() - 300
            },
            {
                "role": "assistant", 
                "content": "Great! Let's start with requirements gathering...",
                "timestamp": time.time() - 290
            }
        ]
    }


@pytest.mark.external_deps
class TestSessionPersistenceService:
    """Test the SessionPersistenceService class."""

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_initialization(self):
        """Test service initialization."""
        service = SessionPersistenceService()
        assert service.artifact_namespace == "session_storage"
        assert service.session_ttl_hours == 24 * 7  # 7 days
        assert service.backup_interval_minutes == 5
        assert service.max_session_size_mb == 10
        
        await service.initialize()
        # Service should initialize even without ADK artifacts available
        assert service._session_metadata_cache == {}
        
        await service.shutdown()

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_save_session_state_success(self, persistence_service, sample_session_data, mock_redis_service):
        """Test successful session state saving."""
        with patch.object(persistence_service, 'redis_service', mock_redis_service):
            # Mock artifact service not available, should fallback to Redis
            persistence_service._artifact_service = None
            
            success = await persistence_service.save_session_state(
                session_id=sample_session_data["session_id"],
                user_id=sample_session_data["user_id"],
                state_data=sample_session_data["state_data"],
                conversation_history=sample_session_data["conversation_history"]
            )
            
            assert success is True
            
            # Verify session metadata was cached
            assert sample_session_data["session_id"] in persistence_service._session_metadata_cache
            
            # Verify Redis calls were made
            mock_redis_service.set_cache.assert_called()

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_save_session_state_oversized(self, persistence_service):
        """Test session state saving with oversized data."""
        # Create oversized session data (> 10MB)
        large_data = {"large_field": "x" * (11 * 1024 * 1024)}  # 11MB
        
        success = await persistence_service.save_session_state(
            session_id="test_session",
            user_id="test_user",
            state_data=large_data,
            conversation_history=[]
        )
        
        assert success is False

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_load_session_state_success(self, persistence_service, sample_session_data, mock_redis_service):
        """Test successful session state loading."""
        with patch.object(persistence_service, 'redis_service', mock_redis_service):
            # First save a session
            persistence_service._artifact_service = None
            await persistence_service.save_session_state(
                session_id=sample_session_data["session_id"],
                user_id=sample_session_data["user_id"],
                state_data=sample_session_data["state_data"],
                conversation_history=sample_session_data["conversation_history"]
            )
            
            # Now load it
            loaded_data = await persistence_service.load_session_state(
                session_id=sample_session_data["session_id"],
                user_id=sample_session_data["user_id"]
            )
            
            assert loaded_data is not None
            assert "session_state" in loaded_data
            assert "conversation_history" in loaded_data
            assert "metadata" in loaded_data

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_load_session_state_wrong_user(self, persistence_service, sample_session_data, mock_redis_service):
        """Test loading session state with wrong user ID."""
        with patch.object(persistence_service, 'redis_service', mock_redis_service):
            # First save a session
            persistence_service._artifact_service = None
            await persistence_service.save_session_state(
                session_id=sample_session_data["session_id"],
                user_id=sample_session_data["user_id"],
                state_data=sample_session_data["state_data"],
                conversation_history=sample_session_data["conversation_history"]
            )
            
            # Try to load with different user ID
            loaded_data = await persistence_service.load_session_state(
                session_id=sample_session_data["session_id"],
                user_id="different_user"
            )
            
            assert loaded_data is None

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_delete_session(self, persistence_service, sample_session_data, mock_redis_service):
        """Test session deletion."""
        with patch.object(persistence_service, 'redis_service', mock_redis_service):
            # First save a session
            persistence_service._artifact_service = None
            await persistence_service.save_session_state(
                session_id=sample_session_data["session_id"],
                user_id=sample_session_data["user_id"],
                state_data=sample_session_data["state_data"],
                conversation_history=sample_session_data["conversation_history"]
            )
            
            # Delete the session
            success = await persistence_service.delete_session(
                session_id=sample_session_data["session_id"],
                user_id=sample_session_data["user_id"]
            )
            
            assert success is True
            
            # Verify session is removed from cache
            assert sample_session_data["session_id"] not in persistence_service._session_metadata_cache

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_get_user_sessions(self, persistence_service, mock_redis_service):
        """Test getting all sessions for a user."""
        with patch.object(persistence_service, 'redis_service', mock_redis_service):
            user_id = "test_user"
            
            # Create multiple sessions for the user
            sessions = []
            for i in range(3):
                session_id = f"{user_id}_session_{int(time.time()) + i}"
                await persistence_service.save_session_state(
                    session_id=session_id,
                    user_id=user_id,
                    state_data={"test": f"data_{i}"},
                    conversation_history=[]
                )
                sessions.append(session_id)
            
            # Get user sessions
            user_sessions = await persistence_service.get_user_sessions(user_id)
            
            assert len(user_sessions) >= 3
            session_ids = [s.session_id for s in user_sessions]
            for session_id in sessions:
                assert session_id in session_ids

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_get_most_recent_session(self, persistence_service, mock_redis_service):
        """Test getting the most recent session for a user."""
        with patch.object(persistence_service, 'redis_service', mock_redis_service):
            user_id = "test_user"
            
            # Create sessions with different timestamps
            older_session = f"{user_id}_session_{int(time.time()) - 100}"
            newer_session = f"{user_id}_session_{int(time.time())}"
            
            await persistence_service.save_session_state(
                session_id=older_session,
                user_id=user_id,
                state_data={"test": "older"},
                conversation_history=[]
            )
            
            await persistence_service.save_session_state(
                session_id=newer_session,
                user_id=user_id,
                state_data={"test": "newer"},
                conversation_history=[]
            )
            
            # Get most recent session
            recent_session = await persistence_service.get_most_recent_session(user_id)
            
            assert recent_session is not None
            assert recent_session.session_id == newer_session

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_migrate_in_memory_session(self, persistence_service, mock_redis_service):
        """Test migrating an in-memory session to persistent storage."""
        with patch.object(persistence_service, 'redis_service', mock_redis_service):
            session_id = "memory_session_123"
            user_id = "test_user"
            state_data = {"skill_level": "beginner", "progress": {}}
            conversation_history = [
                {"role": "user", "content": "Hello", "timestamp": time.time()}
            ]
            
            # Migrate the session
            success = await persistence_service.migrate_in_memory_session(
                session_id=session_id,
                user_id=user_id,
                state_data=state_data,
                conversation_history=conversation_history
            )
            
            assert success is True
            
            # Verify session was saved
            assert session_id in persistence_service._session_metadata_cache

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_cleanup_expired_sessions(self, persistence_service, mock_redis_service):
        """Test cleanup of expired sessions."""
        with patch.object(persistence_service, 'redis_service', mock_redis_service):
            user_id = "test_user"
            
            # Create a session and mark it as expired
            session_id = f"{user_id}_session_expired"
            await persistence_service.save_session_state(
                session_id=session_id,
                user_id=user_id,
                state_data={"test": "expired"},
                conversation_history=[]
            )
            
            # Manually set the session metadata to be expired
            metadata = persistence_service._session_metadata_cache[session_id]
            metadata.last_accessed = datetime.utcnow() - timedelta(hours=persistence_service.session_ttl_hours + 1)
            
            # Run cleanup
            cleaned_count = await persistence_service.cleanup_expired_sessions()
            
            assert cleaned_count >= 1
            assert session_id not in persistence_service._session_metadata_cache

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_session_backup_scheduling(self, persistence_service):
        """Test session backup scheduling."""
        session_id = "test_session_backup"
        
        # Schedule a session for backup
        await persistence_service.schedule_session_backup(session_id)
        
        assert session_id in persistence_service._pending_saves

    @pytest.mark.asyncio 
    @pytest.mark.external_deps
    async def test_adk_artifacts_integration(self, persistence_service):
        """Test ADK artifacts integration when available."""
        # Mock ADK artifact components
        mock_part = MagicMock()
        mock_part.from_bytes.return_value = MagicMock()
        
        mock_session_context = MagicMock()
        mock_session_context.save_artifact.return_value = "v1"
        mock_session_context.load_artifact.return_value = MagicMock(data=b'{"test": "data"}')
        
        # Test with ADK artifacts available
        with patch('app.services.session_persistence_service.Part', mock_part):
            with patch.object(persistence_service, '_get_or_create_session_context', return_value=mock_session_context):
                persistence_service._artifact_service = MagicMock()
                
                success = await persistence_service.save_session_state(
                    session_id="test_session",
                    user_id="test_user",
                    state_data={"test": "artifact_data"},
                    conversation_history=[]
                )
                
                assert success is True
                mock_session_context.save_artifact.assert_called_once()


@pytest.mark.external_deps
class TestSessionPersistenceIntegration:
    """Integration tests for session persistence with other services."""

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_session_persistence_across_restart(self, persistence_service, mock_redis_service):
        """Test that sessions persist across service restarts."""
        with patch.object(persistence_service, 'redis_service', mock_redis_service):
            # Save a session
            session_id = "restart_test_session"
            user_id = "restart_user"
            state_data = {"persistent": "data"}
            
            await persistence_service.save_session_state(
                session_id=session_id,
                user_id=user_id,
                state_data=state_data,
                conversation_history=[]
            )
            
            # Simulate service restart by clearing memory
            persistence_service._session_metadata_cache.clear()
            
            # Should be able to load from persistent storage
            loaded_data = await persistence_service.load_session_state(session_id, user_id)
            
            assert loaded_data is not None
            assert loaded_data["session_state"]["persistent"] == "data"

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_long_term_session_continuity(self, persistence_service, mock_redis_service):
        """Test long-term session continuity (months later)."""
        with patch.object(persistence_service, 'redis_service', mock_redis_service):
            # Create session with historical data
            session_id = "longterm_session"
            user_id = "longterm_user"
            state_data = {
                "skill_level": "expert",
                "learning_progress": {"twitter": "completed", "facebook": "in_progress"}
            }
            conversation_history = [
                {"role": "user", "content": "Let's design Twitter", "timestamp": time.time() - (90 * 24 * 3600)},
                {"role": "assistant", "content": "Great! Let's start...", "timestamp": time.time() - (90 * 24 * 3600)}
            ]
            
            await persistence_service.save_session_state(
                session_id=session_id,
                user_id=user_id,
                state_data=state_data,
                conversation_history=conversation_history
            )
            
            # Load after long time (should still work)
            loaded_data = await persistence_service.load_session_state(session_id, user_id)
            
            assert loaded_data is not None
            assert loaded_data["session_state"]["skill_level"] == "expert"
            assert len(loaded_data["conversation_history"]) == 2

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_fallback_mechanisms(self, persistence_service):
        """Test fallback mechanisms for corrupted or missing artifacts."""
        # Test with corrupted Redis data
        mock_redis = MagicMock()
        mock_redis.is_available.return_value = True
        mock_redis.get_cache = AsyncMock(return_value="invalid_json_data")
        
        with patch.object(persistence_service, 'redis_service', mock_redis):
            loaded_data = await persistence_service.load_session_state("corrupt_session", "test_user")
            assert loaded_data is None

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_performance_optimization(self, persistence_service, mock_redis_service):
        """Test performance optimization for artifact operations."""
        with patch.object(persistence_service, 'redis_service', mock_redis_service):
            # Test batch operations don't cause performance issues
            start_time = time.time()
            
            # Create multiple sessions concurrently
            tasks = []
            for i in range(10):
                task = persistence_service.save_session_state(
                    session_id=f"perf_test_{i}",
                    user_id="perf_user",
                    state_data={"index": i},
                    conversation_history=[]
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            # All operations should succeed
            assert all(results)
            
            # Should complete within reasonable time (adjust threshold as needed)
            assert (end_time - start_time) < 5.0  # 5 seconds for 10 operations


@pytest.mark.external_deps
class TestSessionPersistenceErrorCases:
    """Test error cases and edge conditions."""

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_redis_unavailable(self, persistence_service):
        """Test graceful handling when Redis is unavailable."""
        mock_redis = MagicMock()
        mock_redis.is_available.return_value = False
        
        with patch.object(persistence_service, 'redis_service', mock_redis):
            # Should handle gracefully without throwing errors
            success = await persistence_service.save_session_state(
                session_id="no_redis_session",
                user_id="test_user",
                state_data={"test": "data"},
                conversation_history=[]
            )
            
            # May fail gracefully or succeed with limited functionality
            assert isinstance(success, bool)

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_adk_artifacts_unavailable(self, persistence_service, mock_redis_service):
        """Test fallback when ADK artifacts are unavailable."""
        with patch.object(persistence_service, 'redis_service', mock_redis_service):
            # Ensure ADK artifacts are not available
            persistence_service._artifact_service = None
            
            # Should fallback to Redis
            success = await persistence_service.save_session_state(
                session_id="fallback_session",
                user_id="test_user", 
                state_data={"test": "fallback"},
                conversation_history=[]
            )
            
            assert success is True

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_concurrent_access(self, persistence_service, mock_redis_service):
        """Test concurrent access to session persistence."""
        with patch.object(persistence_service, 'redis_service', mock_redis_service):
            session_id = "concurrent_session"
            user_id = "concurrent_user"
            
            # Simulate concurrent save operations
            tasks = []
            for i in range(5):
                task = persistence_service.save_session_state(
                    session_id=session_id,
                    user_id=user_id,
                    state_data={"concurrent_save": i},
                    conversation_history=[]
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Should handle concurrent access gracefully
            successful_saves = [r for r in results if r is True]
            assert len(successful_saves) > 0


# Helper functions for testing
def create_mock_session_metadata(session_id: str, user_id: str) -> SessionMetadata:
    """Create mock session metadata for testing."""
    return SessionMetadata(
        session_id=session_id,
        user_id=user_id,
        created_at=datetime.utcnow(),
        last_accessed=datetime.utcnow(),
        last_saved=datetime.utcnow(),
        state=SessionState.ACTIVE,
        artifact_id="test_artifact_123",
        version=1,
        size_bytes=1024,
        conversation_count=5
    )


def create_mock_session_backup(session_id: str, user_id: str) -> SessionBackup:
    """Create mock session backup for testing."""
    return SessionBackup(
        session_id=session_id,
        user_id=user_id,
        state_data={"test": "state"},
        conversation_history=[{"role": "user", "content": "test", "timestamp": time.time()}],
        metadata={"backup_type": "test"},
        timestamp=datetime.utcnow(),
        version=1
    )


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])