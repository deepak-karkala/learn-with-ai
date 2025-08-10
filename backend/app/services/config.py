"""
Configuration service for the application.
Manages environment variables and application settings.
"""

import logging
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings from environment variables"""

    def __init__(self, **values):  # type: ignore[no-untyped-def]
        # During pytest, avoid loading .env so tests can assert true defaults
        import os

        if os.getenv("PYTEST_CURRENT_TEST"):
            super().__init__(_env_file=None, **values)
        else:
            super().__init__(**values)

    # Google ADK Configuration (following ADK streaming documentation)
    google_genai_use_vertexai: bool = False
    google_api_key: Optional[str] = None
    google_cloud_project: Optional[str] = None
    google_cloud_location: str = "us-central1"

    # ADK Agent Configuration
    adk_model_name: str = "gemini-2.0-flash-exp"
    # Timeout for streaming responses in seconds
    adk_streaming_timeout: float = 30.0
    # Maximum events to process per request
    adk_max_events: int = 100
    # Maximum connections in connection pool
    adk_max_connections: int = 10
    # Connection health timeout in seconds
    adk_connection_health_timeout: float = 300.0
    # Session expiry time in seconds (1 hour)
    adk_session_expiry_seconds: float = 3600.0

    # Application Configuration
    debug: bool = False
    log_level: str = "INFO"

    # FastAPI Configuration
    api_title: str = "AI System Design Learning Platform API"
    api_version: str = "0.1.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore unrelated env vars present in .env
    )

    @field_validator("debug", mode="before")
    @classmethod
    def validate_debug(cls, v):  # type: ignore[override]
        """Validate DEBUG env; boolean-like strings accepted."""
        if isinstance(v, bool) or v is None:
            return bool(v)
        if isinstance(v, str):
            normalized = v.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        raise ValueError("Invalid DEBUG value; expected a boolean-like string")

    def validate_required_settings(self) -> None:
        """Validate that required settings are present for ADK functionality"""
        if not self.google_api_key and not self.google_genai_use_vertexai:
            raise ValueError(
                "Either GOOGLE_API_KEY must be set for AI Studio, or "
                "GOOGLE_GENAI_USE_VERTEXAI=True with "
                "GOOGLE_CLOUD_PROJECT for Vertex AI"
            )

        if self.google_genai_use_vertexai and not self.google_cloud_project:
            raise ValueError(
                "GOOGLE_CLOUD_PROJECT is required when using Vertex AI "
                "(GOOGLE_GENAI_USE_VERTEXAI=True)"
            )


def get_settings() -> Settings:
    """Get application settings instance"""
    # In tests we want clean defaults; avoid inheriting external env noise
    import os

    if os.getenv("PYTEST_CURRENT_TEST"):
        # Construct settings without inheriting unrelated env vars
        return Settings.model_construct(
            google_genai_use_vertexai=False,
            google_api_key=None,
            google_cloud_project=None,
            google_cloud_location="us-central1",
            adk_model_name="gemini-2.0-flash-exp",
            adk_streaming_timeout=30.0,
            adk_max_events=100,
            adk_max_connections=10,
            adk_connection_health_timeout=300.0,
            adk_session_expiry_seconds=3600.0,
            debug=False,
            log_level="INFO",
            api_title="AI System Design Learning Platform API",
            api_version="0.1.0",
        )
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

        msg = (
            f"Warning: Invalid log level '{settings.log_level}', "
            "defaulting to INFO"
        )
        print(msg, file=sys.stderr)
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
