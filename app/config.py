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
        groq_stt_language: Initial STT language target (default: '' for automatic multilingual recognition).
        log_level: Logging severity level (default: 'INFO').
        active_persona: Active persona to instantiate ('dost' or 'sathi', default: 'dost').
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
    groq_stt_language: str = ""

    # Local TTS configuration (Piper Hindi)
    tts_model: str = "hi_IN-rohan-medium"
    tts_model_path: str = ""
    tts_config_path: str = ""
    tts_device: str = "cpu"
    tts_sample_rate: int = 22050
    tts_auto_download: bool = True

    # Application settings
    log_level: str = "INFO"
    active_persona: str = "dost"

    # API & CORS configuration
    frontend_origin: str = "http://localhost:5173"
    api_host: str = "0.0.0.0"
    api_port: int = 8080

    @property
    def allowed_origins(self) -> list[str]:
        """Return the parsed list of allowed frontend origins for CORS."""
        return [
            origin.strip()
            for origin in self.frontend_origin.split(",")
            if origin.strip()
        ]

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
        # Load environment variables from .env / .env.local file if present
        if env_path:
            load_dotenv(dotenv_path=env_path, override=False)
        else:
            if Path(".env.local").exists():
                load_dotenv(dotenv_path=".env.local", override=False)
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
        groq_stt_language = os.getenv("GROQ_STT_LANGUAGE", "").strip()

        # Local TTS parameters (Piper Hindi/Hinglish)
        tts_model = (
            os.getenv("TTS_MODEL", "hi_IN-rohan-medium").strip() or "hi_IN-rohan-medium"
        )
        tts_model_path = os.getenv("TTS_MODEL_PATH", "").strip()
        tts_config_path = os.getenv("TTS_CONFIG_PATH", "").strip()
        tts_device = os.getenv("TTS_DEVICE", "cpu").strip() or "cpu"

        tts_sample_rate_str = os.getenv("TTS_SAMPLE_RATE", "22050").strip()
        try:
            tts_sample_rate = int(tts_sample_rate_str)
        except ValueError:
            tts_sample_rate = 22050

        tts_auto_download_str = os.getenv("TTS_AUTO_DOWNLOAD", "true").strip().lower()
        tts_auto_download = tts_auto_download_str not in ("0", "false", "no", "off")

        log_level = os.getenv("LOG_LEVEL", "INFO").strip() or "INFO"

        active_persona = os.getenv("ACTIVE_PERSONA", "dost").strip().lower() or "dost"
        if active_persona not in ("dost", "sathi"):
            raise ConfigurationError(
                f"Invalid ACTIVE_PERSONA: '{active_persona}'. "
                "Must be either 'dost' or 'sathi'."
            )

        frontend_origin = (
            os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").strip()
            or "http://localhost:5173"
        )
        api_host = os.getenv("API_HOST", "0.0.0.0").strip() or "0.0.0.0"
        api_port_str = os.getenv("API_PORT", "8080").strip()
        try:
            api_port = int(api_port_str)
        except ValueError:
            api_port = 8080

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
            tts_model=tts_model,
            tts_model_path=tts_model_path,
            tts_config_path=tts_config_path,
            tts_device=tts_device,
            tts_sample_rate=tts_sample_rate,
            tts_auto_download=tts_auto_download,
            log_level=log_level,
            active_persona=active_persona,
            frontend_origin=frontend_origin,
            api_host=api_host,
            api_port=api_port,
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
