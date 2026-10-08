"""Personas package for Roxstar AI Voice Room Assistant."""

from __future__ import annotations

from livekit.agents import Agent

from app.personas.dost import (
    AI_DOST_GREETING,
    AI_DOST_INSTRUCTIONS,
    AIDost,
)
from app.personas.sathi import (
    AI_SATHI_GREETING,
    AI_SATHI_INSTRUCTIONS,
    AISathi,
)


def create_agent(persona: str = "dost") -> Agent:
    """Create an agent instance based on the requested persona identifier.

    Args:
        persona: The persona name ('dost' or 'sathi'). Case-insensitive.

    Returns:
        Agent: An initialized LiveKit Agent persona.

    Raises:
        ValueError: If an unknown persona name is provided.
    """
    normalized = persona.strip().lower()
    if normalized == "dost":
        return AIDost()
    if normalized == "sathi":
        return AISathi()
    raise ValueError(
        f"Unknown persona: '{persona}'. Supported personas are 'dost' and 'sathi'."
    )


def get_persona_greeting(persona: str = "dost") -> str:
    """Retrieve the initial spoken greeting for the specified persona.

    Args:
        persona: The persona name ('dost' or 'sathi'). Case-insensitive.

    Returns:
        str: Spoken greeting text.

    Raises:
        ValueError: If an unknown persona name is provided.
    """
    normalized = persona.strip().lower()
    if normalized == "dost":
        return AI_DOST_GREETING
    if normalized == "sathi":
        return AI_SATHI_GREETING
    raise ValueError(
        f"Unknown persona: '{persona}'. Supported personas are 'dost' and 'sathi'."
    )


__all__ = [
    "AI_DOST_GREETING",
    "AI_DOST_INSTRUCTIONS",
    "AI_SATHI_GREETING",
    "AI_SATHI_INSTRUCTIONS",
    "AIDost",
    "AISathi",
    "create_agent",
    "get_persona_greeting",
]
