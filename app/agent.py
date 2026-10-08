"""LiveKit Voice Room Assistant Agent.

Checkpoint 1: Initial production-quality foundation using:
- LiveKit Agents (Realtime RTC agent orchestration)
- Groq Whisper (Zero-cost STT with Hindi/Hinglish support)
- OpenRouter (Zero-cost free-tier LLM)
- TemporaryStubTTS (TTS intentionally deferred to Checkpoint 2 for local/open-source engine)
"""

from __future__ import annotations

from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    cli,
    stt,
)
from livekit.plugins import groq, openai

from app.config import Settings, get_settings
from app.logging import get_logger, setup_logging
from app.tts import create_tts

logger = get_logger(__name__)

# Default system instruction for the assistant in Checkpoint 2
DEFAULT_SYSTEM_INSTRUCTION = (
    "You are a helpful voice assistant. "
    "Understand Hindi, Hinglish, and English. "
    "Respond naturally and conversationally."
)


# ------------------------------------------------------------------------------
# Component Factories (Isolated for easy replacement in future checkpoints)
# ------------------------------------------------------------------------------
def create_stt(settings: Settings) -> stt.STT:
    """Create the Speech-To-Text component using Groq Whisper.

    Isolated configuration to allow switching models or language strategy
    in later checkpoints without modifying the core agent flow.
    """
    logger.info(
        "Initializing Groq STT (model: %s, language: %s)",
        settings.groq_stt_model,
        settings.groq_stt_language,
    )
    return groq.STT(
        model=settings.groq_stt_model,
        language=settings.groq_stt_language,
        api_key=settings.groq_api_key,
    )


def create_llm(settings: Settings) -> openai.LLM:
    """Create the LLM component via OpenRouter with the OpenAI-compatible plugin.

    Configured for zero-cost operation using free-tier models (e.g. openrouter/free).
    """
    logger.info("Initializing OpenRouter LLM (model: %s)", settings.openrouter_model)
    return openai.LLM.with_openrouter(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )


# ------------------------------------------------------------------------------
# Agent Persona Definition
# ------------------------------------------------------------------------------
class VoiceAssistantAgent(Agent):
    """Voice Assistant Agent representing assistant behavior and instructions.

    Inherits from LiveKit's Agent class to encapsulate conversation instructions.
    Multi-persona logic (AI Dost, AI Sathi) and routing will be introduced
    in future checkpoints.
    """

    def __init__(self, instructions: str = DEFAULT_SYSTEM_INSTRUCTION) -> None:
        super().__init__(instructions=instructions)


# ------------------------------------------------------------------------------
# LiveKit Core Flow
#
#   AgentServer  -> Worker process manager listening for LiveKit room dispatches
#       ↓
#   JobContext   -> Context for a specific room job assigned to this worker
#       ↓
#   AgentSession -> Orchestrator connecting STT, LLM, TTS, VAD, and turn detection
#       ↓
#   Agent        -> Defines assistant persona, instructions, and tools
#       ↓
#   STT / LLM / TTS
# ------------------------------------------------------------------------------

# 1. AgentServer: Top-level worker process manager
server = AgentServer()


@server.rtc_session
async def entrypoint(ctx: JobContext) -> None:
    """Main entrypoint for a LiveKit room session.

    Called whenever a worker process is dispatched to handle an active room.
    """
    # Load and validate settings for this job
    settings = get_settings()

    # 2. JobContext: Connect the agent worker to the room
    await ctx.connect()
    logger.info(
        "Connected to LiveKit room: '%s' (Job ID: %s)", ctx.room.name, ctx.job.id
    )

    # 3. Initialize pipeline components
    stt_provider = create_stt(settings)
    llm_provider = create_llm(settings)
    tts_provider = create_tts(settings)

    # 4. Agent: Initialize assistant persona and instructions
    assistant = VoiceAssistantAgent()

    # 5. AgentSession: Realtime voice session orchestrating media streams and models
    session = AgentSession(
        stt=stt_provider,
        llm=llm_provider,
        tts=tts_provider,
    )

    # 6. session.start(): Attach the agent to the room audio/video streams
    logger.info("Starting voice assistant session...")
    await session.start(agent=assistant, room=ctx.room)
    logger.info("Voice assistant session active in room '%s'", ctx.room.name)


def main() -> None:
    """CLI entrypoint for running the LiveKit agent."""
    import sys

    # Allow viewing CLI help without requiring .env credentials to be configured first
    if any(arg in sys.argv for arg in ("--help", "-h")):
        cli.run_app(server)
        return

    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info("Starting Roxstar AI Voice Room Assistant (Checkpoint 1)...")

    # agents.cli.run_app: Standard LiveKit CLI runner supporting 'dev', 'start', etc.
    cli.run_app(server)


if __name__ == "__main__":
    main()
