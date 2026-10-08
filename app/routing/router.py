"""Turn routing module for two-bot orchestration (Checkpoint 5).

Determines whether AI Dost or AI Sathi should respond to a user utterance
using a deterministic priority-based routing algorithm:
1. Priority 1 — Explicit bot addressing (e.g., "Dost...", "Sathi...")
2. Priority 2 — Conversation ownership (short follow-ups/continuations)
3. Priority 3 — Topic/intent classification (analytical comparisons vs casual/general)
4. Priority 4 — Deterministic default route (AI Dost)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

BotTarget = Literal["dost", "sathi"]


@dataclass(frozen=True)
class RouteDecision:
    """Typed decision returned by the turn router."""

    target: BotTarget
    reason: str
    confidence: float
    raw_text: str
    cleaned_text: str


def normalize_text(text: str | None) -> str:
    """Normalize input text by trimming whitespace, normalizing spaces, and stripping outer punctuation."""
    if not text:
        return ""
    # Collapse multiple whitespaces
    cleaned = re.sub(r"[\s]+", " ", str(text)).strip()
    # Strip leading and trailing punctuation while leaving internal punctuation intact
    cleaned = re.sub(
        r"^[\s,.;:!?\"\'\-\–\—\(\)\[\]{}]+|[\s,.;:!?\"\'\-\–\—\(\)\[\]{}]+$",
        "",
        cleaned,
    )
    return cleaned


class TurnRouter:
    """Deterministic turn router for dual-bot voice room orchestration."""

    def __init__(self, default_target: BotTarget = "dost") -> None:
        self.default_target: BotTarget = default_target
        self.active_bot: BotTarget | None = None

        # Priority 1: Explicit addressing patterns
        self._dost_explicit = re.compile(
            r"(?i)\b(ai\s+dost|bhai\s+dost|dost\s+bhai|dost\s+ji|dost)\b"
        )
        self._sathi_explicit = re.compile(
            r"(?i)\b(ai\s+sathi|sathi\s+ji|behen\s+sathi|sathi)\b"
        )
        self._both_explicit = re.compile(
            r"(?i)\b(both\s+of\s+you|both\s+bots|dono\s+batao|dono\s+kya|dono\s+log|both)\b"
        )

        # Priority 2: Follow-up continuation patterns
        self._followup_starters = re.compile(
            r"(?i)^(aur\s+|and\s+|what\s+about\s+|how\s+about\s+|why\b|kyun\b|kyu\b|isme\s+|iska\s+|iski\s+|iske\s+)"
        )
        self._followup_short = re.compile(
            r"(?i)^(simple\s+batao|simple\s+language|simple\s+difference|simple\s+example|example\s+do|aur\s+kya|explain\s+further|kuch\s+aur)"
        )

        # Priority 3: Topic / Intent classification patterns
        self._sathi_topics = re.compile(
            r"(?i)\b(difference|compare|comparison|versus|vs\b|better|trade-off|tradeoff|trade\s+offs|pros\s+and\s+cons|fayde|nuksan|architecture|scalability|internals|database\s+indexing|concurrency)\b"
        )
        self._dost_topics = re.compile(
            r"(?i)\b(kya\s+chal\s+raha\s+hai|mood|stress|kaise\s+ho|kya\s+haal|bore|kuch\s+sunao|bhai\b|kahani|dabba)\b"
        )

    def reset(self) -> None:
        """Reset conversation ownership state."""
        self.active_bot = None

    def route(self, raw_text: str | None) -> RouteDecision:
        """Evaluate user utterance and return the selected bot responder.

        Args:
            raw_text: The user's transcribed or typed speech input.

        Returns:
            RouteDecision: Typed routing target, reason, and confidence.
        """
        if not raw_text or not isinstance(raw_text, str):
            target = self.active_bot or self.default_target
            return RouteDecision(
                target=target,
                reason="empty_input",
                confidence=0.50,
                raw_text=str(raw_text) if raw_text is not None else "",
                cleaned_text="",
            )

        cleaned = normalize_text(raw_text)
        if not cleaned:
            target = self.active_bot or self.default_target
            return RouteDecision(
                target=target,
                reason="empty_input",
                confidence=0.50,
                raw_text=raw_text,
                cleaned_text="",
            )

        # Priority 1: Check collaborative "both" address
        if self._both_explicit.search(cleaned):
            target = "dost"
            self.active_bot = target
            return RouteDecision(
                target=target,
                reason="collaborative_deferred",
                confidence=0.70,
                raw_text=raw_text,
                cleaned_text=cleaned,
            )

        # Priority 1: Explicit addressing (Dost vs Sathi)
        dost_match = self._dost_explicit.search(cleaned)
        sathi_match = self._sathi_explicit.search(cleaned)

        if dost_match and not sathi_match:
            self.active_bot = "dost"
            return RouteDecision(
                target="dost",
                reason="explicit_address",
                confidence=1.00,
                raw_text=raw_text,
                cleaned_text=cleaned,
            )
        if sathi_match and not dost_match:
            self.active_bot = "sathi"
            return RouteDecision(
                target="sathi",
                reason="explicit_address",
                confidence=1.00,
                raw_text=raw_text,
                cleaned_text=cleaned,
            )

        # Priority 2: Conversation ownership (continuation turns)
        if self.active_bot is not None:
            words = cleaned.split()
            is_followup = (
                self._followup_starters.search(cleaned) is not None
                or self._followup_short.search(cleaned) is not None
                or len(words) <= 4
            )
            if is_followup:
                return RouteDecision(
                    target=self.active_bot,
                    reason="conversation_owner",
                    confidence=0.85,
                    raw_text=raw_text,
                    cleaned_text=cleaned,
                )

        # Priority 3: Topic / Intent classification
        if self._sathi_topics.search(cleaned):
            self.active_bot = "sathi"
            return RouteDecision(
                target="sathi",
                reason="technical_comparison",
                confidence=0.75,
                raw_text=raw_text,
                cleaned_text=cleaned,
            )

        if self._dost_topics.search(cleaned):
            self.active_bot = "dost"
            return RouteDecision(
                target="dost",
                reason="casual_query",
                confidence=0.75,
                raw_text=raw_text,
                cleaned_text=cleaned,
            )

        # Priority 4: Deterministic default route (AI Dost)
        self.active_bot = self.default_target
        return RouteDecision(
            target=self.default_target,
            reason="general_default",
            confidence=0.50,
            raw_text=raw_text,
            cleaned_text=cleaned,
        )
