"""Two-bot central orchestrator agent (Checkpoint 5).

Provides a single unified LiveKit Agent that receives user speech turns,
routes them to either AI Dost or AI Sathi using TurnRouter, enforces mutual
exclusion via ResponseArbitrator, and updates room participant identity.
"""

from __future__ import annotations

import asyncio

from livekit import rtc
from livekit.agents import Agent, StopResponse, llm
from livekit.agents.voice.generation import update_instructions

from app.logging import get_logger
from app.personas import AI_DOST_INSTRUCTIONS, AI_SATHI_INSTRUCTIONS
from app.routing.arbitrator import ResponseArbitrator
from app.routing.router import BotTarget, RouteDecision, TurnRouter

logger = get_logger(__name__)


class TwoBotOrchestrator(Agent):
    """Central two-bot orchestrator for LiveKit voice rooms.

    Manages turn routing and response arbitration between AI Dost and AI Sathi,
    ensuring only the routed bot responds and preventing overlapping speech.
    """

    def __init__(
        self,
        router: TurnRouter | None = None,
        arbitrator: ResponseArbitrator | None = None,
        room: rtc.Room | None = None,
        default_target: BotTarget = "dost",
        instructions: str | None = None,
    ) -> None:
        initial_instructions = instructions or (
            AI_DOST_INSTRUCTIONS if default_target == "dost" else AI_SATHI_INSTRUCTIONS
        )
        super().__init__(instructions=initial_instructions)
        self.router: TurnRouter = router or TurnRouter(default_target=default_target)
        self.arbitrator: ResponseArbitrator = arbitrator or ResponseArbitrator()
        self.room: rtc.Room | None = room
        self.active_bot: BotTarget = default_target

    async def on_user_turn_completed(
        self, turn_ctx: llm.ChatContext, new_message: llm.ChatMessage
    ) -> None:
        """Route the user utterance to either AI Dost or AI Sathi and enforce mutual exclusion."""
        user_text = new_message.text_content
        decision: RouteDecision = self.router.route(user_text)

        logger.info(
            "Turn routed | speaker: user | text: '%s' | selected_bot: %s | reason: %s | confidence: %.2f",
            decision.cleaned_text,
            decision.target,
            decision.reason,
            decision.confidence,
        )

        # Enforce mutual exclusion: ensure no other bot is currently speaking
        acquired = await self.arbitrator.acquire(decision.target)
        if not acquired:
            logger.warning(
                "Turn rejected for %s: speech generation already active by %s",
                decision.target,
                self.arbitrator.current_owner,
            )
            raise StopResponse()

        self.active_bot = decision.target

        # Select persona instructions for this turn
        selected_instructions = (
            AI_DOST_INSTRUCTIONS if decision.target == "dost" else AI_SATHI_INSTRUCTIONS
        )

        # Apply the selected persona instructions to the turn's ChatContext
        update_instructions(
            turn_ctx, instructions=selected_instructions, add_if_missing=True
        )
        self._instructions = selected_instructions

        # Update participant attributes and display name in the LiveKit room if available
        if self.room and self.room.isconnected():
            display_name = "AI Dost" if decision.target == "dost" else "AI Sathi"
            bot_id = f"ai-{decision.target}"
            asyncio.create_task(
                self._update_participant(display_name, bot_id, decision.reason)
            )

    async def _update_participant(
        self, display_name: str, bot_id: str, reason: str
    ) -> None:
        """Dynamically update LiveKit participant name and attributes to reflect active bot."""
        try:
            if self.room and self.room.local_participant:
                await self.room.local_participant.set_name(display_name)
                await self.room.local_participant.set_attributes(
                    {
                        "active_bot": bot_id,
                        "available_bots": "ai-dost,ai-sathi",
                        "routing_reason": reason,
                    }
                )
        except (RuntimeError, TimeoutError, asyncio.CancelledError) as e:
            logger.debug("Participant identity update skipped: %s", e)

    def release_turn(self) -> None:
        """Release current response lock."""
        owner = self.arbitrator.current_owner or self.active_bot
        self.arbitrator.release(owner)
