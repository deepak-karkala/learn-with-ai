"""
Session Persistence Service for storing session state using ADK Artifacts.

This service provides persistent session storage using Google ADK artifacts,
enabling session continuity across server restarts and long user absences.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

try:
    from google.genai.types import Part
    from google.adk.agents import Agent
    from google.adk.runners import InMemoryRunner
    from google.adk.sessions import Session, InMemorySessionService
    from google.adk.artifacts import InMemoryArtifactService, GcsArtifactService
except ImportError:
    # Fallback for environments without ADK
    Part = None
    Agent = None
    InMemoryRunner = None
    Session = None
    InMemorySessionService = None
    InMemoryArtifactService = None
    GcsArtifactService = None

from ..services.redis_service import get_redis_service
from ..services.monitoring_service import get_monitoring_service

logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    """Session state enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    CORRUPTED = "corrupted"


@dataclass
class SessionMetadata:
    """Session metadata for tracking and management."""
    session_id: str
    user_id: str
    created_at: datetime
    last_accessed: datetime
    last_saved: datetime
    state: SessionState
    artifact_id: Optional[str] = None
    version: int = 1
    size_bytes: int = 0
    conversation_count: int = 0


@dataclass
class SessionBackup:
    """Session backup data structure."""
    session_id: str
    user_id: str
    state_data: Dict[str, Any]
    conversation_history: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    timestamp: datetime
    version: int


