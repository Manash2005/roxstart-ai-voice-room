"""Structured latency measurement and instrumentation for Roxstar AI Voice Room.

Measures each stage of the voice assistant pipeline with monotonic high-precision timing:
1. STT duration (voice turn completion to final transcript)
2. Routing duration (classifier & arbitrator execution)
3. LLM generation duration (first-token / generation completion)
4. TTS first-audio duration (synthesis start to first audio chunk)
5. Total turn-to-first-audio latency
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal

from app.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TurnLatencyTracker:
    """Tracks high-precision monotonic timestamps across a single voice turn.

    Zero secrets, keys, or sensitive text are stored or logged.
    """

    turn_id: str
    bot_target: Literal["dost", "sathi"] = "dost"

    # Monotonic timestamps (seconds)
    turn_detected_at: float = field(default_factory=time.perf_counter)
    stt_start_at: float | None = None
    stt_end_at: float | None = None
    routing_start_at: float | None = None
    routing_end_at: float | None = None
    llm_start_at: float | None = None
    llm_first_token_at: float | None = None
    llm_end_at: float | None = None
    tts_start_at: float | None = None
    tts_first_audio_at: float | None = None
    first_audio_published_at: float | None = None

    def mark_stt_start(self) -> None:
        """Record the start of speech-to-text recognition."""
        self.stt_start_at = time.perf_counter()

    def mark_stt_end(self) -> None:
        """Record the completion of speech-to-text transcription."""
        self.stt_end_at = time.perf_counter()

    def mark_routing_start(self) -> None:
        """Record the start of turn routing decision."""
        self.routing_start_at = time.perf_counter()

    def mark_routing_end(self, bot: Literal["dost", "sathi"]) -> None:
        """Record completion of routing decision and selected bot."""
        self.routing_end_at = time.perf_counter()
        self.bot_target = bot

    def mark_llm_start(self) -> None:
        """Record start of LLM generation."""
        self.llm_start_at = time.perf_counter()

    def mark_llm_first_token(self) -> None:
        """Record receipt of first LLM token/chunk."""
        self.llm_first_token_at = time.perf_counter()

    def mark_llm_end(self) -> None:
        """Record completion of LLM response generation."""
        self.llm_end_at = time.perf_counter()
        if self.llm_first_token_at is None:
            self.llm_first_token_at = self.llm_end_at

    def mark_tts_start(self) -> None:
        """Record start of TTS audio synthesis."""
        self.tts_start_at = time.perf_counter()

    def mark_tts_first_audio(self) -> None:
        """Record when first playable PCM audio chunk becomes available."""
        self.tts_first_audio_at = time.perf_counter()
        if self.first_audio_published_at is None:
            self.first_audio_published_at = self.tts_first_audio_at

    def mark_first_audio_published(self) -> None:
        """Record when first audio frame is published to the room."""
        self.first_audio_published_at = time.perf_counter()

    # --- Calculated Duration Helpers (milliseconds) ---

    @property
    def stt_ms(self) -> float | None:
        """STT duration in milliseconds."""
        if self.stt_start_at is not None and self.stt_end_at is not None:
            return round((self.stt_end_at - self.stt_start_at) * 1000, 1)
        return None

    @property
    def routing_ms(self) -> float | None:
        """Routing duration in milliseconds."""
        if self.routing_start_at is not None and self.routing_end_at is not None:
            return round((self.routing_end_at - self.routing_start_at) * 1000, 1)
        return None

    @property
    def llm_ms(self) -> float | None:
        """LLM first-output or completion duration in milliseconds."""
        ref = self.llm_first_token_at or self.llm_end_at
        if self.llm_start_at is not None and ref is not None:
            return round((ref - self.llm_start_at) * 1000, 1)
        return None

    @property
    def tts_first_audio_ms(self) -> float | None:
        """TTS first-audio synthesis duration in milliseconds."""
        if self.tts_start_at is not None and self.tts_first_audio_at is not None:
            return round((self.tts_first_audio_at - self.tts_start_at) * 1000, 1)
        return None

    @property
    def total_first_audio_ms(self) -> float | None:
        """Total duration from turn detection to first audio playback in milliseconds."""
        ref = self.first_audio_published_at or self.tts_first_audio_at
        if self.turn_detected_at is not None and ref is not None:
            return round((ref - self.turn_detected_at) * 1000, 1)
        return None

    def format_summary(self) -> str:
        """Produce a structured log string with all measured durations."""
        parts = [
            f"turn={self.turn_id}",
            f"bot={self.bot_target}",
        ]
        if self.stt_ms is not None:
            parts.append(f"stt={self.stt_ms:.0f}ms")
        if self.routing_ms is not None:
            parts.append(f"routing={self.routing_ms:.0f}ms")
        if self.llm_ms is not None:
            parts.append(f"llm={self.llm_ms:.0f}ms")
        if self.tts_first_audio_ms is not None:
            parts.append(f"tts_first={self.tts_first_audio_ms:.0f}ms")
        if self.total_first_audio_ms is not None:
            parts.append(f"total_first_audio={self.total_first_audio_ms:.0f}ms")

        return " | ".join(parts)

    def log_summary(self) -> None:
        """Emit structured log for monitoring."""
        summary = self.format_summary()
        logger.info("[LATENCY] %s", summary)
