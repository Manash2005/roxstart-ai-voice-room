"""Unit tests for configuration management."""

import os
from unittest.mock import patch

import pytest

from app.config import ConfigurationError, Settings, get_settings


def test_missing_environment_variables_raises_clear_error():
    """Verify that missing required environment variables produce a clear, informative error."""
    with patch.dict(os.environ, {}, clear=True):
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
        assert settings.groq_stt_language == "hi"
        assert settings.tts_model == "hi_IN-rohan-medium"
        assert settings.tts_sample_rate == 22050
        assert settings.tts_device == "cpu"
        assert settings.tts_auto_download is True
        assert settings.log_level == "INFO"


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
