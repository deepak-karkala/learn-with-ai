"""
Simple test suite for session persistence functionality.

Tests the basic functionality of Issue #24: Persistent Session Storage with ADK Artifacts
"""

import asyncio
import json
import pytest
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.session_persistence_service import (
    SessionPersistenceService,
    SessionMetadata,
    SessionBackup,
    SessionState,
)


@pytest.mark.external_deps
class TestSessionPersistenceBasic:
    """Basic tests for session persistence service."""

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_service_initialization(self):
        """Test that service initializes correctly."""
        service = SessionPersistenceService()
        
        # Check default configuration
        assert service.artifact_namespace == "session_storage"
        assert service.session_ttl_hours == 24 * 7  # 7 days
        assert service.backup_interval_minutes == 5
        assert service.max_session_size_mb == 10
        
        # Initialize (should not throw)
        await service.initialize()
        
        # Should have empty cache initially
        assert service._session_metadata_cache == {}
        assert service._pending_saves == set()
        
        # Cleanup
        await service.shutdown()

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_session_backup_scheduling(self):
        """Test session backup scheduling."""
        service = SessionPersistenceService()
        await service.initialize()
        
        session_id = "test_session_backup"
        
        # Schedule a session for backup
        await service.schedule_session_backup(session_id)
        
        # Should be in pending saves
        assert session_id in service._pending_saves
        
        await service.shutdown()

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_session_size_validation(self):
        """Test session size validation."""
        service = SessionPersistenceService()
        await service.initialize()
        
        # Test with normal size data
        small_data = {"test": "data"}
        small_history = [{"role": "user", "content": "Hello"}]
        
        is_valid = await service._validate_session_size(
            "test_session", small_data, small_history
        )
        assert is_valid is True
        
        # Test with oversized data (> 10MB)
        large_data = {"large_field": "x" * (11 * 1024 * 1024)}  # 11MB
        
        is_valid = await service._validate_session_size(
            "test_session", large_data, None
        )
        assert is_valid is False
        
        await service.shutdown()

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_session_metadata_creation(self):
        """Test session metadata creation."""
        session_id = "test_session_123"
        user_id = "test_user"
        
        metadata = SessionMetadata(
            session_id=session_id,
            user_id=user_id,
            created_at=time.time(),
            last_accessed=time.time(),
            last_saved=time.time(),
            state=SessionState.ACTIVE,
            artifact_id="test_artifact",
            version=1,
            size_bytes=1024,
            conversation_count=5
        )
        
        assert metadata.session_id == session_id
        assert metadata.user_id == user_id
        assert metadata.state == SessionState.ACTIVE
        assert metadata.version == 1

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_session_backup_creation(self):
        """Test session backup creation."""
        session_id = "test_session_123"
        user_id = "test_user"
        state_data = {"skill_level": "advanced"}
        conversation_history = [
            {"role": "user", "content": "Hello", "timestamp": time.time()}
        ]
        
        backup = SessionBackup(
            session_id=session_id,
            user_id=user_id,
            state_data=state_data,
            conversation_history=conversation_history,
            metadata={"backup_type": "test"},
            timestamp=time.time(),
            version=1
        )
        
        assert backup.session_id == session_id
        assert backup.user_id == user_id
        assert backup.state_data["skill_level"] == "advanced"
        assert len(backup.conversation_history) == 1

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_session_version_increment(self):
        """Test session version increment logic."""
        service = SessionPersistenceService()
        await service.initialize()
        
        session_id = "test_session"
        
        # First version should be 1
        version1 = service._get_next_version(session_id)
        assert version1 == 1
        
        # Simulate metadata in cache
        metadata = SessionMetadata(
            session_id=session_id,
            user_id="test_user",
            created_at=time.time(),
            last_accessed=time.time(),
            last_saved=time.time(),
            state=SessionState.ACTIVE,
            version=1
        )
        service._session_metadata_cache[session_id] = metadata
        
        # Next version should be 2
        version2 = service._get_next_version(session_id)
        assert version2 == 2
        
        await service.shutdown()

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_session_creation_time_extraction(self):
        """Test extracting creation time from session ID."""
        service = SessionPersistenceService()
        
        # Test with properly formatted session ID
        timestamp = int(time.time())
        session_id = f"user123_session_{timestamp}"
        
        extracted_time = service._get_session_creation_time(session_id)
        assert extracted_time.timestamp() == timestamp
        
        # Test with invalid session ID format
        invalid_session_id = "invalid_format"
        extracted_time = service._get_session_creation_time(invalid_session_id)
        # Should return current time as fallback
        assert extracted_time.timestamp() <= time.time()

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_graceful_degradation_without_adk(self):
        """Test that service works without ADK artifacts available."""
        # Mock environment where ADK is not available
        with patch('app.services.session_persistence_service.Part', None):
            with patch('app.services.session_persistence_service.InMemoryArtifactService', None):
                service = SessionPersistenceService()
                await service.initialize()
                
                # Should initialize without ADK
                assert service._artifact_service is None
                
                # Should still be able to schedule backups
                await service.schedule_session_backup("test_session")
                assert "test_session" in service._pending_saves
                
                await service.shutdown()

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_background_worker_initialization(self):
        """Test that background workers are properly managed."""
        service = SessionPersistenceService()
        await service.initialize()
        
        # Background tasks should be created
        assert service._backup_task is not None
        assert service._cleanup_task is not None
        
        # Tasks should be running
        assert not service._backup_task.done()
        assert not service._cleanup_task.done()
        
        await service.shutdown()
        
        # Tasks should be cancelled after shutdown
        assert service._backup_task.cancelled() or service._backup_task.done()
        assert service._cleanup_task.cancelled() or service._cleanup_task.done()


