"""
SQLAlchemy models for the AI System Design Learning Platform.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import (
    Column, String, DateTime, Text, JSON, Integer, 
    Float, Boolean, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .connection import Base


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    skill_level = Column(String(50), default="intermediate")  # beginner, intermediate, advanced
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now())
    
    # User preferences and settings
    preferences = Column(JSON, default=dict)
    
    # Relationships
    sessions = relationship("LearningSession", back_populates="user", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("Progress", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_created_at", "created_at"),
        Index("idx_users_last_active", "last_active"),
    )


class LearningSession(Base):
    """Learning session model for tracking user interactions."""
    
    __tablename__ = "learning_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session metadata
    chapter_id = Column(String(100), nullable=True)  # e.g., "twitter-design"
    status = Column(String(50), default="active")  # active, completed, paused, abandoned
    
    # Session data
    conversation_history = Column(JSON, default=list)
    session_state = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Session metrics
    total_duration_seconds = Column(Integer, default=0)
    message_count = Column(Integer, default=0)
    whiteboard_interactions = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    assessments = relationship("Assessment", back_populates="session", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="session", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_sessions_user_id", "user_id"),
        Index("idx_sessions_status", "status"),
        Index("idx_sessions_created_at", "created_at"),
        Index("idx_sessions_chapter_id", "chapter_id"),
    )


class Assessment(Base):
    """Assessment model for storing LLM judge evaluations."""
    
    __tablename__ = "assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("learning_sessions.id"), nullable=False)
    
    # Assessment scores (1-5 scale)
    requirements_analysis = Column(Float, nullable=False)
    system_architecture = Column(Float, nullable=False)
    technical_deep_dive = Column(Float, nullable=False)
    scale_performance = Column(Float, nullable=False)
    reliability_fault_tolerance = Column(Float, nullable=False)
    communication_thought_process = Column(Float, nullable=False)
    
    # Overall metrics
    overall_score = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    
    # Assessment data
    detailed_feedback = Column(JSON, nullable=False)
    interaction_context = Column(Text, nullable=True)
    whiteboard_analysis = Column(JSON, nullable=True)
    
    # Metadata
    assessment_version = Column(String(20), default="1.0")
    model_used = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="assessments")
    session = relationship("LearningSession", back_populates="assessments")
    
    # Indexes
    __table_args__ = (
        Index("idx_assessments_user_id", "user_id"),
        Index("idx_assessments_session_id", "session_id"),
        Index("idx_assessments_created_at", "created_at"),
        Index("idx_assessments_overall_score", "overall_score"),
    )


class Progress(Base):
    """Progress tracking model for user analytics."""
    
    __tablename__ = "progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Progress timeline data
    timeline_data = Column(JSON, default=list)
    
    # Trend analysis
    trends = Column(JSON, default=dict)
    
    # Recommendations
    recommendations = Column(JSON, default=list)
    
    # Achievement tracking
    achievements = Column(JSON, default=list)
    
    # Goal setting
    goals = Column(JSON, default=list)
    
    # Statistics
    total_sessions = Column(Integer, default=0)
    total_assessments = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)
    improvement_rate = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="progress")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_progress_user_id"),
        Index("idx_progress_user_id", "user_id"),
        Index("idx_progress_updated_at", "updated_at"),
    )


class Artifact(Base):
    """Artifact model for storing session artifacts (whiteboards, diagrams, etc.)."""
    
    __tablename__ = "artifacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("learning_sessions.id"), nullable=False)
    
    # Artifact metadata
    artifact_type = Column(String(50), nullable=False)  # whiteboard, diagram, chat_export
    artifact_name = Column(String(255), nullable=True)
    
    # Storage information
    storage_url = Column(String(500), nullable=True)  # GCS URL or local path
    content_data = Column(JSON, nullable=True)  # Direct content storage for small artifacts
    
    # File metadata
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA-256 hash for deduplication
    
    # Analysis results
    analysis_results = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    session = relationship("LearningSession", back_populates="artifacts")
    
    # Indexes
    __table_args__ = (
        Index("idx_artifacts_session_id", "session_id"),
        Index("idx_artifacts_type", "artifact_type"),
        Index("idx_artifacts_created_at", "created_at"),
        Index("idx_artifacts_file_hash", "file_hash"),
    )


class SystemMetric(Base):
    """System metrics for monitoring and observability."""
    
    __tablename__ = "system_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric metadata
    metric_name = Column(String(100), nullable=False)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram
    
    # Metric data
    value = Column(Float, nullable=False)
    labels = Column(JSON, default=dict)
    
    # Cost tracking
    api_costs = Column(JSON, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index("idx_metrics_name", "metric_name"),
        Index("idx_metrics_type", "metric_type"),
        Index("idx_metrics_timestamp", "timestamp"),
    )


class FeatureFlag(Base):
    """Feature flags for A/B testing and feature rollouts."""
    
    __tablename__ = "feature_flags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Flag metadata
    flag_name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Flag configuration
    is_enabled = Column(Boolean, default=False)
    rollout_percentage = Column(Float, default=0.0)
    target_users = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index("idx_feature_flags_name", "flag_name"),
        Index("idx_feature_flags_enabled", "is_enabled"),
    )