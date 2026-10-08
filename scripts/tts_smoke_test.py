"""Local smoke test script for Piper TTS Hindi/Hinglish synthesis.

Tests the LiveKit TTS adapter end-to-end with real model inference:
1. Hindi Devanagari: "नमस्ते! आज आप कैसे हैं?"
2. Roman Hindi: "Aaj kya kar rahe ho?"
3. Hinglish: "Haan, basically iska main idea ye hai ki hum context maintain karte hain."
4. English: "Can you explain this in simple terms?"

Verifies that the generated audio frames can be consumed by LiveKit's TTS pipeline.
"""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

from app.config import Settings
from app.personas import AI_DOST_GREETING
from app.tts import create_tts

TEST_CASES = [
    (
        "Hindi Devanagari",
        "नमस्ते! आज आप कैसे हैं?",
    ),
    (
        "Roman Hindi",
        "Aaj kya kar rahe ho?",
    ),
    (
        "Hinglish",
        "Haan, basically iska main idea ye hai ki hum context maintain karte hain.",
    ),
    (
        "English",
        "Can you explain this in simple terms?",
    ),
    (
        "AI Dost Greeting",
        AI_DOST_GREETING,
    ),
]


async def run_smoke_test() -> None:
    print("=" * 70)
    print("ROXSTAR AI VOICE ROOM - TTS SMOKE TEST (Checkpoint 2)")
    print("=" * 70)

    # Use default settings with local model
    settings = Settings(
        livekit_url=os.getenv("LIVEKIT_URL", "wss://placeholder.livekit.cloud"),
        livekit_api_key=os.getenv("LIVEKIT_API_KEY", "placeholder_key"),
        livekit_api_secret=os.getenv("LIVEKIT_API_SECRET", "placeholder_secret"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", "placeholder_or_key"),
        groq_api_key=os.getenv("GROQ_API_KEY", "placeholder_groq_key"),
        tts_model=os.getenv("TTS_MODEL", "hi_IN-rohan-medium"),
        tts_sample_rate=int(os.getenv("TTS_SAMPLE_RATE", "22050")),
        tts_auto_download=True,
    )

    print(f"Model: {settings.tts_model}")
    print(f"Sample Rate: {settings.tts_sample_rate} Hz")
    print(f"Auto-download: {settings.tts_auto_download}")
    print("-" * 70)

    tts_engine = create_tts(settings)
    print(f"Initialized TTS adapter: {type(tts_engine).__name__}")
    print(f"Streaming capability: {tts_engine.capabilities.streaming}")
    print("-" * 70)

    output_dir = Path("output_audio")
    output_dir.mkdir(exist_ok=True)

    total_start = time.perf_counter()

    for idx, (category, text) in enumerate(TEST_CASES, start=1):
        print(f"\n[{idx}/{len(TEST_CASES)}] Category: {category}")
        print(f'Input text: "{text}"')

        t0 = time.perf_counter()
        stream = tts_engine.synthesize(text)

        frames = []
        async for ev in stream:
            frames.append(ev.frame)

        elapsed = time.perf_counter() - t0
        total_audio_duration = sum(f.duration for f in frames)
        total_samples = sum(f.samples_per_channel for f in frames)

        print(f"  -> Generated {len(frames)} LiveKit AudioFrame(s)")
        print(f"  -> Total audio duration: {total_audio_duration:.2f} seconds")
        print(f"  -> Total samples: {total_samples}")
        print(
            f"  -> Synthesis elapsed time: {elapsed:.3f} seconds (RTF: {elapsed / max(total_audio_duration, 0.001):.2f}x)"
        )

        assert len(frames) > 0, f"No audio frames generated for {category}!"
        assert total_audio_duration > 0.0, f"Zero duration audio for {category}!"

        # Verify frame parameters match LiveKit expectations
        sample_frame = frames[0]
        assert sample_frame.sample_rate == settings.tts_sample_rate
        assert sample_frame.num_channels == 1

        await stream.aclose()

    total_time = time.perf_counter() - total_start
    print("\n" + "=" * 70)
    print(
        f"SMOKE TEST SUCCESSFUL: All {len(TEST_CASES)} categories synthesized in {total_time:.2f}s"
    )
    print("=" * 70)


def main() -> None:
    asyncio.run(run_smoke_test())


if __name__ == "__main__":
    main()
