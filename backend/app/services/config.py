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

    # ADK Agent Configuration
    adk_model_name: str = "gemini-2.0-flash-exp"

    # Application Configuration
    debug: bool = False
    log_level: str = "INFO"

    # FastAPI Configuration
    api_title: str = "AI System Design Learning Platform API"
    api_version: str = "0.1.0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def validate_required_settings(self) -> None:
        """Validate that required settings are present for ADK functionality"""
        if not self.google_api_key and not self.google_genai_use_vertexai:
            raise ValueError(
                "Either GOOGLE_API_KEY must be set for AI Studio, or "
                "GOOGLE_GENAI_USE_VERTEXAI=True with GOOGLE_CLOUD_PROJECT for Vertex AI"
            )

        if self.google_genai_use_vertexai and not self.google_cloud_project:
            raise ValueError(
                "GOOGLE_CLOUD_PROJECT is required when using Vertex AI "
                "(GOOGLE_GENAI_USE_VERTEXAI=True)"
            )


def get_settings() -> Settings:
    """Get application settings instance"""
    return Settings()


def setup_logging(settings: Settings) -> None:
    """Configure logging based on settings"""
    # Validate log level to prevent log injection and AttributeError
    valid_log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    log_level_upper = settings.log_level.upper().strip()
    if log_level_upper not in valid_log_levels:
        # Default to INFO if invalid level provided
        log_level = logging.INFO
        # Use stderr for early warnings before logging is configured
        import sys
        print(f"Warning: Invalid log level '{settings.log_level}', defaulting to INFO", file=sys.stderr)
    else:
        log_level = valid_log_levels[log_level_upper]

    logging.basicConfig(
        level=log_level,
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
