"""Unit tests for AI Sathi persona and instructions (Checkpoint 4)."""

import pytest
from livekit.agents import Agent

from app.personas import (
    AI_DOST_GREETING,
    AI_SATHI_GREETING,
    AI_SATHI_INSTRUCTIONS,
    AIDost,
    AISathi,
    create_agent,
    get_persona_greeting,
)


def test_ai_sathi_instantiation():
    """Verify AISathi instantiates properly as a LiveKit Agent."""
    sathi = AISathi()
    assert isinstance(sathi, Agent)
    assert sathi.instructions == AI_SATHI_INSTRUCTIONS
    assert sathi.greeting == AI_SATHI_GREETING


def test_ai_sathi_custom_instructions():
    """Verify AISathi can accept custom instructions if provided."""
    custom_prompt = "Custom analytical instructions for testing."
    sathi = AISathi(instructions=custom_prompt)
    assert sathi.instructions == custom_prompt


def test_ai_sathi_instructions_non_empty_and_substantial():
    """Verify persona instructions are detailed and non-empty."""
    assert isinstance(AI_SATHI_INSTRUCTIONS, str)
    assert len(AI_SATHI_INSTRUCTIONS) > 300


def test_ai_sathi_persona_identity():
    """Verify AI Sathi persona reflects intelligent, calm, composed identity."""
    instructions = AI_SATHI_INSTRUCTIONS.lower()
    assert "ai sathi" in instructions
    assert "calm" in instructions
    assert "analytical" in instructions
    assert "composed" in instructions
    assert "warm" in instructions
    # Prohibitions on corporate/academic clichés
    assert "textbook" in instructions
    assert "customer-service bot" in instructions or "corporate" in instructions


def test_ai_sathi_female_identity():
    """Verify female persona identity is represented without stereotypical tropes."""
    instructions = AI_SATHI_INSTRUCTIONS.lower()
    assert "female" in instructions
    # Anti-stereotype guideline
    assert "stereotypical" in instructions


def test_ai_sathi_multilingual_behavior():
    """Verify multilingual support for Hindi, Hinglish, Roman Hindi, and English."""
    instructions = AI_SATHI_INSTRUCTIONS.lower()
    assert "hindi" in instructions
    assert "hinglish" in instructions
    assert "english" in instructions
    # Technical terminology guidance
    assert "api" in instructions
    assert "technical terms" in instructions or "technical terminology" in instructions


def test_ai_sathi_english_language_matching():
    """Verify that language matching switches to English when user speaks English."""
    instructions = AI_SATHI_INSTRUCTIONS.lower()
    assert "english" in instructions
    assert "language matching" in instructions or "primarily in english" in instructions


def test_ai_sathi_analytical_and_conversational():
    """Verify analytical, logical comparison and clarity guidelines."""
    instructions = AI_SATHI_INSTRUCTIONS.lower()
    assert "analytical" in instructions
    assert "trade-off" in instructions or "trade-offs" in instructions
    assert "clarity" in instructions or "precision" in instructions
    # Avoid academic lecture
    assert "lecture" in instructions or "academic" in instructions


def test_ai_sathi_tts_constraints():
    """Verify critical TTS-friendly constraints (no emojis, no markdown tables/bullets, concise)."""
    instructions = AI_SATHI_INSTRUCTIONS.lower()
    assert "emojis" in instructions
    assert "table" in instructions or "bullet" in instructions
    assert "as an ai" in instructions
    # Short sentence guidance
    assert "1 to 4" in instructions or "short" in instructions


def test_ai_sathi_greeting():
    """Verify initial spoken greeting is distinct, concise, and TTS-ready."""
    assert isinstance(AI_SATHI_GREETING, str)
    assert len(AI_SATHI_GREETING) > 10
    assert len(AI_SATHI_GREETING) < 120  # Keeps TTS initial latency low
    assert "Namaste" in AI_SATHI_GREETING
    assert "Sathi" in AI_SATHI_GREETING


def test_persona_factory_create_agent():
    """Verify persona factory creates correct Agent instances."""
    dost = create_agent("dost")
    assert isinstance(dost, AIDost)

    sathi = create_agent("sathi")
    assert isinstance(sathi, AISathi)

    # Case insensitivity
    assert isinstance(create_agent("DOST"), AIDost)
    assert isinstance(create_agent("Sathi"), AISathi)

    # Invalid persona
    with pytest.raises(ValueError) as exc:
        create_agent("unknown_bot")
    assert "Unknown persona" in str(exc.value)


def test_persona_factory_get_greeting():
    """Verify get_persona_greeting retrieves correct greeting."""
    assert get_persona_greeting("dost") == AI_DOST_GREETING
    assert get_persona_greeting("sathi") == AI_SATHI_GREETING

    with pytest.raises(ValueError):
        get_persona_greeting("unknown_bot")
