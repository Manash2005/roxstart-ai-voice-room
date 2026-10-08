"""Unit tests for LiveKit Voice Room Assistant Agent (Checkpoint 1)."""

import pytest
from livekit.agents import AgentServer, AgentSession
from livekit.plugins import groq, openai

from app.agent import (
    DEFAULT_SYSTEM_INSTRUCTION,
    TemporaryStubTTS,
    VoiceAssistantAgent,
    create_llm,
    create_stt,
    create_tts,
    server,
)
from app.config import Settings


@pytest.fixture
def dummy_settings() -> Settings:
    """Fixture providing dummy settings without making live API calls."""
    return Settings(
        livekit_url="wss://test.livekit.cloud",
        livekit_api_key="test-api-key",
        livekit_api_secret="test-api-secret",
        openrouter_api_key="test-openrouter-key",
        openrouter_model="openrouter/free",
        openrouter_base_url="https://openrouter.ai/api/v1",
        groq_api_key="test-groq-key",
        groq_stt_model="whisper-large-v3-turbo",
        groq_stt_language="hi",
        log_level="DEBUG",
    )


def test_agent_initialization():
    """Verify VoiceAssistantAgent initializes with default system instruction."""
    agent = VoiceAssistantAgent()
    assert agent.instructions == DEFAULT_SYSTEM_INSTRUCTION
    assert "Hindi" in agent.instructions
    assert "Hinglish" in agent.instructions
    assert "English" in agent.instructions


def test_custom_agent_instructions():
    """Verify VoiceAssistantAgent accepts custom instructions."""
    custom = "Custom instruction for testing."
    agent = VoiceAssistantAgent(instructions=custom)
    assert agent.instructions == custom


def test_create_stt_isolated_factory(dummy_settings: Settings):
    """Verify STT factory initializes Groq STT with configured model and language."""
    stt_instance = create_stt(dummy_settings)
    assert isinstance(stt_instance, groq.STT)
    assert stt_instance.model == dummy_settings.groq_stt_model
    assert dummy_settings.groq_stt_language in stt_instance._opts.languages


def test_create_llm_with_openrouter(dummy_settings: Settings):
    """Verify LLM factory initializes OpenRouter via OpenAI plugin with free model."""
    llm_instance = create_llm(dummy_settings)
    assert isinstance(llm_instance, openai.LLM)
    assert llm_instance.model == dummy_settings.openrouter_model


def test_create_tts_returns_temporary_stub():
    """Verify TTS factory returns TemporaryStubTTS for Checkpoint 1."""
    tts_instance = create_tts()
    assert isinstance(tts_instance, TemporaryStubTTS)
    assert tts_instance.capabilities.streaming is False


@pytest.mark.asyncio
async def test_temporary_stub_tts_synthesis():
    """Verify TemporaryStubTTS synthesizes a chunked stream without external API calls."""
    tts_instance = TemporaryStubTTS()
    stream = tts_instance.synthesize("Namaste, kaise hain aap?")
    assert stream is not None
    assert stream.input_text == "Namaste, kaise hain aap?"
    await stream.aclose()


def test_agent_server_instance():
    """Verify module-level AgentServer is correctly instantiated."""
    assert isinstance(server, AgentServer)


@pytest.mark.asyncio
async def test_agent_session_compatibility(dummy_settings: Settings):
    """Verify AgentSession can be composed with our STT, LLM, and TTS instances."""
    stt_inst = create_stt(dummy_settings)
    llm_inst = create_llm(dummy_settings)
    tts_inst = create_tts()

    session = AgentSession(
        stt=stt_inst,
        llm=llm_inst,
        tts=tts_inst,
    )

    assert session.stt is stt_inst
    assert session.tts is tts_inst
    await session.aclose()
