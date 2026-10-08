"""Unit tests for PiperTTS adapter (Checkpoint 2)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from livekit.agents import tts

from app.config import Settings
from app.tts import PiperTTS, create_tts


class MockPiperVoice:
    """Mock PiperVoice avoiding disk/network model download during unit tests."""

    def __init__(self, sample_rate: int = 22050) -> None:
        self.config = MagicMock()
        self.config.sample_rate = sample_rate

    def synthesize(self, text: str):
        # Generate 0.5s of dummy int16 audio (22050 * 0.5 * 2 = 22050 bytes)
        num_samples = int(self.config.sample_rate * 0.5)
        dummy_pcm = b"\x01\x00" * num_samples
        chunk = MagicMock()
        chunk.audio_int16_bytes = dummy_pcm
        yield chunk


@pytest.fixture
def mock_piper_voice() -> MockPiperVoice:
    return MockPiperVoice(sample_rate=22050)


def test_piper_tts_initialization(mock_piper_voice: MockPiperVoice):
    """Verify PiperTTS initializes with correct sample rate and LiveKit capabilities."""
    adapter = PiperTTS(
        model_name="hi_IN-rohan-medium",
        sample_rate=22050,
        voice_instance=mock_piper_voice,
        auto_download=False,
    )

    assert adapter.model_name == "hi_IN-rohan-medium"
    assert adapter.sample_rate == 22050
    assert adapter.num_channels == 1
    assert adapter.capabilities.streaming is False


@pytest.mark.asyncio
async def test_piper_tts_synthesis_flow(mock_piper_voice: MockPiperVoice):
    """Verify PiperTTS synthesizes audio chunks into LiveKit audio frames."""
    adapter = PiperTTS(
        model_name="hi_IN-rohan-medium",
        sample_rate=22050,
        voice_instance=mock_piper_voice,
        auto_download=False,
    )

    stream = adapter.synthesize("नमस्ते! आज आप कैसे हैं?")
    assert stream is not None
    assert stream.input_text == "नमस्ते! आज आप कैसे हैं?"

    frames = []
    async for ev in stream:
        frames.append(ev.frame)

    assert len(frames) > 0
    # Combined duration should be approximately 0.5 seconds
    total_duration = sum(f.duration for f in frames)
    assert 0.45 <= total_duration <= 0.55
    await stream.aclose()


@pytest.mark.asyncio
async def test_piper_tts_empty_text_handling(mock_piper_voice: MockPiperVoice):
    """Verify empty or whitespace strings are handled gracefully without error."""
    adapter = PiperTTS(
        model_name="hi_IN-rohan-medium",
        sample_rate=22050,
        voice_instance=mock_piper_voice,
        auto_download=False,
    )

    stream = adapter.synthesize("   ")
    frames = []
    async for ev in stream:
        frames.append(ev.frame)

    assert len(frames) == 0
    await stream.aclose()


@pytest.mark.asyncio
async def test_piper_tts_error_handling():
    """Verify synthesis failures raise useful exceptions."""
    faulty_voice = MagicMock()
    faulty_voice.config.sample_rate = 22050
    faulty_voice.synthesize.side_effect = RuntimeError("ONNX inference failed")

    adapter = PiperTTS(
        model_name="hi_IN-rohan-medium",
        sample_rate=22050,
        voice_instance=faulty_voice,
        auto_download=False,
    )

    stream = adapter.synthesize("Valid sentence")
    with pytest.raises(RuntimeError):
        async for _ in stream:
            pass
    await stream.aclose()


def test_create_tts_factory():
    """Verify create_tts factory constructs a PiperTTS instance."""
    settings = Settings(
        livekit_url="wss://test.livekit.cloud",
        livekit_api_key="k",
        livekit_api_secret="s",
        openrouter_api_key="sk-or",
        groq_api_key="gsk",
        tts_model="hi_IN-rohan-medium",
        tts_sample_rate=22050,
        tts_auto_download=False,
    )

    tts_instance = create_tts(settings)
    assert isinstance(tts_instance, PiperTTS)
    assert isinstance(tts_instance, tts.TTS)
    assert tts_instance.model_name == "hi_IN-rohan-medium"
    assert tts_instance.sample_rate == 22050
