"""Arbitration and mutual exclusion module for two-bot voice rooms (Checkpoint 5).

Enforces that at most one bot may speak or own the response turn at any time,
preventing overlapping responses, race conditions, or duplicate speech.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from enum import Enum


class BotState(str, Enum):
    """Represents the operational state of the dual-bot response pipeline."""

    IDLE = "idle"
    RESPONDING = "responding"


class ResponseArbitrator:
    """Asyncio-safe response arbitrator enforcing mutual exclusion between bots."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._state: BotState = BotState.IDLE
        self._current_owner: str | None = None

    @property
    def state(self) -> BotState:
        """Current pipeline operational state (IDLE or RESPONDING)."""
        return self._state

    @property
    def current_owner(self) -> str | None:
        """Identifier of the bot currently holding response ownership."""
        return self._current_owner

    @property
    def is_responding(self) -> bool:
        """True if any bot is actively generating speech or responding."""
        return self._state == BotState.RESPONDING

    async def acquire(self, bot_id: str) -> bool:
        """Attempt to acquire exclusive response ownership for bot_id.

        Returns:
            bool: True if ownership was granted; False if another bot is already responding.
        """
        # If lock is already acquired, do not block: immediately reject to avoid race
        if self._lock.locked():
            return False

        await self._lock.acquire()
        self._state = BotState.RESPONDING
        self._current_owner = bot_id
        return True

    def release(self, bot_id: str) -> None:
        """Release exclusive response ownership if held by bot_id."""
        if self._lock.locked() and (self._current_owner == bot_id or not bot_id):
            self._state = BotState.IDLE
            self._current_owner = None
            self._lock.release()

    @asynccontextmanager
    async def response_scope(self, bot_id: str) -> AsyncIterator[bool]:
        """Context manager for acquiring and safely releasing response ownership."""
        acquired = await self.acquire(bot_id)
        try:
            yield acquired
        finally:
            if acquired:
                self.release(bot_id)
