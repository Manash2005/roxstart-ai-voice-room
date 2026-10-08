"""Unit tests for Checkpoint 6: Contextual Memory and Multi-Speaker Interaction.

Tests cover:
- Memory domain model (ConversationTurn) and bounded FIFO eviction
- In-memory ConversationMemory storage and ordering
- Speaker attribution (distinct participant IDs, display names, fallbacks)
- Voice and text modality unification in the same conversation history
- Context formatting and injection into LLM prompts
- Multi-user conversational context preservation
- Bot turn storage and cross-bot memory sharing (Dost -> Sathi)
- Robustness and error fallback when memory operations encounter issues
"""

from unittest.mock import MagicMock

import pytest
from livekit.agents import StopResponse, llm

from app.memory import ConversationMemory, ConversationTurn
from app.personas import AI_DOST_INSTRUCTIONS, AI_SATHI_INSTRUCTIONS
from app.routing.arbitrator import ResponseArbitrator
from app.routing.orchestrator import TwoBotOrchestrator
from app.routing.router import TurnRouter

# ==============================================================================
# 1. ConversationTurn & Memory Model Tests
# ==============================================================================


def test_conversation_turn_properties():
    """Verify ConversationTurn stores fields and exposes helper properties."""
    human_turn = ConversationTurn(
        speaker_id="user-123",
        speaker_name="Manash",
        role="human",
        text="Mujhe Kubernetes samajh nahi aa raha.",
        input_type="voice",
        target_bot="dost",
    )
    assert human_turn.is_human is True
    assert human_turn.is_bot is False
    assert human_turn.speaker_id == "user-123"
    assert (
        human_turn.format_line()
        == '- Manash (voice): "Mujhe Kubernetes samajh nahi aa raha."'
    )

    bot_turn = ConversationTurn(
        speaker_id="ai-dost",
        speaker_name="AI Dost",
        role="bot",
        text="Kubernetes ek container manager hai.",
        input_type="voice",
        target_bot="dost",
    )
    assert bot_turn.is_human is False
    assert bot_turn.is_bot is True
    assert (
        bot_turn.format_line()
        == '- AI Dost (voice): "Kubernetes ek container manager hai."'
    )


def test_memory_add_turns_and_preserve_order():
    """Verify turns are stored in insertion order."""
    mem = ConversationMemory(max_turns=10)
    mem.add_human_turn(
        speaker_id="p1", speaker_name="Alice", text="Turn 1", input_type="voice"
    )
    mem.add_bot_turn(
        bot_id="ai-dost", bot_name="AI Dost", text="Turn 2", input_type="voice"
    )
    mem.add_human_turn(
        speaker_id="p2", speaker_name="Bob", text="Turn 3", input_type="text"
    )

    turns = mem.get_recent_turns()
    assert len(turns) == 3
    assert [t.text for t in turns] == ["Turn 1", "Turn 2", "Turn 3"]
    assert turns[0].speaker_name == "Alice"
    assert turns[1].speaker_name == "AI Dost"
    assert turns[2].speaker_name == "Bob"
    assert turns[2].input_type == "text"


def test_memory_bounded_fifo_eviction():
    """Verify oldest turns are evicted when memory reaches max_turns limit."""
    mem = ConversationMemory(max_turns=4)
    for i in range(6):
        mem.add_human_turn(
            speaker_id=f"p{i}",
            speaker_name=f"User {i}",
            text=f"Message {i}",
            input_type="voice",
        )

    assert len(mem) == 4
    turns = mem.get_recent_turns()
    # Oldest (0 and 1) must be evicted; only 2, 3, 4, 5 remain
    assert [t.text for t in turns] == [
        "Message 2",
        "Message 3",
        "Message 4",
        "Message 5",
    ]
    assert turns[0].speaker_name == "User 2"


def test_memory_clear_resets_state():
    """Verify memory.clear() resets all recorded turns on room exit."""
    mem = ConversationMemory()
    mem.add_human_turn(
        speaker_id="p1", speaker_name="Alice", text="Hello", input_type="voice"
    )
    mem.add_bot_turn(
        bot_id="ai-dost", bot_name="AI Dost", text="Namaste", input_type="voice"
    )
    assert len(mem) == 2

    mem.clear()
    assert len(mem) == 0
    assert mem.get_recent_turns() == []
    assert mem.format_context_for_llm() == ""


def test_memory_ignores_empty_or_whitespace_turns():
    """Verify empty or blank turns are safely ignored without insertion."""
    mem = ConversationMemory()
    mem.add_human_turn(speaker_id="p1", speaker_name="Alice", text="   ")
    mem.add_bot_turn(bot_id="ai-dost", bot_name="AI Dost", text="")
    assert len(mem) == 0


# ==============================================================================
# 2. Speaker Attribution & Fallbacks
# ==============================================================================


