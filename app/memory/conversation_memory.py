"""In-memory session conversation memory (Checkpoint 6).

Provides bounded, thread-safe, in-memory conversation history shared across
both AI participants (AI Dost and AI Sathi) and all human participants in the room.
"""

from __future__ import annotations

from app.logging import get_logger
from app.memory.turn import ConversationTurn, InputType

logger = get_logger(__name__)


class ConversationMemory:
    """Bounded in-memory session conversation memory.

    Maintains recent conversation turns across all human and AI participants
    in the LiveKit room, providing shared short-term context without requiring
    an external database or vector store.
    """

    def __init__(self, max_turns: int = 12) -> None:
        self.max_turns = max_turns
        self._turns: list[ConversationTurn] = []

    def add_turn(self, turn: ConversationTurn) -> None:
        """Append a turn and evict oldest if exceeding max_turns."""
        if not turn.text or not turn.text.strip():
            return

        self._turns.append(turn)
        if len(self._turns) > self.max_turns:
            evicted = self._turns.pop(0)
            logger.debug(
                "Evicted oldest turn from memory (speaker: %s, text: '%.30s...')",
                evicted.speaker_name,
                evicted.text,
            )

    def add_human_turn(
        self,
        speaker_id: str,
        speaker_name: str,
        text: str,
        input_type: InputType = "voice",
        target_bot: str | None = None,
    ) -> ConversationTurn:
        """Convenience helper to record a human user turn."""
        turn = ConversationTurn(
            speaker_id=speaker_id or "human",
            speaker_name=speaker_name or "User",
            role="human",
            text=text.strip(),
            input_type=input_type,
            target_bot=target_bot,
        )
        self.add_turn(turn)
        return turn

    def add_bot_turn(
        self,
        bot_id: str,
        bot_name: str,
        text: str,
        input_type: InputType = "voice",
    ) -> ConversationTurn:
        """Convenience helper to record an AI bot response turn."""
        turn = ConversationTurn(
            speaker_id=bot_id,
            speaker_name=bot_name,
            role="bot",
            text=text.strip(),
            input_type=input_type,
            target_bot=bot_id.replace("ai-", ""),
        )
        self.add_turn(turn)
        return turn

    def get_recent_turns(self, limit: int | None = None) -> list[ConversationTurn]:
        """Return the most recent turns up to limit."""
        if limit is None or limit >= len(self._turns):
            return list(self._turns)
        return list(self._turns[-limit:])

    def format_context_for_llm(
        self, max_turns: int | None = None, exclude_last: bool = False
    ) -> str:
        """Format recent turns into a structured text block for LLM context injection.

        Args:
            max_turns: Maximum number of recent turns to include.
            exclude_last: If True, omits the most recent turn (e.g. current in-flight turn).

        Returns:
            str: Markdown formatted list of conversation turns, or empty string if no history.
        """
        turns = self._turns[:-1] if (exclude_last and self._turns) else self._turns
        if not turns:
            return ""

        effective_limit = max_turns or self.max_turns
        selected = turns[-effective_limit:]
        lines = [turn.format_line() for turn in selected]
        return "\n".join(lines)

    def get_speaker_turns(self, speaker_id: str) -> list[ConversationTurn]:
        """Retrieve all recorded turns by a specific participant."""
        return [t for t in self._turns if t.speaker_id == speaker_id]

    def clear(self) -> None:
        """Reset conversation memory (used on room session end)."""
        self._turns.clear()

    def __len__(self) -> int:
        return len(self._turns)
