"""LiveKit Voice Room Assistant Agent.

Checkpoint 1: Initial production-quality foundation using:
- LiveKit Agents (Realtime RTC agent orchestration)
- Groq Whisper (Zero-cost STT with Hindi/Hinglish support)
- OpenRouter (Zero-cost free-tier LLM)
- TemporaryStubTTS (TTS intentionally deferred to Checkpoint 2 for local/open-source engine)
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections import deque
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
    resolve_language_mode,
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

    Checkpoint 6.5: Multilingual by default. If groq_stt_language is unset, empty,
    or 'auto', automatic language detection is enabled so English, Hindi, and Hinglish
    are recognized accurately without forcing a single language.
    """
    lang = (settings.groq_stt_language or "").strip()
    if lang.lower() in ("", "auto", "multilingual", "none"):
        logger.info(
            "Initializing Groq STT with automatic multilingual detection (model: %s)",
            settings.groq_stt_model,
        )
        return groq.STT(
            model=settings.groq_stt_model,
            language="",
            detect_language=True,
            api_key=settings.groq_api_key,
        )

    logger.info(
        "Initializing Groq STT with specific target language '%s' (model: %s)",
        lang,
        settings.groq_stt_model,
    )
    return groq.STT(
        model=settings.groq_stt_model,
        language=lang,
        detect_language=False,
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
                close_on_disconnect=False,
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
    # Checkpoint 6.5: Snappy conversational endpointing (0.35s) + preemptive generation
    session_dost = AgentSession(
        stt=stt_provider,
        llm=llm_dost,
        tts=tts_dost,
        min_endpointing_delay=0.35,
        preemptive_generation=True,
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
            # Only release lock on actual transition from speaking to idle/listening
            if (
                ev.old_state == "speaking"
                and ev.new_state in ("idle", "listening")
                and orchestrator.arbitrator.current_owner == "sathi"
            ):
                logger.info(
                    "Sathi speech playback concluded; releasing arbitration lock"
                )
                orchestrator.arbitrator.release("sathi")

    # Wire user speaking listener to interrupt Sathi on genuine barge-in
    @session_dost.on("user_state_changed")
    def _on_user_state_changed(ev: UserStateChangedEvent) -> None:
        if (
            ev.new_state == "speaking"
            and session_sathi is not None
            and orchestrator.arbitrator.current_owner == "sathi"
        ):
            # Guard against immediate acoustic echo or trailing user breath during warmup
            time_since_sathi_start = time.monotonic() - getattr(
                orchestrator, "sathi_turn_started_at", 0.0
            )
            if time_since_sathi_start < 1.5:
                logger.debug(
                    "Ignoring potential echo or transition barge-in during Sathi warmup (%.2fs < 1.5s)",
                    time_since_sathi_start,
                )
                return

            logger.info(
                "Genuine user speech detected while Sathi is active; interrupting Sathi"
            )
            try:
                session_sathi.interrupt()
            except (RuntimeError, TimeoutError, asyncio.CancelledError) as e:
                logger.debug("Sathi interrupt error: %s", e)
            orchestrator.arbitrator.release("sathi")

    async def _broadcast_turn(
        room: rtc.Room | None,
        turn_id: str,
        speaker_id: str,
        speaker_name: str,
        speaker_type: str,
        text: str,
        input_type: str,
        timestamp: float | None = None,
    ) -> None:
        """Broadcast a conversation turn via data channel to all room participants."""
        if not room:
            return
        try:
            is_conn = getattr(room, "isconnected", None)
            if callable(is_conn) and not is_conn():
                return
            local_p = getattr(room, "local_participant", None)
            if not local_p or not hasattr(local_p, "publish_data"):
                return
            payload = json.dumps(
                {
                    "type": "conversation_turn",
                    "id": turn_id,
                    "speaker_id": speaker_id,
                    "speaker_name": speaker_name,
                    "speaker_type": speaker_type,
                    "text": text,
                    "input_type": input_type,
                    "timestamp": int((timestamp or time.time()) * 1000),
                }
            )
            await local_p.publish_data(
                payload.encode("utf-8"),
                reliable=True,
                topic="lk.chat",
            )
        except (
            RuntimeError,
            TimeoutError,
            ValueError,
            KeyError,
            OSError,
            asyncio.CancelledError,
        ) as e:
            logger.debug("Turn broadcast skipped or failed: %s", e)

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
                    asyncio.create_task(
                        _broadcast_turn(
                            ctx.room,
                            turn_id=f"bot_{uuid.uuid4().hex[:6]}",
                            speaker_id="ai-dost",
                            speaker_name="AI Dost",
                            speaker_type="ai-dost",
                            text=text,
                            input_type="voice",
                        )
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
                        asyncio.create_task(
                            _broadcast_turn(
                                ctx.room,
                                turn_id=f"bot_{uuid.uuid4().hex[:6]}",
                                speaker_id="ai-sathi",
                                speaker_name="AI Sathi",
                                speaker_type="ai-sathi",
                                text=text,
                                input_type="voice",
                            )
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
                    if (
                        session_sathi is not None
                        and hasattr(session_sathi, "room_io")
                        and session_sathi.room_io is not None
                    ):
                        session_sathi.room_io.set_participant(active_human.identity)
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
                if (
                    session_sathi is not None
                    and hasattr(session_sathi, "room_io")
                    and session_sathi.room_io is not None
                ):
                    session_sathi.room_io.set_participant(p.identity)

            # Send recent conversation history to newly joined human participant
            if (
                p.identity not in ("ai-dost", "ai-sathi")
                and ctx.room
                and ctx.room.local_participant
                and memory.get_turns()
            ):
                turns_data = [
                    {
                        "id": t.turn_id,
                        "speaker_id": t.speaker_id,
                        "speaker_name": t.speaker_name,
                        "speaker_type": t.speaker_type,
                        "text": t.text,
                        "input_type": t.input_type,
                        "timestamp": int(t.timestamp.timestamp() * 1000),
                    }
                    for t in memory.get_turns()
                ]
                resp = json.dumps({"type": "conversation_history", "turns": turns_data})
                asyncio.create_task(
                    ctx.room.local_participant.publish_data(
                        resp.encode("utf-8"),
                        reliable=True,
                        destination_identities=[p.identity],
                        topic="lk.chat",
                    )
                )
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
                        if (
                            session_sathi is not None
                            and hasattr(session_sathi, "room_io")
                            and session_sathi.room_io is not None
                        ):
                            session_sathi.room_io.set_participant(remotes[0].identity)
                    else:
                        session_dost.room_io.unset_participant()
                        if (
                            session_sathi is not None
                            and hasattr(session_sathi, "room_io")
                            and session_sathi.room_io is not None
                        ):
                            session_sathi.room_io.unset_participant()
        except (RuntimeError, AttributeError, ValueError) as e:
            logger.debug("Participant disconnect handler error: %s", e)

    recent_text_turns: deque[tuple[str, str, float]] = deque(maxlen=20)

    async def _handle_user_text_message(
        raw_text: str,
        speaker_id: str,
        speaker_name: str,
    ) -> None:
        try:
            raw_text = (raw_text or "").strip()
            if not raw_text:
                return

            now = time.monotonic()
            for prev_text, prev_id, prev_time in recent_text_turns:
                if (
                    prev_text == raw_text
                    and prev_id == speaker_id
                    and (now - prev_time) < 1.5
                ):
                    logger.debug("Deduplicated identical text turn from %s", speaker_id)
                    return
            recent_text_turns.append((raw_text, speaker_id, now))

            decision = orchestrator.router.route(raw_text)
            logger.info(
                "Text turn received | speaker: '%s' (%s) | text: '%s' | selected_bot: %s",
                speaker_name,
                speaker_id,
                decision.cleaned_text,
                decision.target,
            )

            turn_id = f"text_{uuid.uuid4().hex[:6]}"
            # Record human turn into unified shared memory
            memory.add_human_turn(
                speaker_id=speaker_id,
                speaker_name=speaker_name,
                text=decision.cleaned_text,
                input_type="text",
                target_bot=decision.target,
            )

            # Broadcast the human turn to room participants
            asyncio.create_task(
                _broadcast_turn(
                    ctx.room,
                    turn_id=turn_id,
                    speaker_id=speaker_id,
                    speaker_name=speaker_name,
                    speaker_type="human",
                    text=decision.cleaned_text,
                    input_type="text",
                )
            )

            # Evaluate language policy for text input
            lang_policy = resolve_language_mode(
                raw_text, orchestrator.preferred_language
            )
            if lang_policy.new_persistent_preference is not None:
                orchestrator.preferred_language = lang_policy.new_persistent_preference

            # Build bounded context and persona instructions with language directive
            context_str = memory.format_context_for_llm(exclude_last=True)
            instructions = orchestrator.build_instructions_with_context(
                decision.target, context_str, lang_policy.system_directive
            )

            # Claim user turn programmatic scope
            async with session_dost._claim_user_turn():
                try:
                    await session_dost.interrupt()
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
                        session_dost.generate_reply(
                            user_input=decision.cleaned_text,
                            instructions=instructions,
                        )
                elif decision.target == "sathi" and session_sathi is not None:
                    acquired = await orchestrator.arbitrator.acquire("sathi")
                    if acquired:
                        orchestrator.active_bot = "sathi"
                        orchestrator.sathi_turn_started_at = time.monotonic()
                        handle = session_sathi.generate_reply(
                            user_input=decision.cleaned_text,
                            instructions=instructions,
                        )

                        def _on_sathi_text_done(sh: Any) -> None:
                            err = sh.exception() if hasattr(sh, "exception") else None
                            if err:
                                logger.error("AI Sathi text response failed: %s", err)
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

    async def _on_text_input(sess: AgentSession, ev: TextInputEvent) -> None:
        participant = ev.participant
        if participant is not None:
            s_id = getattr(participant, "identity", None) or "human-text"
            s_name = getattr(participant, "name", None) or s_id
        else:
            s_id = "human-text"
            s_name = "User"
        await _handle_user_text_message(ev.text, s_id, s_name)

    @ctx.room.on("data_received")
    def _on_room_data_received(dp: rtc.DataPacket) -> None:
        try:
            if not dp.data:
                return
            raw_str = dp.data.decode("utf-8")
            try:
                parsed = json.loads(raw_str)
            except json.JSONDecodeError:
                parsed = {"text": raw_str}

            msg_type = parsed.get("type", "chat_message")
            if msg_type == "request_history":
                p = dp.participant
                if p and ctx.room and ctx.room.local_participant:
                    turns_data = [
                        {
                            "id": t.turn_id,
                            "speaker_id": t.speaker_id,
                            "speaker_name": t.speaker_name,
                            "speaker_type": t.speaker_type,
                            "text": t.text,
                            "input_type": t.input_type,
                            "timestamp": int(t.timestamp.timestamp() * 1000),
                        }
                        for t in memory.get_turns()
                    ]
                    resp = json.dumps(
                        {"type": "conversation_history", "turns": turns_data}
                    )
                    asyncio.create_task(
                        ctx.room.local_participant.publish_data(
                            resp.encode("utf-8"),
                            reliable=True,
                            destination_identities=[p.identity],
                            topic="lk.chat",
                        )
                    )
                return

            text = (parsed.get("text") or parsed.get("message") or "").strip()
            if not text:
                return

            p = dp.participant
            if p is not None:
                s_id = getattr(p, "identity", None) or "human-text"
                s_name = getattr(p, "name", None) or s_id
            else:
                s_id = parsed.get("speaker_id") or "human-text"
                s_name = parsed.get("speaker_name") or "User"

            asyncio.create_task(_handle_user_text_message(text, s_id, s_name))
        except (
            RuntimeError,
            TimeoutError,
            ValueError,
            KeyError,
            OSError,
            asyncio.CancelledError,
        ) as e:
            logger.debug("Error handling room data packet: %s", e)

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