def test_speaker_attribution_distinct_and_repeated_participants():
    """Verify memory correctly tracks distinct speakers and repeated turns."""
    mem = ConversationMemory()
    mem.add_human_turn(
        speaker_id="p1", speaker_name="Alice", text="I like Python", input_type="voice"
    )
    mem.add_human_turn(
        speaker_id="p2", speaker_name="Bob", text="I like Go", input_type="voice"
    )
    mem.add_human_turn(
        speaker_id="p1",
        speaker_name="Alice",
        text="Can you compare them?",
        input_type="voice",
    )

    alice_turns = mem.get_speaker_turns("p1")
    bob_turns = mem.get_speaker_turns("p2")

    assert len(alice_turns) == 2
    assert [t.text for t in alice_turns] == ["I like Python", "Can you compare them?"]
    assert len(bob_turns) == 1
    assert bob_turns[0].text == "I like Go"


def test_speaker_attribution_missing_metadata_fallback():
    """Verify fallback values when speaker identity is missing or empty."""
    mem = ConversationMemory()
    turn = mem.add_human_turn(
        speaker_id="",
        speaker_name="",
        text="Hello there",
        input_type="voice",
    )
    assert turn.speaker_id == "human"
    assert turn.speaker_name == "User"


# ==============================================================================
# 3. Voice and Text Modality Unification
# ==============================================================================


def test_voice_and_text_unified_in_same_memory():
    """Verify voice turns and text turns share the exact same chronological memory."""
    mem = ConversationMemory()

    # Turn 1: Human speaks via voice
    mem.add_human_turn(
        speaker_id="user-1",
        speaker_name="Manash",
        text="Mera project Node.js mein hai.",
        input_type="voice",
    )
    # Turn 2: AI Dost responds
    mem.add_bot_turn(
        bot_id="ai-dost",
        bot_name="AI Dost",
        text="Node.js badiya choice hai backend ke liye.",
        input_type="voice",
    )
    # Turn 3: Human types via text
    mem.add_human_turn(
        speaker_id="user-1",
        speaker_name="Manash",
        text="Which database should I use?",
        input_type="text",
    )

    context = mem.format_context_for_llm()
    assert '- Manash (voice): "Mera project Node.js mein hai."' in context
    assert '- AI Dost (voice): "Node.js badiya choice hai backend ke liye."' in context
    assert '- Manash (text): "Which database should I use?"' in context


# ==============================================================================
# 4. Context Formatting & Injection
# ==============================================================================


def test_format_context_exclude_last():
    """Verify format_context_for_llm(exclude_last=True) excludes current active turn."""
    mem = ConversationMemory()
    mem.add_human_turn(
        speaker_id="p1", speaker_name="Alice", text="First question", input_type="voice"
    )
    mem.add_bot_turn(
        bot_id="ai-dost", bot_name="AI Dost", text="First answer", input_type="voice"
    )
    mem.add_human_turn(
        speaker_id="p1",
        speaker_name="Alice",
        text="Second question",
        input_type="voice",
    )

    context_full = mem.format_context_for_llm(exclude_last=False)
    context_excluded = mem.format_context_for_llm(exclude_last=True)

    assert "Second question" in context_full
    assert "Second question" not in context_excluded
    assert "First question" in context_excluded
    assert "First answer" in context_excluded


def test_base_persona_instructions_remain_unmodified():
    """Verify base instructions constants are never altered by context builder."""
    orchestrator = TwoBotOrchestrator()
    original_dost_len = len(AI_DOST_INSTRUCTIONS)
    original_sathi_len = len(AI_SATHI_INSTRUCTIONS)

    context_str = "- Alice: 'Hello'\n- AI Dost: 'Hi'"
    combined_dost = orchestrator.build_instructions_with_context("dost", context_str)
    combined_sathi = orchestrator.build_instructions_with_context("sathi", context_str)

    # Base instructions constants are untouched
    assert len(AI_DOST_INSTRUCTIONS) == original_dost_len
    assert len(AI_SATHI_INSTRUCTIONS) == original_sathi_len

    # Generated strings contain both base persona and context
    assert AI_DOST_INSTRUCTIONS in combined_dost
    assert context_str in combined_dost
    assert AI_SATHI_INSTRUCTIONS in combined_sathi
    assert context_str in combined_sathi


# ==============================================================================
# 5. Multi-User Conversational Flow
# ==============================================================================


def test_multi_user_context_preserves_both_speakers():
    """Verify multi-human dialogue preserves speaker attribution across turns."""
    mem = ConversationMemory()

    # Human A declares React
    mem.add_human_turn(
        speaker_id="user-a",
        speaker_name="Human A",
        text="Mera project React mein hai.",
        input_type="voice",
    )
    # Human B declares Django
    mem.add_human_turn(
        speaker_id="user-b",
        speaker_name="Human B",
        text="Mera Django mein.",
        input_type="voice",
    )
    # Human A asks follow-up
    mem.add_human_turn(
        speaker_id="user-a",
        speaker_name="Human A",
        text="Mere liye database suggest karo.",
        input_type="voice",
    )

    ctx = mem.format_context_for_llm(exclude_last=True)
    assert 'Human A (voice): "Mera project React mein hai."' in ctx
    assert 'Human B (voice): "Mera Django mein."' in ctx