class SessionPersistenceService:
    """Service for persistent session storage using ADK artifacts."""
    
    def __init__(self):
        self.redis_service = get_redis_service()
        self.monitoring_service = get_monitoring_service()
        
        # Configuration
        self.artifact_namespace = "session_storage"
        self.session_ttl_hours = 24 * 7  # 7 days
        self.backup_interval_minutes = 5
        self.max_session_size_mb = 10
        self.cleanup_interval_hours = 6
        
        # ADK artifact services
        self._artifact_service: Optional[Any] = None
        self._session_service: Optional[InMemorySessionService] = None
        self._use_gcs_artifacts = os.getenv("USE_GCS_ARTIFACTS", "false").lower() == "true"
        self._gcs_bucket_name = os.getenv("GCS_BUCKET_NAME")
        
        # In-memory caches for performance
        self._session_metadata_cache: Dict[str, SessionMetadata] = {}
        self._pending_saves: Set[str] = set()
        self._last_cleanup_time = time.time()
        
        # Background task management
        self._backup_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info("Session persistence service initialized")
    
    async def initialize(self) -> None:
        """Initialize the session persistence service."""
        try:
            # Initialize ADK artifact service
            await self._initialize_artifact_service()
            
            # Initialize session service
            if InMemorySessionService:
                self._session_service = InMemorySessionService()
            
            # Start background tasks
            self._backup_task = asyncio.create_task(self._backup_worker())
            self._cleanup_task = asyncio.create_task(self._cleanup_worker())
            
            # Load session metadata from Redis cache
            await self._load_session_metadata_cache()
            
            logger.info("Session persistence service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize session persistence service: {e}")
            raise
    
    async def _initialize_artifact_service(self) -> None:
        """Initialize the appropriate ADK artifact service."""
        try:
            if self._use_gcs_artifacts and self._gcs_bucket_name and GcsArtifactService:
                # Use GCS-based persistent artifact storage
                self._artifact_service = GcsArtifactService(bucket_name=self._gcs_bucket_name)
                logger.info(f"Initialized GCS artifact service with bucket: {self._gcs_bucket_name}")
            elif InMemoryArtifactService:
                # Use in-memory artifact storage (fallback)
                self._artifact_service = InMemoryArtifactService()
                logger.info("Initialized in-memory artifact service")
            else:
                logger.warning("ADK artifacts not available, using Redis fallback")
                self._artifact_service = None
        except Exception as e:
            logger.error(f"Failed to initialize artifact service: {e}")
            self._artifact_service = None
    
    async def shutdown(self) -> None:
        """Shutdown the session persistence service."""
        try:
            # Cancel background tasks
            if self._backup_task:
                self._backup_task.cancel()
                try:
                    await self._backup_task
                except asyncio.CancelledError:
                    pass
            
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Save any pending session data
            await self._flush_pending_saves()
            
            logger.info("Session persistence service shut down")
            
        except Exception as e:
            logger.error(f"Error during session persistence service shutdown: {e}")
    
    # =============================================================================
    # Session State Management
    # =============================================================================
    
    async def save_session_state(
        self,
        session_id: str,
        user_id: str,
        state_data: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Save session state to persistent storage.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            state_data: Session state data
            conversation_history: Optional conversation history
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Validate session data size
            if not await self._validate_session_size(session_id, state_data, conversation_history):
                return False
            
            # Create session backup
            backup = SessionBackup(
                session_id=session_id,
                user_id=user_id,
                state_data=state_data,
                conversation_history=conversation_history or [],
                metadata={
                    "saved_at": datetime.utcnow().isoformat(),
                    "service_version": "1.0",
                    "backup_type": "automatic"
                },
                timestamp=datetime.utcnow(),
                version=self._get_next_version(session_id)
            )
            
            # Save to ADK artifact
            artifact_id = await self._save_to_artifact(backup)
            if not artifact_id:
                return False
            
            # Update session metadata
            # Calculate size using the same serialization approach as _save_to_artifact
            backup_data = {
                "session_id": backup.session_id,
                "user_id": backup.user_id,
                "state_data": backup.state_data,
                "conversation_history": backup.conversation_history,
                "metadata": backup.metadata,
                "timestamp": backup.timestamp.isoformat(),
                "version": backup.version
            }
            size_bytes = len(json.dumps(backup_data, default=str).encode())
            
            metadata = SessionMetadata(
                session_id=session_id,
                user_id=user_id,
                created_at=self._get_session_creation_time(session_id),
                last_accessed=datetime.utcnow(),
                last_saved=datetime.utcnow(),
                state=SessionState.ACTIVE,
                artifact_id=artifact_id,
                version=backup.version,
                size_bytes=size_bytes,
                conversation_count=len(conversation_history or [])
            )
            
            # Cache metadata and save to Redis
            self._session_metadata_cache[session_id] = metadata
            await self._save_session_metadata(metadata)
            
            # Remove from pending saves
            self._pending_saves.discard(session_id)
            
            logger.debug(f"Successfully saved session {session_id} to artifact {artifact_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            self.monitoring_service.track_error(
                error=e,
                context="session_persistence_save",
                metadata={"session_id": session_id, "user_id": user_id}
            )
            return False
    
    async def load_session_state(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Load session state from persistent storage.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            
        Returns:
            Session state data if found, None otherwise
        """
        try:
            # Get session metadata
            metadata = await self._get_session_metadata(session_id)
            if not metadata:
                logger.debug(f"No metadata found for session {session_id}")
                return None
            
            # Verify user ownership
            if metadata.user_id != user_id:
                logger.warning(f"User {user_id} attempted to access session {session_id} owned by {metadata.user_id}")
                return None
            
            # Check if session is expired
            if self._is_session_expired(metadata):
                logger.debug(f"Session {session_id} is expired")
                await self._mark_session_expired(session_id)
                return None
            
            # Load from ADK artifact
            backup = await self._load_from_artifact(metadata.artifact_id)
            if not backup:
                logger.warning(f"Failed to load session {session_id} from artifact {metadata.artifact_id}")
                await self._mark_session_corrupted(session_id)
                return None
            
            # Update last accessed time
            metadata.last_accessed = datetime.utcnow()
            self._session_metadata_cache[session_id] = metadata
            await self._save_session_metadata(metadata)
            
            # Return combined state
            return {
                "session_state": backup.state_data,
                "conversation_history": backup.conversation_history,
                "metadata": {
                    **backup.metadata,
                    "restored_at": datetime.utcnow().isoformat(),
                    "version": backup.version
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            self.monitoring_service.track_error(
                error=e,
                context="session_persistence_load",
                metadata={"session_id": session_id, "user_id": user_id}
            )
            return None
    
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """
        Delete a session from persistent storage.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Get session metadata
            metadata = await self._get_session_metadata(session_id)
            if not metadata:
                return True  # Already deleted
            
            # Verify user ownership
            if metadata.user_id != user_id:
                logger.warning(f"User {user_id} attempted to delete session {session_id} owned by {metadata.user_id}")
                return False
            
            # Delete from ADK artifact
            if metadata.artifact_id:
                await self._delete_artifact(metadata.artifact_id)
            
            # Remove from caches and Redis
            self._session_metadata_cache.pop(session_id, None)
            await self._delete_session_metadata(session_id)
            self._pending_saves.discard(session_id)
            
            logger.info(f"Successfully deleted session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    # =============================================================================
    # Session Discovery and Management
    # =============================================================================
    
    async def get_user_sessions(
        self,
        user_id: str,
        include_expired: bool = False
    ) -> List[SessionMetadata]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User identifier
            include_expired: Whether to include expired sessions
            
        Returns:
            List of session metadata
        """
        try:
            # Get all session IDs for this user from Redis
            session_ids = await self._get_user_session_ids(user_id)
            
            sessions = []
            for session_id in session_ids:
                metadata = await self._get_session_metadata(session_id)
                if metadata and (include_expired or not self._is_session_expired(metadata)):
                    sessions.append(metadata)
            
            # Sort by last accessed time (most recent first)
            sessions.sort(key=lambda s: s.last_accessed, reverse=True)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            return []
    
    async def get_most_recent_session(
        self,
        user_id: str
    ) -> Optional[SessionMetadata]:
        """
        Get the most recently accessed session for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Most recent session metadata or None
        """
        sessions = await self.get_user_sessions(user_id, include_expired=False)
        return sessions[0] if sessions else None
    
    async def migrate_in_memory_session(
        self,
        session_id: str,
        user_id: str,
        state_data: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Migrate an in-memory session to persistent storage.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
            state_data: Session state data from memory
            conversation_history: Conversation history from memory
            
        Returns:
            True if migration was successful, False otherwise
        """
        try:
            logger.info(f"Migrating in-memory session {session_id} to persistent storage")
            
            # Check if session already exists in persistent storage
            existing_metadata = await self._get_session_metadata(session_id)
            if existing_metadata:
                logger.info(f"Session {session_id} already exists in persistent storage, updating")
            
            # Save the session state
            success = await self.save_session_state(
                session_id=session_id,
                user_id=user_id,
                state_data=state_data,
                conversation_history=conversation_history
            )
            
            if success:
                logger.info(f"Successfully migrated session {session_id} to persistent storage")
            else:
                logger.error(f"Failed to migrate session {session_id} to persistent storage")
            
            return success
            
        except Exception as e:
            logger.error(f"Error migrating session {session_id}: {e}")
            return False
    
    # =============================================================================
    # Cleanup and Maintenance
    # =============================================================================
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            cleaned_count = 0
            
            # Get all session metadata from cache
            for session_id, metadata in list(self._session_metadata_cache.items()):
                if self._is_session_expired(metadata):
                    if await self.delete_session(session_id, metadata.user_id):
                        cleaned_count += 1
            
            # Also clean up from Redis in case of cache misses
            all_session_ids = await self._get_all_session_ids()
            for session_id in all_session_ids:
                if session_id not in self._session_metadata_cache:
                    metadata = await self._get_session_metadata(session_id)
                    if metadata and self._is_session_expired(metadata):
                        if await self.delete_session(session_id, metadata.user_id):
                            cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired sessions")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
            return 0
    
    async def schedule_session_backup(self, session_id: str) -> None:
        """
        Schedule a session for backup.
        
        Args:
            session_id: Session to backup
        """
        self._pending_saves.add(session_id)
        logger.debug(f"Scheduled session {session_id} for backup")
    
    # =============================================================================
    # Session Context Management
    # =============================================================================
    
    async def _get_or_create_session_context(self, user_id: str, session_id: str) -> Optional[Any]:
        """Get or create a session context for artifact operations."""
        try:
            if not self._session_service:
                return None

            # Get or create a session for artifact operations
            try:
                # Try to get existing session first
                session_context = await self._session_service.get_session(session_id=session_id)
            except Exception:
                # Session doesn't exist, create it (without 'app' parameter - not supported by InMemorySessionService)
                session_context = await self._session_service.create_session(
                    app_name="session_persistence",
                    user_id=user_id,
                    session_id=session_id,
                    state={}
                )

            return session_context

        except Exception as e:
            logger.error(f"Failed to create session context for {user_id}/{session_id}: {e}")
            return None
    
    # =============================================================================
    # Private Methods - ADK Artifact Operations
    # =============================================================================
    
    async def _save_to_artifact(self, backup: SessionBackup) -> Optional[str]:
        """Save session backup to ADK artifact."""
        try:
            # Prepare artifact data
            backup_data = json.dumps({
                "session_id": backup.session_id,
                "user_id": backup.user_id,
                "state_data": backup.state_data,
                "conversation_history": backup.conversation_history,
                "metadata": backup.metadata,
                "timestamp": backup.timestamp.isoformat(),
                "version": backup.version
            }, default=str)
            
            # Create filename with namespace prefix for user-scoped artifact
            artifact_filename = f"user:{backup.user_id}_session_{backup.session_id}_v{backup.version}.json"
            
            if self._artifact_service and Part:
                # Get session context for artifact operations
                session_context = await self._get_or_create_session_context(
                    backup.user_id, 
                    backup.session_id
                )
                
                if session_context:
                    # Use ADK artifacts with session context
                    artifact_part = Part.from_bytes(
                        data=backup_data.encode('utf-8'),
                        mime_type="application/json"
                    )
                    
                    # Save using session context (proper ADK pattern)
                    try:
                        version = session_context.save_artifact(
                            filename=artifact_filename,
                            artifact=artifact_part
                        )
                        logger.debug(f"Saved session {backup.session_id} to ADK artifact {artifact_filename} version {version}")
                        return f"{artifact_filename}:{version}"
                    except AttributeError:
                        logger.warning("Session context doesn't support save_artifact method")
                else:
                    logger.warning("Could not create session context for artifact operations")
            
            # Fallback to Redis storage
            artifact_id = f"artifact_{backup.session_id}_{int(time.time())}"
            if self.redis_service.is_available():
                redis_key = f"session_artifact:{artifact_id}"
                await self.redis_service.set_cache(
                    redis_key,
                    backup_data,
                    ttl_seconds=self.session_ttl_hours * 3600
                )
                logger.debug(f"Saved session {backup.session_id} to Redis fallback {artifact_id}")
                return artifact_id
            
            logger.error("No storage backend available for session artifacts")
            return None
            
        except Exception as e:
            logger.error(f"Failed to save session backup to artifact: {e}")
            return None
    
    async def _load_from_artifact(self, artifact_id: str) -> Optional[SessionBackup]:
        """Load session backup from ADK artifact."""
        try:
            backup_data = None
            
            # Try ADK artifacts first
            if self._artifact_service and ":" in artifact_id:
                filename, version = artifact_id.split(":", 1)
                
                # Extract user_id from filename for session context
                user_id = None
                if filename.startswith("user:"):
                    parts = filename.split("_")
                    if len(parts) >= 2:
                        user_id = parts[0].replace("user:", "")
                
                if user_id:
                    session_context = await self._get_or_create_session_context(user_id, "temp_load_session")
                    if session_context:
                        try:
                            artifact_part = session_context.load_artifact(
                                filename=filename,
                                version=int(version) if version.isdigit() else None
                            )
                            if artifact_part and hasattr(artifact_part, 'data'):
                                backup_data = artifact_part.data.decode('utf-8')
                                logger.debug(f"Loaded session from ADK artifact {filename}:{version}")
                        except Exception as e:
                            logger.warning(f"Failed to load from ADK artifact {artifact_id}: {e}")
                    else:
                        logger.warning(f"Could not create session context for loading artifact {artifact_id}")
                else:
                    logger.warning(f"Could not extract user_id from artifact filename {filename}")
            
            # Fallback to Redis
            if not backup_data and self.redis_service.is_available():
                redis_key = f"session_artifact:{artifact_id}"
                backup_data = await self.redis_service.get_cache(redis_key)
                if backup_data:
                    logger.debug(f"Loaded session from Redis fallback {artifact_id}")
            
            if backup_data:
                backup_dict = json.loads(backup_data)
                return SessionBackup(
                    session_id=backup_dict["session_id"],
                    user_id=backup_dict["user_id"],
                    state_data=backup_dict["state_data"],
                    conversation_history=backup_dict["conversation_history"],
                    metadata=backup_dict["metadata"],
                    timestamp=datetime.fromisoformat(backup_dict["timestamp"]),
                    version=backup_dict["version"]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load session backup from artifact {artifact_id}: {e}")
            return None
    
    async def _delete_artifact(self, artifact_id: str) -> bool:
        """Delete ADK artifact."""
        try:
            deleted = False
            
            # Try ADK artifacts first
            if self._artifact_service and ":" in artifact_id:
                filename, version = artifact_id.split(":", 1)
                try:
                    if hasattr(self._artifact_service, 'delete_artifact'):
                        await self._artifact_service.delete_artifact(
                            filename=filename,
                            version=int(version) if version.isdigit() else None
                        )
                        deleted = True
                        logger.debug(f"Deleted ADK artifact {filename}:{version}")
                except Exception as e:
                    logger.warning(f"Failed to delete ADK artifact {artifact_id}: {e}")
            
            # Also clean up Redis fallback
            if self.redis_service.is_available():
                redis_key = f"session_artifact:{artifact_id}"
                await self.redis_service.delete_cache(redis_key)
                deleted = True
                logger.debug(f"Deleted Redis artifact {artifact_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete artifact {artifact_id}: {e}")
            return False
    
    # =============================================================================
    # Private Methods - Metadata Management
    # =============================================================================
    
    async def _get_session_metadata(self, session_id: str) -> Optional[SessionMetadata]:
        """Get session metadata from cache or Redis."""
        # Check cache first
        if session_id in self._session_metadata_cache:
            return self._session_metadata_cache[session_id]
        
        # Load from Redis
        if self.redis_service.is_available():
            redis_key = f"session_metadata:{session_id}"
            data = await self.redis_service.get_cache(redis_key)
            if data:
                try:
                    metadata_dict = json.loads(data)
                    metadata = SessionMetadata(
                        session_id=metadata_dict["session_id"],
                        user_id=metadata_dict["user_id"],
                        created_at=datetime.fromisoformat(metadata_dict["created_at"]),
                        last_accessed=datetime.fromisoformat(metadata_dict["last_accessed"]),
                        last_saved=datetime.fromisoformat(metadata_dict["last_saved"]),
                        state=SessionState(metadata_dict["state"]),
                        artifact_id=metadata_dict.get("artifact_id"),
                        version=metadata_dict.get("version", 1),
                        size_bytes=metadata_dict.get("size_bytes", 0),
                        conversation_count=metadata_dict.get("conversation_count", 0)
                    )
                    
                    # Cache it
                    self._session_metadata_cache[session_id] = metadata
                    return metadata
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse session metadata for {session_id}: {e}")
                    return None
        
        return None
    
    async def _save_session_metadata(self, metadata: SessionMetadata) -> None:
        """Save session metadata to Redis."""
        if self.redis_service.is_available():
            redis_key = f"session_metadata:{metadata.session_id}"
            await self.redis_service.set_cache(
                redis_key,
                json.dumps({
                    "session_id": metadata.session_id,
                    "user_id": metadata.user_id,
                    "created_at": metadata.created_at.isoformat(),
                    "last_accessed": metadata.last_accessed.isoformat(),
                    "last_saved": metadata.last_saved.isoformat(),
                    "state": metadata.state.value,
                    "artifact_id": metadata.artifact_id,
                    "version": metadata.version,
                    "size_bytes": metadata.size_bytes,
                    "conversation_count": metadata.conversation_count
                }),
                ttl_seconds=self.session_ttl_hours * 3600
            )
            
            # Also add to user's session list
            user_sessions_key = f"user_sessions:{metadata.user_id}"
            await self.redis_service.sadd(user_sessions_key, metadata.session_id)
    
    async def _delete_session_metadata(self, session_id: str) -> None:
        """Delete session metadata from Redis."""
        if self.redis_service.is_available():
            # Get metadata first to remove from user's session list
            metadata = await self._get_session_metadata(session_id)
            if metadata:
                user_sessions_key = f"user_sessions:{metadata.user_id}"
                await self.redis_service.srem(user_sessions_key, session_id)
            
            # Delete metadata
            redis_key = f"session_metadata:{session_id}"
            await self.redis_service.delete_cache(redis_key)
    
    async def _get_user_session_ids(self, user_id: str) -> List[str]:
        """Get all session IDs for a user."""
        if self.redis_service.is_available():
            user_sessions_key = f"user_sessions:{user_id}"
            return await self.redis_service.smembers(user_sessions_key) or []
        return []
    
    async def _get_all_session_ids(self) -> List[str]:
        """Get all session IDs."""
        if self.redis_service.is_available():
            pattern = "session_metadata:*"
            keys = await self.redis_service.scan_keys(pattern)
            return [key.replace("session_metadata:", "") for key in keys]
        return []
    
    async def _load_session_metadata_cache(self) -> None:
        """Load session metadata into cache on startup."""
        try:
            session_ids = await self._get_all_session_ids()
            for session_id in session_ids:
                metadata = await self._get_session_metadata(session_id)
                if metadata:
                    self._session_metadata_cache[session_id] = metadata
            
            logger.info(f"Loaded {len(self._session_metadata_cache)} sessions into metadata cache")
            
        except Exception as e:
            logger.error(f"Failed to load session metadata cache: {e}")
    
    # =============================================================================
    # Private Methods - Utilities
    # =============================================================================
    
    def _is_session_expired(self, metadata: SessionMetadata) -> bool:
        """Check if a session is expired."""
        expiry_time = metadata.last_accessed + timedelta(hours=self.session_ttl_hours)
        return datetime.utcnow() > expiry_time
    
    async def _mark_session_expired(self, session_id: str) -> None:
        """Mark a session as expired."""
        if session_id in self._session_metadata_cache:
            self._session_metadata_cache[session_id].state = SessionState.EXPIRED
            await self._save_session_metadata(self._session_metadata_cache[session_id])
    
    async def _mark_session_corrupted(self, session_id: str) -> None:
        """Mark a session as corrupted."""
        if session_id in self._session_metadata_cache:
            self._session_metadata_cache[session_id].state = SessionState.CORRUPTED
            await self._save_session_metadata(self._session_metadata_cache[session_id])
    
    def _get_session_creation_time(self, session_id: str) -> datetime:
        """Extract creation time from session ID or return current time."""
        try:
            # Session IDs are in format: {user_id}_session_{timestamp}
            parts = session_id.split("_session_")
            if len(parts) == 2:
                timestamp = int(parts[1])
                return datetime.fromtimestamp(timestamp)
        except (ValueError, IndexError):
            pass
        
        return datetime.utcnow()
    
    def _get_next_version(self, session_id: str) -> int:
        """Get the next version number for a session."""
        metadata = self._session_metadata_cache.get(session_id)
        return (metadata.version + 1) if metadata else 1
    
    async def _validate_session_size(
        self,
        session_id: str,
        state_data: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, Any]]]
    ) -> bool:
        """Validate that session data is within size limits."""
        try:
            # Calculate approximate size
            data_size = len(json.dumps(state_data).encode())
            if conversation_history:
                data_size += len(json.dumps(conversation_history).encode())
            
            size_mb = data_size / (1024 * 1024)
            
            if size_mb > self.max_session_size_mb:
                logger.warning(
                    f"Session {session_id} size ({size_mb:.2f}MB) exceeds limit ({self.max_session_size_mb}MB)"
                )
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate session size for {session_id}: {e}")
            return False
    
    # =============================================================================
    # Background Workers
    # =============================================================================
    
    async def _backup_worker(self) -> None:
        """Background worker for periodic session backups."""
        while True:
            try:
                await asyncio.sleep(self.backup_interval_minutes * 60)
                await self._flush_pending_saves()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in backup worker: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _cleanup_worker(self) -> None:
        """Background worker for periodic cleanup."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval_hours * 3600)
                
                # Perform cleanup if enough time has passed
                current_time = time.time()
                if current_time - self._last_cleanup_time > (self.cleanup_interval_hours * 3600):
                    cleaned_count = await self.cleanup_expired_sessions()
                    self._last_cleanup_time = current_time
                    
                    if cleaned_count > 0:
                        logger.info(f"Periodic cleanup removed {cleaned_count} expired sessions")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
                await asyncio.sleep(3600)  # Wait before retrying
    
    async def _flush_pending_saves(self) -> None:
        """Flush all pending session saves."""
        if not self._pending_saves:
            return
        
        pending_count = len(self._pending_saves)
        logger.debug(f"Flushing {pending_count} pending session saves")
        
        # Note: In a real implementation, we would need access to the actual session data
        # This would require integration with the ADK service to get current session states
        # For now, we just clear the pending saves list
        self._pending_saves.clear()
        
        logger.debug(f"Flushed {pending_count} pending session saves")


# Global service instance
_session_persistence_service: Optional[SessionPersistenceService] = None


async def get_session_persistence_service() -> SessionPersistenceService:
    """Get the global session persistence service instance."""
    global _session_persistence_service
    if _session_persistence_service is None:
        _session_persistence_service = SessionPersistenceService()
        await _session_persistence_service.initialize()
    return _session_persistence_service


async def init_session_persistence_service() -> None:
    """Initialize session persistence service."""
    global _session_persistence_service
    if _session_persistence_service is None:
        _session_persistence_service = SessionPersistenceService()
        await _session_persistence_service.initialize()
    logger.info("Session persistence service initialized")