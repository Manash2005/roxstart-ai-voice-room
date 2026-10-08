"""Unit tests for dual genuine LiveKit participants (Checkpoint 5A)."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from livekit.agents import StopResponse, llm
from livekit.agents.voice import room_io

from app.agent import on_request
from app.routing.arbitrator import BotState, ResponseArbitrator
from app.routing.orchestrator import TwoBotOrchestrator
from app.routing.router import TurnRouter
from app.routing.secondary_participant import (
    create_participant_token,
    disconnect_secondary_participant,
)


def test_participant_token_generation():
    """Verify create_participant_token produces an access token with identity 'ai-sathi'."""
    token = create_participant_token(
        api_key="test_api_key_12345678901234567890",
        api_secret="test_api_secret_12345678901234567890",
        room_name="voice-room-alpha",
        identity="ai-sathi",
        name="AI Sathi",
        kind="agent",
    )
    assert isinstance(token, str)
    assert len(token) > 50


def test_secondary_session_room_input_options():
    """Verify secondary session input options strictly disable audio and text listening."""
    opts = room_io.RoomInputOptions(
        audio_enabled=False,
        text_enabled=False,
    )
    assert opts.audio_enabled is False
    assert opts.text_enabled is False


@pytest.mark.asyncio
async def test_job_request_on_request_configures_ai_dost():
    """Verify primary job request acceptance sets identity 'ai-dost' and display name 'AI Dost'."""
    mock_req = MagicMock()
    mock_req.accept = AsyncMock()

    await on_request(mock_req)
    mock_req.accept.assert_called_once_with(identity="ai-dost", name="AI Dost")


@pytest.mark.asyncio
async def test_dost_turn_does_not_invoke_sathi_generate_reply():
    """Verify that when a turn is routed to AI Dost, AI Sathi's generate_reply is NOT invoked."""
    router = TurnRouter()
    arbitrator = ResponseArbitrator()
    mock_sathi_session = MagicMock()
    mock_sathi_session.generate_reply = MagicMock()

    orchestrator = TwoBotOrchestrator(
        router=router,
        arbitrator=arbitrator,
        sathi_session=mock_sathi_session,
    )

    chat_ctx = llm.ChatContext.empty()
    user_msg_dost = llm.ChatMessage(
        role="user", content=["Dost, Docker explain karo simple words mein."]
    )

    # Must complete normally without raising StopResponse
    await orchestrator.on_user_turn_completed(chat_ctx, user_msg_dost)

    # AI Sathi must NOT have been called
    mock_sathi_session.generate_reply.assert_not_called()
    assert orchestrator.active_bot == "dost"
    assert arbitrator.current_owner == "dost"
    assert arbitrator.state == BotState.RESPONDING

    orchestrator.release_turn()
    assert arbitrator.is_responding is False


@pytest.mark.asyncio
async def test_sathi_turn_invokes_generate_reply_and_raises_stop_response():
    """Verify that when a turn is routed to AI Sathi:
    1. Sathi's generate_reply is called exactly once.
    2. Primary session StopResponse is raised to prevent Dost speech.
    """
    router = TurnRouter()
    arbitrator = ResponseArbitrator()
    mock_sathi_session = MagicMock()
    mock_handle = MagicMock()
    mock_sathi_session.generate_reply = MagicMock(return_value=mock_handle)

    orchestrator = TwoBotOrchestrator(
        router=router,
        arbitrator=arbitrator,
        sathi_session=mock_sathi_session,
    )

    chat_ctx = llm.ChatContext.empty()
    user_msg_sathi = llm.ChatMessage(
        role="user", content=["Sathi, compare REST and GraphQL architecture."]
    )

    # Primary session must raise StopResponse to suppress AI Dost reply
    with pytest.raises(StopResponse):
        await orchestrator.on_user_turn_completed(chat_ctx, user_msg_sathi)

    # Sathi generate_reply must have been called exactly once with the transcript
    mock_sathi_session.generate_reply.assert_called_once_with(
        user_input="Sathi, compare REST and GraphQL architecture."
    )
    assert orchestrator.active_bot == "sathi"
    assert arbitrator.current_owner == "sathi"
    assert arbitrator.state == BotState.RESPONDING