@pytest.mark.external_deps
class TestSessionPersistenceWithMockRedis:
    """Test session persistence with mocked Redis."""

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_save_with_redis_fallback(self):
        """Test saving session with Redis fallback."""
        # Mock Redis service
        mock_redis = MagicMock()
        mock_redis.is_available.return_value = True
        mock_redis.set_cache = AsyncMock(return_value=True)
        mock_redis.sadd = AsyncMock(return_value=True)
        mock_redis.scan_keys = AsyncMock(return_value=[])  # For initialization
        
        service = SessionPersistenceService()
        service.redis_service = mock_redis
        await service.initialize()
        
        # Mock no ADK artifacts available
        service._artifact_service = None
        
        success = await service.save_session_state(
            session_id="test_session",
            user_id="test_user",
            state_data={"skill_level": "beginner"},
            conversation_history=[{"role": "user", "content": "Hello"}]
        )
        
        assert success is True
        
        # Verify Redis was called
        assert mock_redis.set_cache.call_count >= 1
        
        await service.shutdown()

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_load_with_redis_fallback(self):
        """Test loading session with Redis fallback."""
        # Mock Redis service with data
        mock_redis = MagicMock()
        mock_redis.is_available.return_value = True
        
        # Mock metadata
        now = datetime.utcnow().isoformat()
        metadata_json = {
            "session_id": "test_session",
            "user_id": "test_user",
            "created_at": now,
            "last_accessed": now,
            "last_saved": now,
            "state": "active",
            "artifact_id": "test_artifact",
            "version": 1,
            "size_bytes": 100,
            "conversation_count": 1
        }
        
        mock_redis.get_cache = AsyncMock(return_value=json.dumps(metadata_json))
        mock_redis.scan_keys = AsyncMock(return_value=[])  # For initialization
        
        service = SessionPersistenceService()
        service.redis_service = mock_redis
        await service.initialize()
        
        metadata = await service._get_session_metadata("test_session")
        
        assert metadata is not None
        assert metadata.session_id == "test_session"
        assert metadata.user_id == "test_user"
        assert metadata.state == SessionState.ACTIVE
        
        await service.shutdown()

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_delete_with_redis_cleanup(self):
        """Test deleting session cleans up Redis data."""
        mock_redis = MagicMock()
        mock_redis.is_available.return_value = True
        mock_redis.get_cache = AsyncMock(return_value=None)
        mock_redis.delete_cache = AsyncMock(return_value=True)
        mock_redis.srem = AsyncMock(return_value=True)
        mock_redis.scan_keys = AsyncMock(return_value=[])  # For initialization
        
        service = SessionPersistenceService()
        service.redis_service = mock_redis
        await service.initialize()
        
        # Add session to cache
        metadata = SessionMetadata(
            session_id="test_session",
            user_id="test_user",
            created_at=time.time(),
            last_accessed=time.time(),
            last_saved=time.time(),
            state=SessionState.ACTIVE
        )
        service._session_metadata_cache["test_session"] = metadata
        
        success = await service.delete_session("test_session", "test_user")
        
        assert success is True
        assert "test_session" not in service._session_metadata_cache
        
        # Verify Redis cleanup was called
        mock_redis.delete_cache.assert_called()
        
        await service.shutdown()


@pytest.mark.external_deps
class TestSessionPersistenceErrorHandling:
    """Test error handling in session persistence."""

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_redis_unavailable_graceful_handling(self):
        """Test graceful handling when Redis is unavailable."""
        mock_redis = MagicMock()
        mock_redis.is_available.return_value = False
        mock_redis.scan_keys = AsyncMock(return_value=[])  # For initialization
        
        service = SessionPersistenceService()
        service.redis_service = mock_redis
        await service.initialize()
        
        # Should handle gracefully
        success = await service.save_session_state(
            session_id="test_session",
            user_id="test_user",
            state_data={"test": "data"},
            conversation_history=[]
        )
        
        # Should return False but not throw exception
        assert success is False
        
        await service.shutdown()

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_malformed_metadata_handling(self):
        """Test handling of malformed metadata."""
        mock_redis = MagicMock()
        mock_redis.is_available.return_value = True
        mock_redis.get_cache = AsyncMock(return_value="invalid_json")
        mock_redis.scan_keys = AsyncMock(return_value=[])
        
        service = SessionPersistenceService()
        service.redis_service = mock_redis
        await service.initialize()
        
        # Should handle malformed data gracefully
        try:
            metadata = await service._get_session_metadata("test_session")
            # Should return None for malformed data
            assert metadata is None
        except json.JSONDecodeError:
            # This is also acceptable - the service should handle JSON errors
            pass
        
        await service.shutdown()

    @pytest.mark.asyncio
    @pytest.mark.external_deps
    async def test_concurrent_access_safety(self):
        """Test concurrent access safety."""
        service = SessionPersistenceService()
        await service.initialize()
        
        # Simulate concurrent access to pending saves
        session_ids = [f"session_{i}" for i in range(10)]
        
        # Add all sessions concurrently
        tasks = [service.schedule_session_backup(sid) for sid in session_ids]
        await asyncio.gather(*tasks)
        
        # All should be in pending saves
        for sid in session_ids:
            assert sid in service._pending_saves
        
        await service.shutdown()


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_session_persistence_simple.py -v
    import json
    pytest.main([__file__, "-v"])