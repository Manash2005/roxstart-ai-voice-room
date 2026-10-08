"""Unit tests for TurnRouter (Checkpoint 5).

Covers all 12 core routing criteria:
1. Explicit Dost addressing
2. Explicit Sathi addressing
3. Explicit "AI Dost"
4. Explicit "AI Sathi"
5. Technical comparison questions
6. Casual and everyday conversation
7. Follow-up ownership when previous was Sathi
8. Follow-up ownership when previous was Dost
9. General fallback routing to Dost
10. Case normalization
11. Collaborative / both-bot handling (no accidental dual speech)
12. Invalid or empty inputs handled gracefully
"""

import pytest

from app.routing.router import RouteDecision, TurnRouter, normalize_text


@pytest.fixture
def router() -> TurnRouter:
    """Fixture providing a clean TurnRouter instance."""
    return TurnRouter(default_target="dost")


def test_1_explicit_dost(router: TurnRouter):
    """Scenario 1: User explicitly addresses Dost."""
    decision: RouteDecision = router.route("Dost, Docker kya hai?")
    assert decision.target == "dost"
    assert decision.reason == "explicit_address"
    assert decision.confidence == 1.0
    assert router.active_bot == "dost"


def test_2_explicit_sathi(router: TurnRouter):
    """Scenario 2: User explicitly addresses Sathi."""
    decision: RouteDecision = router.route("Sathi, compare REST and GraphQL.")
    assert decision.target == "sathi"
    assert decision.reason == "explicit_address"
    assert decision.confidence == 1.0
    assert router.active_bot == "sathi"


def test_3_explicit_ai_dost(router: TurnRouter):
    """Scenario 3: User addresses with prefix 'AI Dost'."""
    decision: RouteDecision = router.route("AI Dost, simple language mein samjhao.")
    assert decision.target == "dost"
    assert decision.reason == "explicit_address"
    assert decision.confidence == 1.0
    assert router.active_bot == "dost"


def test_4_explicit_ai_sathi(router: TurnRouter):
    """Scenario 4: User addresses with prefix 'AI Sathi'."""
    decision: RouteDecision = router.route("AI Sathi, architecture explain karo.")
    assert decision.target == "sathi"
    assert decision.reason == "explicit_address"
    assert decision.confidence == 1.0
    assert router.active_bot == "sathi"


def test_5_technical_comparison(router: TurnRouter):
    """Scenario 5: Unaddressed technical comparison routes to Sathi."""
    decision: RouteDecision = router.route("REST aur GraphQL mein kya difference hai?")
    assert decision.target == "sathi"
    assert decision.reason == "technical_comparison"
    assert decision.confidence >= 0.7
    assert router.active_bot == "sathi"


def test_6_casual_conversation(router: TurnRouter):
    """Scenario 6: Casual/mood conversation routes to Dost."""
    decision: RouteDecision = router.route("Aaj kya chal raha hai?")
    assert decision.target == "dost"
    assert decision.reason == "casual_query"
    assert decision.confidence >= 0.7
    assert router.active_bot == "dost"


def test_7_followup_ownership_sathi(router: TurnRouter):
    """Scenario 7: Follow-up question stays with previous active bot (Sathi)."""
    # Establish previous ownership
    router.active_bot = "sathi"

    decision: RouteDecision = router.route("Aur iska alternative?")
    assert decision.target == "sathi"
    assert decision.reason == "conversation_owner"
    assert decision.confidence == 0.85
    assert router.active_bot == "sathi"


def test_8_followup_ownership_dost(router: TurnRouter):
    """Scenario 8: Short follow-up stays with previous active bot (Dost)."""
    # Establish previous ownership
    router.active_bot = "dost"

    decision: RouteDecision = router.route("Simple batao.")
    assert decision.target == "dost"
    assert decision.reason == "conversation_owner"
    assert decision.confidence == 0.85
    assert router.active_bot == "dost"


def test_9_general_fallback_to_dost(router: TurnRouter):
    """Scenario 9: Unaddressed, non-comparison general question defaults deterministically to Dost."""
    decision: RouteDecision = router.route("Docker kya hota hai?")
    assert decision.target == "dost"
    assert decision.reason == "general_default"
    assert decision.confidence == 0.50
    assert router.active_bot == "dost"


def test_10_case_normalization(router: TurnRouter):
    """Scenario 10: Input with uppercase and punctuation normalizes properly."""
    decision: RouteDecision = router.route("DOST, explain Docker!")
    assert decision.target == "dost"
    assert decision.reason == "explicit_address"
    assert decision.confidence == 1.0


def test_11_collaborative_both_question(router: TurnRouter):
    """Scenario 11: Questions addressing both bots do not cause simultaneous speech."""
    decision: RouteDecision = router.route("Both of you, what do you think?")
    # Must route cleanly to a single responder (Dost) with explicit deferred reason
    assert decision.target == "dost"
    assert decision.reason == "collaborative_deferred"
    assert decision.target in ("dost", "sathi")


def test_12_invalid_and_empty_inputs(router: TurnRouter):
    """Scenario 12: Empty string, None, or pure punctuation handled safely."""
    decision_empty: RouteDecision = router.route("")
    assert decision_empty.target == "dost"
    assert decision_empty.reason == "empty_input"

    decision_none: RouteDecision = router.route(None)  # type: ignore
    assert decision_none.target == "dost"
    assert decision_none.reason == "empty_input"

    decision_spaces: RouteDecision = router.route("     ")
    assert decision_spaces.target == "dost"
    assert decision_spaces.reason == "empty_input"

    decision_punct: RouteDecision = router.route("???!!!")
    assert decision_punct.target == "dost"
    assert decision_punct.reason == "empty_input"


def test_normalize_text_helper():
    """Verify normalize_text helper utility."""
    assert normalize_text("  hello world  ") == "hello world"
    assert normalize_text("...Dost, explain Docker???") == "Dost, explain Docker"
    assert normalize_text(None) == ""
    assert normalize_text("") == ""


def test_explicit_addressing_overrides_topic(router: TurnRouter):
    """Verify Priority 1 explicit addressing overrides Priority 3 topic classification."""
    # Sathi query directed to Dost:
    dost_override = router.route("Dost, REST aur GraphQL compare karo.")
    assert dost_override.target == "dost"
    assert dost_override.reason == "explicit_address"

    # Dost query directed to Sathi:
    sathi_override = router.route("Sathi, aaj mood kharab hai.")
    assert sathi_override.target == "sathi"
    assert sathi_override.reason == "explicit_address"


def test_router_reset(router: TurnRouter):
    """Verify router state reset."""
    router.active_bot = "sathi"
    router.reset()
    assert router.active_bot is None
