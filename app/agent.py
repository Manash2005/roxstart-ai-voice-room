"""LiveKit Voice Room Assistant Agent.

Checkpoint 1: Initial production-quality foundation using:
- LiveKit Agents (Realtime RTC agent orchestration)
- Groq Whisper (Zero-cost STT with Hindi/Hinglish support)
- OpenRouter (Zero-cost free-tier LLM)
- TemporaryStubTTS (TTS intentionally deferred to Checkpoint 2 for local/open-source engine)
"""

from __future__ import annotations

import asyncio
from typing import Any

from livekit import rtc
from livekit.agents import (
    AgentServer,
    AgentSession,
    AgentStateChangedEvent,
    JobContext,
    JobRequest,
    UserStateChangedEvent,
    cli,
    llm,
    stt,
)
from livekit.agents.voice import ConversationItemAddedEvent, room_io
from livekit.agents.voice.room_io import TextInputEvent
from livekit.plugins import groq, openai

from app.config import Settings, get_settings
from app.logging import get_logger, setup_logging
from app.memory import ConversationMemory
from app.personas import (
    AI_DOST_GREETING,
    AI_DOST_INSTRUCTIONS,
    AI_SATHI_GREETING,
    create_agent,
)
from app.routing import (
    BotTarget,
    TwoBotOrchestrator,
    connect_secondary_participant,
    disconnect_secondary_participant,
)
from app.tts import create_tts

logger = get_logger(__name__)

# Backward-compatible aliases for prior checkpoint references
VoiceAssistantAgent = TwoBotOrchestrator
DEFAULT_SYSTEM_INSTRUCTION = AI_DOST_INSTRUCTIONS

__all__ = [
    "DEFAULT_SYSTEM_INSTRUCTION",
    "VoiceAssistantAgent",
    "create_agent",
    "create_llm",
    "create_stt",
    "entrypoint",
    "main",
    "on_request",
    "server",
]


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
# LiveKit Dual-Participant Flow (Checkpoint 5A)
#
#   AgentServer  -> Worker process manager listening for LiveKit room dispatches
#       ↓
#   JobContext   -> Dispatched primary connection (identity: "ai-dost", name: "AI Dost")
#       ├── Receives human audio -> Groq Whisper STT -> TurnRouter -> ResponseArbitrator
#       ↓
#   Secondary Room -> Programmatic connection (identity: "ai-sathi", name: "AI Sathi")
#       └── Output-only session (audio_enabled=False), activated on-demand
# ------------------------------------------------------------------------------

# 1. AgentServer: Top-level worker process manager
server = AgentServer()


async def on_request(req: JobRequest) -> None:
    """Accept the job request specifying primary identity 'ai-dost' and display name 'AI Dost'."""
    await req.accept(identity="ai-dost", name="AI Dost")


