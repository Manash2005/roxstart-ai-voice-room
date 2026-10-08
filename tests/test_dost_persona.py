"""Unit tests for AI Dost persona and instructions (Checkpoint 3)."""

from livekit.agents import Agent

from app.personas import (
    AI_DOST_GREETING,
    AI_DOST_INSTRUCTIONS,
    AIDost,
)


def test_ai_dost_instantiation():
    """Verify AIDost instantiates properly as a LiveKit Agent."""
    dost = AIDost()
    assert isinstance(dost, Agent)
    assert dost.instructions == AI_DOST_INSTRUCTIONS


def test_ai_dost_custom_instructions():
    """Verify AIDost can accept custom instructions if provided."""
    custom_prompt = "Custom instructions for testing."
    dost = AIDost(instructions=custom_prompt)
    assert dost.instructions == custom_prompt


def test_ai_dost_instructions_non_empty_and_substantial():
    """Verify persona instructions are detailed and non-empty."""
    assert isinstance(AI_DOST_INSTRUCTIONS, str)
    assert len(AI_DOST_INSTRUCTIONS) > 300


def test_ai_dost_core_identity_and_personality():
    """Verify AI Dost persona reflects Indian friendliness rather than a corporate bot."""
    instructions = AI_DOST_INSTRUCTIONS.lower()
    assert "ai dost" in instructions
    assert "friend" in instructions
    # Prohibitions on robotic corporate persona
    assert "textbook" in instructions
    assert "corporate" in instructions


def test_ai_dost_multilingual_and_hinglish_behavior():
    """Verify multilingual support for Hindi, Hinglish, and English."""
    instructions = AI_DOST_INSTRUCTIONS.lower()
    assert "hindi" in instructions
    assert "hinglish" in instructions
    assert "english" in instructions
    # Technical terminology guidance
    assert "technical terms" in instructions or "terms" in instructions
    assert "api" in instructions


def test_ai_dost_spoken_voice_and_tts_constraints():
    """Verify critical TTS-friendly constraints (no emojis, no markdown tables/bullets, concise)."""
    instructions = AI_DOST_INSTRUCTIONS.lower()
    assert "emojis" in instructions
    assert "table" in instructions or "bullet" in instructions
    assert "as an ai" in instructions
    # Short sentence guidance
    assert "1 to 4" in instructions or "short" in instructions


def test_ai_dost_greeting():
    """Verify initial spoken greeting is warm, concise, and TTS-ready."""
    assert isinstance(AI_DOST_GREETING, str)
    assert len(AI_DOST_GREETING) > 10
    assert len(AI_DOST_GREETING) < 120  # Keeps TTS initial latency low
    assert "Namaste" in AI_DOST_GREETING
    assert "Dost" in AI_DOST_GREETING