# ==============================================================================
# 6. Cross-Bot Memory Sharing (Dost -> Sathi)
# ==============================================================================


@pytest.mark.asyncio
async def test_sathi_receives_dost_previous_response_in_context():
    """Verify Sathi's generate_reply receives prior Dost dialogue context in chat_ctx."""
    router = TurnRouter()
    arbitrator = ResponseArbitrator()
    memory = ConversationMemory()
    mock_sathi_session = MagicMock()
    mock_handle = MagicMock()
    mock_sathi_session.generate_reply = MagicMock(return_value=mock_handle)

    orchestrator = TwoBotOrchestrator(
        router=router,
        arbitrator=arbitrator,
        memory=memory,
        sathi_session=mock_sathi_session,
    )

    # 1. Human asked Dost earlier
    memory.add_human_turn(
        speaker_id="u1",
        speaker_name="User",
        text="Explain Docker.",
        input_type="voice",
        target_bot="dost",
    )
    memory.add_bot_turn(
        bot_id="ai-dost",
        bot_name="AI Dost",
        text="Docker ek container tool hai jisme code pack hota hai.",
        input_type="voice",
    )

    # 2. Human now asks Sathi explicitly
    chat_ctx = llm.ChatContext.empty()
    user_msg_sathi = llm.ChatMessage(
        role="user",
        content=["Sathi, iska technical architecture compare karo."],
    )

    with pytest.raises(StopResponse):
        await orchestrator.on_user_turn_completed(chat_ctx, user_msg_sathi)

    # Sathi generate_reply must have been called with chat_ctx containing context
    assert mock_sathi_session.generate_reply.called
    kwargs = mock_sathi_session.generate_reply.call_args.kwargs
    assert "chat_ctx" in kwargs
    sathi_chat_ctx = kwargs["chat_ctx"]

    # Verify context message in sathi_chat_ctx
    context_msgs = [
        m
        for m in sathi_chat_ctx.items
        if getattr(m, "id", None) == "conversation_context"
    ]
    assert len(context_msgs) == 1
    content_text = context_msgs[0].content[0]
    assert "Explain Docker" in content_text
    assert "Docker ek container tool hai" in content_text


# ==============================================================================
# 7. Follow-up Routing with Conversation Context
# ==============================================================================


def test_followup_pronouns_routed_to_active_bot():
    """Verify follow-up pronouns ('uska', 'same problem') maintain conversation ownership."""
    router = TurnRouter()

    # Initial turn to Dost
    d1 = router.route("Mujhe Kubernetes samajh nahi aa raha.")
    assert d1.target == "dost"

    # Follow-up with pronoun 'uska'
    d2 = router.route("Uska simple alternative kya hai?")
    assert d2.target == "dost"
    assert d2.reason == "conversation_owner"

    # Follow-up with 'same problem'
    d3 = router.route("Mere project mein bhi same problem hai.")
    assert d3.target == "dost"
    assert d3.reason == "conversation_owner"

    # Explicit switch to Sathi
    d4 = router.route("Sathi, Kubernetes ke fayde batao.")
    assert d4.target == "sathi"

    # Follow-up now stays with Sathi
    d5 = router.route("Aur iska downside kya hai?")
    assert d5.target == "sathi"
    assert d5.reason == "conversation_owner"


# ==============================================================================
# 8. Error Handling and Resilience
# ==============================================================================


@pytest.mark.asyncio
async def test_memory_failure_falls_back_gracefully():
    """Verify that an unexpected exception in memory does not crash the orchestrator."""
    router = TurnRouter()
    arbitrator = ResponseArbitrator()

    # Broken memory mock that raises on formatting
    broken_memory = MagicMock()
    broken_memory.add_human_turn = MagicMock(
        side_effect=RuntimeError("Memory write failed")
    )
    broken_memory.format_context_for_llm = MagicMock(
        side_effect=RuntimeError("Format failed")
    )

    orchestrator = TwoBotOrchestrator(
        router=router,
        arbitrator=arbitrator,
        memory=broken_memory,
    )

    chat_ctx = llm.ChatContext.empty()
    user_msg = llm.ChatMessage(role="user", content=["Dost, kya haal hai?"])

    # Must complete without crashing
    await orchestrator.on_user_turn_completed(chat_ctx, user_msg)
    assert orchestrator.active_bot == "dost"
    assert arbitrator.current_owner == "dost"
    orchestrator.release_turn()