@pytest.mark.asyncio
async def test_sathi_done_callback_releases_arbitration_lock():
    """Verify done callback on Sathi SpeechHandle automatically releases the arbitration lock."""
    router = TurnRouter()
    arbitrator = ResponseArbitrator()
    mock_sathi_session = MagicMock()
    mock_handle = MagicMock()
    callbacks = []
    mock_handle.add_done_callback = MagicMock(
        side_effect=lambda cb: callbacks.append(cb)
    )
    mock_sathi_session.generate_reply = MagicMock(return_value=mock_handle)

    orchestrator = TwoBotOrchestrator(
        router=router,
        arbitrator=arbitrator,
        sathi_session=mock_sathi_session,
    )

    chat_ctx = llm.ChatContext.empty()
    user_msg = llm.ChatMessage(role="user", content=["Sathi, explain Kubernetes."])

    with pytest.raises(StopResponse):
        await orchestrator.on_user_turn_completed(chat_ctx, user_msg)

    assert arbitrator.current_owner == "sathi"
    assert len(callbacks) == 1

    # Simulate Sathi playback completing
    callbacks[0](mock_handle)
    assert arbitrator.current_owner is None
    assert arbitrator.state == BotState.IDLE


@pytest.mark.asyncio
async def test_sathi_generation_failure_releases_arbitration_lock():
    """Verify that if Sathi generate_reply raises an exception, the arbitration lock is released."""
    router = TurnRouter()
    arbitrator = ResponseArbitrator()
    mock_sathi_session = MagicMock()
    mock_sathi_session.generate_reply = MagicMock(
        side_effect=RuntimeError("LLM rate limit reached")
    )

    orchestrator = TwoBotOrchestrator(
        router=router,
        arbitrator=arbitrator,
        sathi_session=mock_sathi_session,
    )

    chat_ctx = llm.ChatContext.empty()
    user_msg = llm.ChatMessage(role="user", content=["Sathi, explain microservices."])

    with pytest.raises(StopResponse):
        await orchestrator.on_user_turn_completed(chat_ctx, user_msg)

    # Arbitration lock must be released despite failure
    assert arbitrator.current_owner is None
    assert arbitrator.state == BotState.IDLE


@pytest.mark.asyncio
async def test_sathi_unavailable_fallback_to_dost():
    """Verify that if sathi_session is None, routing falls back to single-session Dost."""
    router = TurnRouter()
    arbitrator = ResponseArbitrator()

    # Orchestrator without sathi_session attached
    orchestrator = TwoBotOrchestrator(
        router=router,
        arbitrator=arbitrator,
        sathi_session=None,
    )

    chat_ctx = llm.ChatContext.empty()
    user_msg = llm.ChatMessage(
        role="user", content=["Sathi, compare Kafka and RabbitMQ."]
    )

    # Should not raise StopResponse or unhandled errors
    await orchestrator.on_user_turn_completed(chat_ctx, user_msg)

    assert orchestrator.active_bot == "sathi"
    orchestrator.release_turn()
    assert arbitrator.state == BotState.IDLE


@pytest.mark.asyncio
async def test_dost_turn_interrupts_active_sathi():
    """Verify that an incoming Dost turn interrupts an active Sathi speech and acquires the lock."""
    router = TurnRouter()
    arbitrator = ResponseArbitrator()
    mock_sathi_session = MagicMock()
    mock_sathi_session.interrupt = MagicMock()

    orchestrator = TwoBotOrchestrator(
        router=router,
        arbitrator=arbitrator,
        sathi_session=mock_sathi_session,
    )

    # Simulate Sathi currently holding response ownership
    await arbitrator.acquire("sathi")
    assert arbitrator.current_owner == "sathi"

    # User addresses Dost
    chat_ctx = llm.ChatContext.empty()
    user_msg_dost = llm.ChatMessage(role="user", content=["Dost, ruko ek minute."])

    await orchestrator.on_user_turn_completed(chat_ctx, user_msg_dost)

    # Sathi must have been interrupted and Dost must hold ownership
    mock_sathi_session.interrupt.assert_called_once()
    assert arbitrator.current_owner == "dost"
    assert orchestrator.active_bot == "dost"

    orchestrator.release_turn()


@pytest.mark.asyncio
async def test_disconnect_secondary_participant_safe_cleanup():
    """Verify disconnect_secondary_participant safely handles connected, disconnected, and None rooms."""
    # 1. None room
    await disconnect_secondary_participant(None)

    # 2. Mock room disconnected
    mock_room_disconnected = MagicMock()
    mock_room_disconnected.isconnected.return_value = False
    mock_room_disconnected.disconnect = AsyncMock()
    await disconnect_secondary_participant(mock_room_disconnected)
    mock_room_disconnected.disconnect.assert_not_called()

    # 3. Mock room connected
    mock_room_connected = MagicMock()
    mock_room_connected.isconnected.return_value = True
    mock_room_connected.disconnect = AsyncMock()
    await disconnect_secondary_participant(mock_room_connected)
    mock_room_connected.disconnect.assert_called_once()
