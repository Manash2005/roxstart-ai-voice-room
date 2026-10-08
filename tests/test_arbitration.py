"""Unit tests for response arbitration and mutual exclusion (Checkpoint 5)."""

import pytest
from livekit.agents import StopResponse, llm

from app.personas import AI_DOST_INSTRUCTIONS, AI_SATHI_INSTRUCTIONS
from app.routing.arbitrator import BotState, ResponseArbitrator
from app.routing.orchestrator import TwoBotOrchestrator
from app.routing.router import TurnRouter


@pytest.fixture
def arbitrator() -> ResponseArbitrator:
    """Fixture providing a clean ResponseArbitrator instance."""
    return ResponseArbitrator()


@pytest.mark.asyncio
async def test_initial_arbitrator_state(arbitrator: ResponseArbitrator):
    """Verify arbitrator starts in IDLE state with no current owner."""
    assert arbitrator.state == BotState.IDLE
    assert arbitrator.current_owner is None
    assert arbitrator.is_responding is False


@pytest.mark.asyncio
async def test_mutual_exclusion_dost_then_sathi(arbitrator: ResponseArbitrator):
    """Verify that when Dost acquires the lock, Sathi cannot acquire until Dost releases."""
    # 1. Dost acquires
    acquired_dost = await arbitrator.acquire("dost")
    assert acquired_dost is True
    assert arbitrator.state == BotState.RESPONDING
    assert arbitrator.current_owner == "dost"
    assert arbitrator.is_responding is True

    # 2. Sathi attempts acquisition -> must be rejected
    acquired_sathi = await arbitrator.acquire("sathi")
    assert acquired_sathi is False
    assert arbitrator.current_owner == "dost"

    # 3. Dost releases
    arbitrator.release("dost")
    assert arbitrator.state == BotState.IDLE
    assert arbitrator.current_owner is None
    assert arbitrator.is_responding is False

    # 4. Sathi can now acquire
    acquired_sathi_retry = await arbitrator.acquire("sathi")
    assert acquired_sathi_retry is True
    assert arbitrator.state == BotState.RESPONDING
    assert arbitrator.current_owner == "sathi"

    # Clean up
    arbitrator.release("sathi")
    assert arbitrator.state == BotState.IDLE


@pytest.mark.asyncio
async def test_mutual_exclusion_sathi_then_dost(arbitrator: ResponseArbitrator):
    """Verify that when Sathi acquires the lock, Dost cannot acquire until Sathi releases."""
    # 1. Sathi acquires
    assert await arbitrator.acquire("sathi") is True

    # 2. Dost attempts acquisition -> rejected
    assert await arbitrator.acquire("dost") is False

    # 3. Sathi releases
    arbitrator.release("sathi")

    # 4. Dost can now acquire
    assert await arbitrator.acquire("dost") is True
    arbitrator.release("dost")


@pytest.mark.asyncio
async def test_response_scope_context_manager(arbitrator: ResponseArbitrator):
    """Verify async context manager acquires on entry and automatically releases on exit."""
    async with arbitrator.response_scope("dost") as acquired:
        assert acquired is True
        assert arbitrator.state == BotState.RESPONDING
        assert arbitrator.current_owner == "dost"

        # Concurrently attempting acquisition inside the scope fails
        assert await arbitrator.acquire("sathi") is False

    # After exiting the block, lock is released
    assert arbitrator.state == BotState.IDLE
    assert arbitrator.current_owner is None


@pytest.mark.asyncio
async def test_orchestrator_raises_stop_response_when_locked():
    """Verify TwoBotOrchestrator raises StopResponse when response is already locked."""
    arbitrator = ResponseArbitrator()
    router = TurnRouter()
    orchestrator = TwoBotOrchestrator(router=router, arbitrator=arbitrator)

    # Simulate another bot currently speaking
    await arbitrator.acquire("sathi")

    chat_ctx = llm.ChatContext.empty()
    user_msg = llm.ChatMessage(role="user", content=["Dost, kya haal hai?"])

    # When incoming turn arrives while locked, StopResponse must be raised
    with pytest.raises(StopResponse):
        await orchestrator.on_user_turn_completed(chat_ctx, user_msg)


@pytest.mark.asyncio
async def test_orchestrator_updates_instructions_on_routing():
    """Verify TwoBotOrchestrator updates turn instructions to the selected persona."""
    arbitrator = ResponseArbitrator()
    router = TurnRouter()
    orchestrator = TwoBotOrchestrator(router=router, arbitrator=arbitrator)

    chat_ctx = llm.ChatContext.empty()
    # Turn 1: Sathi comparison query
    user_msg_sathi = llm.ChatMessage(
        role="user", content=["Sathi, compare REST and GraphQL."]
    )

    await orchestrator.on_user_turn_completed(chat_ctx, user_msg_sathi)
    assert orchestrator.active_bot == "sathi"
    assert orchestrator.instructions == AI_SATHI_INSTRUCTIONS
    # Turn instructions should match Sathi
    assert chat_ctx.items[0].content[0] == AI_SATHI_INSTRUCTIONS

    # Release turn
    orchestrator.release_turn()
    assert arbitrator.is_responding is False

    # Turn 2: Explicit Dost query
    user_msg_dost = llm.ChatMessage(
        role="user", content=["Dost, simple language mein samjhao."]
    )
    await orchestrator.on_user_turn_completed(chat_ctx, user_msg_dost)
    assert orchestrator.active_bot == "dost"
    assert orchestrator.instructions == AI_DOST_INSTRUCTIONS
    assert chat_ctx.items[0].content[0] == AI_DOST_INSTRUCTIONS
    orchestrator.release_turn()
