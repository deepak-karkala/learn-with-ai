"""
Configuration service for the application.
Manages environment variables and application settings.
"""

import logging
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Google ADK Configuration (following ADK streaming documentation)
    google_genai_use_vertexai: bool = False
    google_api_key: Optional[str] = None
    google_cloud_project: Optional[str] = None
    google_cloud_location: str = "us-central1"

    # Application Configuration
    debug: bool = False
    log_level: str = "INFO"

    # FastAPI Configuration
    api_title: str = "AI System Design Learning Platform API"
    api_version: str = "0.1.0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


def get_settings() -> Settings:
    """Get application settings instance"""
    return Settings()


def setup_logging(settings: Settings) -> None:
    """Configure logging based on settings"""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
        ],
    )

    # Set specific logger levels
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


# Global settings instance
settings = get_settings()