@server.rtc_session(on_request=on_request)
async def entrypoint(ctx: JobContext) -> None:
    """Main entrypoint for a LiveKit room session.

    Establishes two genuine LiveKit AI participants (AI Dost and AI Sathi) in the room.
    """
    # Load and validate settings for this job
    settings = get_settings()

    # 2. Connect primary worker participant (AI Dost)
    await ctx.connect()
    logger.info(
        "Primary participant connected to LiveKit room: '%s' (Job ID: %s, SID: %s)",
        ctx.room.name,
        ctx.job.id,
        getattr(ctx.room.local_participant, "sid", "unknown"),
    )

    # Ensure primary participant metadata reflects identity "ai-dost"
    if ctx.room and ctx.room.local_participant:
        try:
            await ctx.room.local_participant.set_name("AI Dost")
            await ctx.room.local_participant.set_attributes(
                {
                    "active_bot": "ai-dost",
                    "available_bots": "ai-dost,ai-sathi",
                    "participant_role": "primary_voice_assistant",
                }
            )
        except (RuntimeError, TimeoutError, asyncio.CancelledError) as e:
            logger.debug("Primary participant metadata setup skipped: %s", e)

    # 3. Connect secondary participant (AI Sathi) to the same room
    sathi_room = None
    try:
        sathi_room = await connect_secondary_participant(
            livekit_url=settings.livekit_url,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
            room_name=ctx.room.name,
            identity="ai-sathi",
            name="AI Sathi",
            auto_subscribe=False,
        )
    except (RuntimeError, TimeoutError, ConnectionError, OSError) as e:
        logger.error("Failed to connect secondary participant 'AI Sathi': %s", e)
        sathi_room = None

    # Register cleanup callback for the secondary participant room on job shutdown
    async def _cleanup_secondary_participant() -> None:
        if sathi_room is not None:
            logger.info("Cleaning up secondary AI Sathi room connection...")
            await disconnect_secondary_participant(sathi_room)

    ctx.add_shutdown_callback(_cleanup_secondary_participant)

    # 4. Initialize shared/isolated pipeline components
    stt_provider = create_stt(settings)
    llm_dost = create_llm(settings)
    tts_dost = create_tts(settings)

    # 5. Initialize secondary AgentSession for AI Sathi (output-only)
    session_sathi: AgentSession | None = None
    if sathi_room is not None:
        try:
            llm_sathi = create_llm(settings)
            tts_sathi = create_tts(settings)
            session_sathi = AgentSession(
                llm=llm_sathi,
                tts=tts_sathi,
            )
            sathi_agent = create_agent(persona="sathi")
            sathi_input_opts = room_io.RoomInputOptions(
                audio_enabled=False,
                text_enabled=False,
            )
            await session_sathi.start(
                agent=sathi_agent,
                room=sathi_room,
                room_input_options=sathi_input_opts,
            )
            logger.info(
                "AI Sathi session started (output-only mode, audio_enabled=False)."
            )
        except (RuntimeError, TimeoutError, ValueError, OSError) as e:
            logger.error("Failed to start AI Sathi agent session: %s", e)
            session_sathi = None

    # 6. Initialize shared session ConversationMemory (Checkpoint 6)
    memory = ConversationMemory(max_turns=12)

    async def _cleanup_memory() -> None:
        logger.info("Clearing shared conversation memory on session shutdown...")
        memory.clear()

    ctx.add_shutdown_callback(_cleanup_memory)

    # 7. Initialize central TwoBotOrchestrator
    default_target: BotTarget = (
        "sathi" if settings.active_persona == "sathi" else "dost"
    )
    orchestrator = TwoBotOrchestrator(
        room=ctx.room,
        sathi_session=session_sathi,
        memory=memory,
        default_target=default_target,
    )

    # 8. Initialize primary AgentSession for AI Dost
    session_dost = AgentSession(
        stt=stt_provider,
        llm=llm_dost,
        tts=tts_dost,
    )
    orchestrator.set_primary_session(session_dost)

    # Wire arbitration release when speech concludes on either bot
    @session_dost.on("agent_state_changed")
    def _on_dost_state_changed(ev: AgentStateChangedEvent) -> None:
        if (
            ev.new_state in ("idle", "listening")
            and orchestrator.arbitrator.current_owner == "dost"
        ):
            logger.info("Dost speech concluded; releasing arbitration lock")
            orchestrator.arbitrator.release("dost")

    if session_sathi is not None:

        @session_sathi.on("agent_state_changed")
        def _on_sathi_state_changed(ev: AgentStateChangedEvent) -> None:
            if (
                ev.new_state in ("idle", "listening")
                and orchestrator.arbitrator.current_owner == "sathi"
            ):
                logger.info("Sathi speech concluded; releasing arbitration lock")
                orchestrator.arbitrator.release("sathi")

    # Wire user speaking listener to interrupt Sathi immediately on barge-in
    @session_dost.on("user_state_changed")
    def _on_user_state_changed(ev: UserStateChangedEvent) -> None:
        if (
            ev.new_state == "speaking"
            and session_sathi is not None
            and orchestrator.arbitrator.current_owner == "sathi"
        ):
            logger.info("User speaking while Sathi is active; interrupting Sathi")
            try:
                session_sathi.interrupt()
            except (RuntimeError, TimeoutError, asyncio.CancelledError) as e:
                logger.debug("Sathi interrupt error: %s", e)
            orchestrator.arbitrator.release("sathi")

    # Record bot turns in shared ConversationMemory on generation completion
    @session_dost.on("conversation_item_added")
    def _on_dost_item_added(ev: ConversationItemAddedEvent) -> None:
        try:
            if isinstance(ev.item, llm.ChatMessage) and ev.item.role == "assistant":
                text = ev.item.text_content
                if text and text.strip():
                    logger.info(
                        "Recorded AI Dost response in shared memory: '%.40s...'", text
                    )
                    memory.add_bot_turn(
                        bot_id="ai-dost",
                        bot_name="AI Dost",
                        text=text,
                        input_type="voice",
                    )
        except (RuntimeError, ValueError, KeyError) as e:
            logger.warning("Error storing AI Dost turn in memory: %s", e)

    if session_sathi is not None:

        @session_sathi.on("conversation_item_added")
        def _on_sathi_item_added(ev: ConversationItemAddedEvent) -> None:
            try:
                if isinstance(ev.item, llm.ChatMessage) and ev.item.role == "assistant":
                    text = ev.item.text_content
                    if text and text.strip():
                        logger.info(
                            "Recorded AI Sathi response in shared memory: '%.40s...'",
                            text,
                        )
                        memory.add_bot_turn(
                            bot_id="ai-sathi",
                            bot_name="AI Sathi",
                            text=text,
                            input_type="voice",
                        )
            except (RuntimeError, ValueError, KeyError) as e:
                logger.warning("Error storing AI Sathi turn in memory: %s", e)

    # Multi-human dynamic ear switching: dynamically follow active human speaker
    @ctx.room.on("active_speakers_changed")
    def _on_active_speakers_changed(speakers: list[rtc.Participant]) -> None:
        try:
            human_speakers = [
                s
                for s in speakers
                if s.identity not in ("ai-dost", "ai-sathi")
                and getattr(s, "kind", None)
                != rtc.ParticipantKind.PARTICIPANT_KIND_AGENT
            ]
            if not human_speakers:
                return

            active_human = human_speakers[0]
            if hasattr(session_dost, "room_io") and session_dost.room_io is not None:
                linked = getattr(session_dost.room_io, "linked_participant", None)
                if (
                    linked is None
                    or getattr(linked, "identity", None) != active_human.identity
                ):
                    logger.info(
                        "Switching primary ear to active human speaker: %s (%s)",
                        getattr(active_human, "name", None) or active_human.identity,
                        active_human.identity,
                    )
                    session_dost.room_io.set_participant(active_human.identity)
        except (RuntimeError, AttributeError, ValueError) as e:
            logger.warning("Error switching active speaker: %s", e)

    @ctx.room.on("participant_connected")
    def _on_participant_connected(p: rtc.RemoteParticipant) -> None:
        try:
            if (
                p.identity not in ("ai-dost", "ai-sathi")
                and getattr(p, "kind", None)
                != rtc.ParticipantKind.PARTICIPANT_KIND_AGENT
                and hasattr(session_dost, "room_io")
                and session_dost.room_io is not None
                and session_dost.room_io.linked_participant is None
            ):
                logger.info(
                    "Linking primary ear to newly connected human: %s (%s)",
                    p.name,
                    p.identity,
                )
                session_dost.room_io.set_participant(p.identity)
        except (RuntimeError, AttributeError, ValueError) as e:
            logger.debug("Participant connect handler error: %s", e)

    @ctx.room.on("participant_disconnected")
    def _on_participant_disconnected(p: rtc.RemoteParticipant) -> None:
        try:
            if hasattr(session_dost, "room_io") and session_dost.room_io is not None:
                linked = session_dost.room_io.linked_participant
                if linked and getattr(linked, "identity", None) == p.identity:
                    remotes = [
                        rp
                        for rp in ctx.room.remote_participants.values()
                        if rp.identity not in ("ai-dost", "ai-sathi")
                        and getattr(rp, "kind", None)
                        != rtc.ParticipantKind.PARTICIPANT_KIND_AGENT
                        and rp.identity != p.identity
                    ]
                    if remotes:
                        session_dost.room_io.set_participant(remotes[0].identity)
                    else:
                        session_dost.room_io.unset_participant()
        except (RuntimeError, AttributeError, ValueError) as e:
            logger.debug("Participant disconnect handler error: %s", e)

    # Unified voice + text input handler
    async def _on_text_input(sess: AgentSession, ev: TextInputEvent) -> None:
        try:
            raw_text = (ev.text or "").strip()
            if not raw_text:
                return

            participant = ev.participant
            if participant is not None:
                speaker_id = getattr(participant, "identity", None) or "human-text"
                speaker_name = getattr(participant, "name", None) or speaker_id
            else:
                speaker_id = "human-text"
                speaker_name = "User"

            decision = orchestrator.router.route(raw_text)
            logger.info(
                "Text turn received | speaker: '%s' (%s) | text: '%s' | selected_bot: %s",
                speaker_name,
                speaker_id,
                decision.cleaned_text,
                decision.target,
            )

            # Record human turn into unified shared memory
            memory.add_human_turn(
                speaker_id=speaker_id,
                speaker_name=speaker_name,
                text=decision.cleaned_text,
                input_type="text",
                target_bot=decision.target,
            )

            # Build bounded context and persona instructions
            context_str = memory.format_context_for_llm(exclude_last=True)
            instructions = orchestrator.build_instructions_with_context(
                decision.target, context_str
            )

            # Claim user turn programmatic scope
            async with sess._claim_user_turn():
                try:
                    await sess.interrupt()
                except (RuntimeError, TimeoutError, asyncio.CancelledError):
                    pass
                if session_sathi is not None:
                    try:
                        session_sathi.interrupt()
                    except (RuntimeError, TimeoutError, asyncio.CancelledError):
                        pass

                if decision.target == "dost":
                    acquired = await orchestrator.arbitrator.acquire("dost")
                    if acquired:
                        orchestrator.active_bot = "dost"
                        sess.generate_reply(
                            user_input=decision.cleaned_text,
                            instructions=instructions,
                        )
                elif decision.target == "sathi" and session_sathi is not None:
                    acquired = await orchestrator.arbitrator.acquire("sathi")
                    if acquired:
                        orchestrator.active_bot = "sathi"
                        handle = session_sathi.generate_reply(
                            user_input=decision.cleaned_text,
                            instructions=instructions,
                        )

                        def _on_sathi_text_done(_: Any) -> None:
                            orchestrator.arbitrator.release("sathi")

                        handle.add_done_callback(_on_sathi_text_done)
        except (
            RuntimeError,
            TimeoutError,
            ValueError,
            KeyError,
            OSError,
            asyncio.CancelledError,
        ) as e:
            logger.warning("Error processing text input turn: %s", e)

    # 9. session_dost.start(): Attach orchestrator with text + audio input options
    dost_input_opts = room_io.RoomInputOptions(
        text_input_cb=_on_text_input,
    )
    logger.info("Starting primary voice room session for AI Dost...")
    await session_dost.start(
        agent=orchestrator,
        room=ctx.room,
        room_input_options=dost_input_opts,
    )
    logger.info("Primary AI Dost session active in room '%s'", ctx.room.name)

    # 10. Opening Greeting: Speak opening greeting on the active bot
    greeting = AI_SATHI_GREETING if default_target == "sathi" else AI_DOST_GREETING
    try:
        if default_target == "sathi" and session_sathi is not None:
            await session_sathi.say(greeting)
        else:
            await session_dost.say(greeting)
    except (RuntimeError, TimeoutError, asyncio.CancelledError) as e:
        logger.debug("Initial greeting skipped or cancelled: %s", e)


def main() -> None:
    """CLI entrypoint for running the LiveKit agent."""
    import sys

    # Allow viewing CLI help without requiring .env credentials to be configured first
    if any(arg in sys.argv for arg in ("--help", "-h")):
        cli.run_app(server)
        return

    settings = get_settings()
    setup_logging(settings.log_level)
    logger.info(
        "Starting Roxstar AI Voice Room Assistant (Checkpoint 5 - Two-Bot Orchestrator)..."
    )

    # agents.cli.run_app: Standard LiveKit CLI runner supporting 'dev', 'start', etc.
    cli.run_app(server)


if __name__ == "__main__":
    main()
