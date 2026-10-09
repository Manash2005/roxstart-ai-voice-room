"""Unit tests for configuration management."""

import os
from unittest.mock import patch

import pytest

from app.config import ConfigurationError, Settings, get_settings


def test_missing_environment_variables_raises_clear_error():
    """Verify that missing required environment variables produce a clear, informative error."""
    with patch.dict(os.environ, {}, clear=True), patch("app.config.load_dotenv"):
        with pytest.raises(ConfigurationError) as exc_info:
            Settings.load()

        error_message = str(exc_info.value)
        assert "Missing required environment variable(s)" in error_message
        assert "LIVEKIT_URL" in error_message
        assert "LIVEKIT_API_KEY" in error_message
        assert "LIVEKIT_API_SECRET" in error_message
        assert "OPENROUTER_API_KEY" in error_message
        assert "GROQ_API_KEY" in error_message
        assert ".env.example" in error_message


def test_valid_settings_loading_with_defaults():
    """Verify settings load properly with zero-cost defaults when all required vars are provided."""
    env = {
        "LIVEKIT_URL": "wss://test.livekit.cloud",
        "LIVEKIT_API_KEY": "devkey",
        "LIVEKIT_API_SECRET": "secret123",
        "OPENROUTER_API_KEY": "sk-or-v1-test",
        "GROQ_API_KEY": "gsk_test123",
    }
    with patch.dict(os.environ, env, clear=True):
        settings = Settings.load()

        assert settings.livekit_url == "wss://test.livekit.cloud"
        assert settings.livekit_api_key == "devkey"
        assert settings.livekit_api_secret == "secret123"
        assert settings.openrouter_api_key == "sk-or-v1-test"
        assert settings.openrouter_model == "openrouter/free"
        assert settings.openrouter_base_url == "https://openrouter.ai/api/v1"
        assert settings.groq_api_key == "gsk_test123"
        assert settings.groq_stt_model == "whisper-large-v3-turbo"
        assert settings.groq_stt_language == ""
        assert settings.tts_model == "hi_IN-rohan-medium"
        assert settings.tts_sample_rate == 22050
        assert settings.tts_device == "cpu"
        assert settings.tts_auto_download is True
        assert settings.log_level == "INFO"
        assert settings.active_persona == "dost"
        assert settings.frontend_origin == "http://localhost:5173"
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8080
        assert settings.allowed_origins == ["http://localhost:5173"]


def test_settings_custom_overrides():
    """Verify that optional settings can be overridden via environment variables."""
    env = {
        "LIVEKIT_URL": "wss://custom.livekit.cloud",
        "LIVEKIT_API_KEY": "key",
        "LIVEKIT_API_SECRET": "secret",
        "OPENROUTER_API_KEY": "sk-test",
        "OPENROUTER_MODEL": "meta-llama/llama-3.3-70b-instruct:free",
        "OPENROUTER_BASE_URL": "https://custom.openrouter.ai/api/v1",
        "GROQ_API_KEY": "groq-key",
        "GROQ_STT_MODEL": "whisper-large-v3",
        "GROQ_STT_LANGUAGE": "hi-IN",
        "TTS_MODEL": "hi_IN-pratham-medium",
        "TTS_SAMPLE_RATE": "16000",
        "TTS_DEVICE": "cpu",
        "TTS_AUTO_DOWNLOAD": "false",
        "LOG_LEVEL": "DEBUG",
        "ACTIVE_PERSONA": "sathi",
        "FRONTEND_ORIGIN": "https://app.roxstar.ai, http://localhost:3000",
        "API_HOST": "127.0.0.1",
        "API_PORT": "9000",
    }
    with patch.dict(os.environ, env, clear=True):
        settings = Settings.load()

        assert settings.openrouter_model == "meta-llama/llama-3.3-70b-instruct:free"
        assert settings.openrouter_base_url == "https://custom.openrouter.ai/api/v1"
        assert settings.groq_stt_model == "whisper-large-v3"
        assert settings.groq_stt_language == "hi-IN"
        assert settings.tts_model == "hi_IN-pratham-medium"
        assert settings.tts_sample_rate == 16000
        assert settings.tts_auto_download is False
        assert settings.log_level == "DEBUG"
        assert settings.active_persona == "sathi"
        assert (
            settings.frontend_origin == "https://app.roxstar.ai, http://localhost:3000"
        )
        assert settings.api_host == "127.0.0.1"
        assert settings.api_port == 9000
        assert settings.allowed_origins == [
            "https://app.roxstar.ai",
            "http://localhost:3000",
        ]


def test_render_port_environment_variable():
    """Verify that cloud provider PORT env variable is respected for Render/Heroku deployments."""
    env = {
        "LIVEKIT_URL": "wss://test.livekit.cloud",
        "LIVEKIT_API_KEY": "key",
        "LIVEKIT_API_SECRET": "secret",
        "OPENROUTER_API_KEY": "sk-test",
        "GROQ_API_KEY": "groq-key",
        "PORT": "10000",
    }
    with patch.dict(os.environ, env, clear=True):
        settings = Settings.load()
        assert settings.api_port == 10000


def test_invalid_active_persona_raises_configuration_error():
    """Verify that an unsupported ACTIVE_PERSONA value raises ConfigurationError."""
    env = {
        "LIVEKIT_URL": "wss://test.livekit.cloud",
        "LIVEKIT_API_KEY": "k",
        "LIVEKIT_API_SECRET": "s",
        "OPENROUTER_API_KEY": "or-k",
        "GROQ_API_KEY": "g-k",
        "ACTIVE_PERSONA": "unsupported_robot",
    }
    with patch.dict(os.environ, env, clear=True):
        with pytest.raises(ConfigurationError) as exc_info:
            Settings.load()
        assert "Invalid ACTIVE_PERSONA" in str(exc_info.value)
        assert "unsupported_robot" in str(exc_info.value)


def test_get_settings_caching_and_reload():
    """Verify get_settings caches instance and reloads when requested."""
    env = {
        "LIVEKIT_URL": "wss://test.livekit.cloud",
        "LIVEKIT_API_KEY": "k",
        "LIVEKIT_API_SECRET": "s",
        "OPENROUTER_API_KEY": "or-k",
        "GROQ_API_KEY": "g-k",
    }
    with patch.dict(os.environ, env, clear=True):
        s1 = get_settings(force_reload=True)
        s2 = get_settings()
        assert s1 is s2

        s3 = get_settings(force_reload=True)
        assert s3 is not None
