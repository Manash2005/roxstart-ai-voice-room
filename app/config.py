"""Typed configuration management for Roxstar AI Voice Room Assistant."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class ConfigurationError(ValueError):
    """Raised when one or more required configuration variables are missing or invalid."""


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables and .env file.

    Attributes:
        livekit_url: LiveKit server WebSocket URL (wss://...).
        livekit_api_key: LiveKit API key for room access and worker authentication.
        livekit_api_secret: LiveKit API secret for worker authentication.
        openrouter_api_key: OpenRouter API key for LLM inference.
        openrouter_model: OpenRouter model identifier (default: 'openrouter/free').
        openrouter_base_url: OpenRouter API base URL.
        groq_api_key: Groq Cloud API key for Whisper STT.
        groq_stt_model: Groq Whisper model name (default: 'whisper-large-v3-turbo').
        groq_stt_language: Initial STT language target (default: 'hi' for Hindi/Hinglish).
        log_level: Logging severity level (default: 'INFO').
    """

    # LiveKit credentials
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str

    # OpenRouter LLM configuration
    openrouter_api_key: str
    openrouter_model: str = "openrouter/free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Groq STT configuration
    groq_api_key: str = ""
    groq_stt_model: str = "whisper-large-v3-turbo"
    groq_stt_language: str = "hi"

    # Application settings
    log_level: str = "INFO"

    @classmethod
    def load(cls, env_path: Path | str | None = None) -> Settings:
        """Load and validate settings from environment variables.

        Args:
            env_path: Optional path to a specific .env file to load.

        Returns:
            Settings: Strongly-typed, validated settings instance.

        Raises:
            ConfigurationError: If any required environment variables are unset.
        """
        # Load environment variables from .env file if present
        if env_path:
            load_dotenv(dotenv_path=env_path, override=False)
        else:
            load_dotenv(override=False)

        missing_vars: list[str] = []

        # Validate LiveKit connection parameters
        livekit_url = os.getenv("LIVEKIT_URL", "").strip()
        if not livekit_url:
            missing_vars.append("LIVEKIT_URL")

        livekit_api_key = os.getenv("LIVEKIT_API_KEY", "").strip()
        if not livekit_api_key:
            missing_vars.append("LIVEKIT_API_KEY")

        livekit_api_secret = os.getenv("LIVEKIT_API_SECRET", "").strip()
        if not livekit_api_secret:
            missing_vars.append("LIVEKIT_API_SECRET")

        # Validate OpenRouter LLM parameters
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not openrouter_api_key:
            missing_vars.append("OPENROUTER_API_KEY")

        # Validate Groq STT parameters
        groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not groq_api_key:
            missing_vars.append("GROQ_API_KEY")

        if missing_vars:
            formatted_vars = ", ".join(missing_vars)
            raise ConfigurationError(
                f"Missing required environment variable(s): {formatted_vars}. "
                "Please set them in your environment or create a '.env' file "
                "based on '.env.example'."
            )

        # Optional / Configurable parameters with safe zero-cost defaults
        openrouter_model = (
            os.getenv("OPENROUTER_MODEL", "openrouter/free").strip()
            or "openrouter/free"
        )
        openrouter_base_url = (
            os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
            or "https://openrouter.ai/api/v1"
        )
        groq_stt_model = (
            os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo").strip()
            or "whisper-large-v3-turbo"
        )
        groq_stt_language = os.getenv("GROQ_STT_LANGUAGE", "hi").strip() or "hi"
        log_level = os.getenv("LOG_LEVEL", "INFO").strip() or "INFO"

        return cls(
            livekit_url=livekit_url,
            livekit_api_key=livekit_api_key,
            livekit_api_secret=livekit_api_secret,
            openrouter_api_key=openrouter_api_key,
            openrouter_model=openrouter_model,
            openrouter_base_url=openrouter_base_url,
            groq_api_key=groq_api_key,
            groq_stt_model=groq_stt_model,
            groq_stt_language=groq_stt_language,
            log_level=log_level,
        )


_cached_settings: Settings | None = None


def get_settings(force_reload: bool = False) -> Settings:
    """Retrieve the cached application settings or load them if not initialized.

    Args:
        force_reload: If True, bypasses the cache and reloads settings.

    Returns:
        Settings: The validated application settings.
    """
    global _cached_settings
    if _cached_settings is None or force_reload:
        _cached_settings = Settings.load()
    return _cached_settings
