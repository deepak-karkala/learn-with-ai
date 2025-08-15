"""
Database configuration and models for the AI System Design Learning Platform.
"""

from .connection import get_database, init_database
from .models import Base, User, LearningSession, Assessment, Progress, Artifact

__all__ = [
    "get_database",
    "init_database", 
    "Base",
    "User",
    "LearningSession",
    "Assessment", 
    "Progress",
    "Artifact"
]