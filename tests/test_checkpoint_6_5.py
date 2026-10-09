"""Checkpoint 6.5 regression and validation test suite.

Verifies:
1. Multilingual Groq STT configuration (automatic detection by default).
2. Language response policy:
   - Case 1: Pure English query -> English response directive
   - Case 2: Hindi query -> Hinglish response directive
   - Case 3: Hinglish mixed query -> Hinglish response directive
   - Case 4: Explicit English request -> English directive
   - Case 5: Explicit Hindi request -> Hinglish directive
   - Case 6: Mixed tech English + Hindi -> Hinglish directive
   - Case 7: Persistent preference switch ('Ab se English mein...')
3. Sathi routing, dispatch, and arbitration safety.
4. Latency instrumentation correctness and zero secret leakage.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from livekit.agents import StopResponse, llm

from app.agent import create_stt
from app.config import Settings
from app.routing import (
    ResponseArbitrator,
    TurnLatencyTracker,
    TurnRouter,
    TwoBotOrchestrator,
    resolve_language_mode,
)


# ==============================================================================
# 1. Multilingual STT Configuration
# ==============================================================================
def test_groq_stt_multilingual_default(monkeypatch):
    """Verify create_stt enables automatic multilingual detection by default."""
    settings = Settings(
        livekit_url="wss://dummy.livekit.cloud",
        livekit_api_key="key",
        livekit_api_secret="secret",
        openrouter_api_key="or-key",
        groq_api_key="gsk-test",
        groq_stt_language="",  # default empty -> auto
    )
    stt_inst = create_stt(settings)
    assert stt_inst._opts.detect_language is True
    assert stt_inst._opts.languages == []


def test_groq_stt_auto_keyword(monkeypatch):
    """Verify 'auto' keyword in GROQ_STT_LANGUAGE activates automatic detection."""
    settings = Settings(
        livekit_url="wss://dummy.livekit.cloud",
        livekit_api_key="key",
        livekit_api_secret="secret",
        openrouter_api_key="or-key",
        groq_api_key="gsk-test",
        groq_stt_language="auto",
    )
    stt_inst = create_stt(settings)
    assert stt_inst._opts.detect_language is True


def test_groq_stt_explicit_fixed_language():
    """Verify explicit language code (e.g. 'hi' or 'en') disables auto detection."""
    settings = Settings(
        livekit_url="wss://dummy.livekit.cloud",
        livekit_api_key="key",
        livekit_api_secret="secret",
        openrouter_api_key="or-key",
        groq_api_key="gsk-test",
        groq_stt_language="hi",
    )
    stt_inst = create_stt(settings)
    assert stt_inst._opts.detect_language is False
    assert stt_inst._opts.languages == ["hi"]


# ==============================================================================
# 2. Language Policy & 7 Required Cases
# ==============================================================================
def test_case_1_english_query():
    """CASE 1: 'Explain what a binary tree is.' -> Natural English response."""
    result = resolve_language_mode("Explain what a binary tree is.")
    assert result.mode == "en"
    assert "English" in result.system_directive


def test_case_2_hindi_query():
    """CASE 2: 'Binary tree kya hota hai?' -> Natural Hindi/Hinglish response."""
    result = resolve_language_mode("Binary tree kya hota hai?")
    assert result.mode == "hi"
    assert "Hinglish" in result.system_directive


def test_case_3_hinglish_mixed_query():
    """CASE 3: 'Can you explain binary tree simple language mein?' -> Natural Hinglish."""
    result = resolve_language_mode("Can you explain binary tree simple language mein?")
    assert result.mode == "hi"


def test_case_4_explicit_english_request():
    """CASE 4: 'Please answer completely in English.' -> 100% English."""
    result = resolve_language_mode("Please answer completely in English.")
    assert result.mode == "en"
    assert "Do NOT use Hindi" in result.system_directive


def test_case_5_explicit_hindi_request():
    """CASE 5: 'Isko Hindi mein samjhao.' -> Hindi/Hinglish."""
    result = resolve_language_mode("Isko Hindi mein samjhao.")
    assert result.mode == "hi"


def test_case_6_mixed_technical_hinglish():
    """CASE 6: 'React mein state management kaise karte hain?' -> Conversational Hinglish."""
    result = resolve_language_mode("React mein state management kaise karte hain?")
    assert result.mode == "hi"


def test_case_7_persistent_language_preference_switch():
    """CASE 7: 'Ab se English mein answer karo.' -> Subsequent queries stay in English."""
    result1 = resolve_language_mode("Ab se English mein answer karo.")
    assert result1.mode == "en"
    assert result1.new_persistent_preference == "en"

    # Next query has no explicit language directive, should adhere to saved preference
    result2 = resolve_language_mode(
        "Next question: how does garbage collection work?",
        current_preference=result1.new_persistent_preference,
    )
    assert result2.mode == "en"


def test_persistent_preference_switch_back_to_hindi():
    """Verify switching persistent preference back to Hindi ('Ab se Hindi mein bolo')."""
    res = resolve_language_mode("Ab se Hindi mein bolo", current_preference="en")
    assert res.mode == "hi"
    assert res.new_persistent_preference == "hi"


# ==============================================================================
# 3. TwoBotOrchestrator Language & Routing Integration
# ==============================================================================
@pytest.mark.asyncio
async def test_orchestrator_injects_language_directive_for_english():
    """Verify orchestrator injects English directive into context message when user speaks English."""
    orchestrator = TwoBotOrchestrator()
    chat_ctx = llm.ChatContext.empty()
    user_msg = llm.ChatMessage(
        role="user", content=["Explain what a binary tree is in English."]
    )

    await orchestrator.on_user_turn_completed(chat_ctx, user_msg)
    assert orchestrator.active_bot == "dost"

    # Context message should contain English language directive
    ctx_msg = next(
        m for m in chat_ctx.items if getattr(m, "id", None) == "conversation_context"
    )
    assert "LANGUAGE DIRECTIVE" in ctx_msg.content[0]
    assert "English" in ctx_msg.content[0]


@pytest.mark.asyncio
async def test_orchestrator_injects_language_directive_for_hindi():
    """Verify orchestrator injects Hinglish directive when user speaks Hindi."""
    orchestrator = TwoBotOrchestrator()
    chat_ctx = llm.ChatContext.empty()
    user_msg = llm.ChatMessage(
        role="user", content=["Dost, mujhe binary tree samjhao."]
    )

    await orchestrator.on_user_turn_completed(chat_ctx, user_msg)
    assert orchestrator.active_bot == "dost"

    ctx_msg = next(
        m for m in chat_ctx.items if getattr(m, "id", None) == "conversation_context"
    )
    assert "Hinglish" in ctx_msg.content[0]


@pytest.mark.asyncio
async def test_sathi_explicit_routing_and_execution():
    """Verify explicit Sathi routing triggers Sathi session generate_reply and raises StopResponse."""
    router = TurnRouter()
    arbitrator = ResponseArbitrator()
    mock_sathi_session = MagicMock()
    mock_handle = MagicMock()
    mock_sathi_session.generate_reply.return_value = mock_handle

    orchestrator = TwoBotOrchestrator(
        router=router,
        arbitrator=arbitrator,
        sathi_session=mock_sathi_session,
    )

    chat_ctx = llm.ChatContext.empty()
    user_msg = llm.ChatMessage(
        role="user",
        content=["Sathi, explain the technical difference between React and Angular."],
    )

    with pytest.raises(StopResponse):
        await orchestrator.on_user_turn_completed(chat_ctx, user_msg)

    assert orchestrator.active_bot == "sathi"
    assert arbitrator.current_owner == "sathi"
    mock_sathi_session.generate_reply.assert_called_once()


@pytest.mark.asyncio
async def test_dost_explicit_routing():
    """Verify explicit Dost query routes directly to Dost without touching Sathi."""
    router = TurnRouter()
    arbitrator = ResponseArbitrator()
    mock_sathi_session = MagicMock()

    orchestrator = TwoBotOrchestrator(
        router=router,
        arbitrator=arbitrator,
        sathi_session=mock_sathi_session,
    )

    chat_ctx = llm.ChatContext.empty()
    user_msg = llm.ChatMessage(role="user", content=["Hey Dost, what is React?"])

    await orchestrator.on_user_turn_completed(chat_ctx, user_msg)
    assert orchestrator.active_bot == "dost"
    assert arbitrator.current_owner == "dost"
    mock_sathi_session.generate_reply.assert_not_called()


# ==============================================================================
# 4. Latency Instrumentation
# ==============================================================================
def test_latency_tracker_calculations_and_logging():
    """Verify TurnLatencyTracker accurately calculates millisecond durations and produces log string."""
    tracker = TurnLatencyTracker(turn_id="turn_test_1", bot_target="dost")
    tracker.turn_detected_at = 100.0
    tracker.stt_start_at = 100.1
    tracker.stt_end_at = 100.5  # 400ms
    tracker.routing_start_at = 100.5
    tracker.routing_end_at = 100.505  # 5ms
    tracker.llm_start_at = 100.51
    tracker.llm_first_token_at = 101.11  # 600ms
    tracker.tts_start_at = 101.12
    tracker.tts_first_audio_at = 101.32  # 200ms
    tracker.first_audio_published_at = 101.35  # total: 1350ms

    assert tracker.stt_ms == 400.0
    assert tracker.routing_ms == 5.0
    assert tracker.llm_ms == 600.0
    assert tracker.tts_first_audio_ms == 200.0
    assert tracker.total_first_audio_ms == 1350.0

    summary = tracker.format_summary()
    assert "turn=turn_test_1" in summary
    assert "bot=dost" in summary
    assert "stt=400ms" in summary
    assert "routing=5ms" in summary
    assert "llm=600ms" in summary
    assert "tts_first=200ms" in summary
    assert "total_first_audio=1350ms" in summary

    # Verify no raw user prompt or credentials leaked
    assert "api_key" not in summary.lower()
    assert "secret" not in summary.lower()
