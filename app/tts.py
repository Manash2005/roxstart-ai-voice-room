"""Local Text-to-Speech (TTS) adapter for Roxstar AI Voice Room Assistant.

Checkpoint 2: Purely local, ₹0-cost open-source TTS implementation using Piper TTS
with native Indian Hindi/Hinglish voices (trained on IIT Madras Indic TTS dataset).
"""

from __future__ import annotations

import asyncio
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from livekit.agents import (
    DEFAULT_API_CONNECT_OPTIONS,
    APIConnectOptions,
    tts,
)
from livekit.agents.tts import AudioEmitter

from app.config import Settings, get_settings
from app.logging import get_logger

logger = get_logger(__name__)

# Base Hugging Face repository for official Piper voices
_PIPER_VOICES_BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

# Standard voice catalog mapping
_SUPPORTED_VOICE_PATHS: dict[str, str] = {
    "hi_IN-rohan-medium": "hi/hi_IN/rohan/medium/hi_IN-rohan-medium",
    "hi_IN-pratham-medium": "hi/hi_IN/pratham/medium/hi_IN-pratham-medium",
}


def download_piper_model(
    model_name: str, target_dir: Path | str = "models"
) -> tuple[Path, Path]:
    """Ensure the specified Piper ONNX model and config files exist locally.

    Downloads model files from Hugging Face on demand if not present.

    Args:
        model_name: Voice model identifier (e.g. 'hi_IN-rohan-medium').
        target_dir: Local directory where model files will be saved.

    Returns:
        tuple[Path, Path]: (model_path, config_path)
    """
    dest_dir = Path(target_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    onnx_file = dest_dir / f"{model_name}.onnx"
    json_file = dest_dir / f"{model_name}.onnx.json"

    if onnx_file.exists() and json_file.exists():
        logger.debug("Piper model files already present locally: %s", onnx_file)
        return onnx_file, json_file

    relative_path = _SUPPORTED_VOICE_PATHS.get(
        model_name, f"hi/hi_IN/{model_name.split('-')[1]}/medium/{model_name}"
    )
    onnx_url = f"{_PIPER_VOICES_BASE_URL}/{relative_path}.onnx"
    json_url = f"{_PIPER_VOICES_BASE_URL}/{relative_path}.onnx.json"

    if not onnx_file.exists():
        logger.info(
            "Downloading Piper TTS model '%s' from Hugging Face (~63 MB)...",
            model_name,
        )
        urllib.request.urlretrieve(onnx_url, onnx_file)
        logger.info("Piper model downloaded successfully: %s", onnx_file)

    if not json_file.exists():
        logger.info("Downloading Piper TTS model config for '%s'...", model_name)
        urllib.request.urlretrieve(json_url, json_file)
        logger.info("Piper model config downloaded successfully: %s", json_file)

    return onnx_file, json_file


class _PiperChunkedStream(tts.ChunkedStream):
    """Chunked audio stream synthesizing text using local Piper TTS."""

    def __init__(
        self,
        *,
        tts_instance: PiperTTS,
        input_text: str,
        conn_options: APIConnectOptions,
    ) -> None:
        super().__init__(
            tts=tts_instance,
            input_text=input_text,
            conn_options=conn_options,
        )
        self._piper_tts = tts_instance

    async def _run(self, output_emitter: AudioEmitter) -> None:
        """Synthesize text in a background thread and push PCM audio to LiveKit.

        Checkpoint 6.5 optimization: Streams sentence chunks to output_emitter
        as soon as each sentence finishes synthesis, rather than waiting for the entire
        paragraph to complete. This dramatically reduces first-audio playback latency.
        """
        # Always initialize LiveKit AudioEmitter first so it is marked started
        req_id = f"piper_{uuid.uuid4().hex[:8]}"
        output_emitter.initialize(
            request_id=req_id,
            sample_rate=self._piper_tts.sample_rate,
            num_channels=self._piper_tts.num_channels,
            mime_type="audio/pcm",
        )

        text = self.input_text.strip()
        if not text:
            output_emitter.flush()
            return

        loop = asyncio.get_running_loop()
        chunk_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        worker_error: list[Exception] = []

        def _synthesize_worker() -> None:
            try:
                voice = self._piper_tts._get_or_load_voice()
                if hasattr(voice, "synthesize"):
                    for chunk in voice.synthesize(text):
                        raw = getattr(chunk, "audio_int16_bytes", b"")
                        if raw:
                            loop.call_soon_threadsafe(chunk_queue.put_nowait, raw)
                else:
                    raw = self._piper_tts.synthesize_raw_pcm(text)
                    if raw:
                        loop.call_soon_threadsafe(chunk_queue.put_nowait, raw)
            except (RuntimeError, ValueError, OSError, AttributeError) as exc:
                logger.error("Error in Piper TTS synthesis worker: %s", exc)
                worker_error.append(exc)
            finally:
                loop.call_soon_threadsafe(chunk_queue.put_nowait, None)

        worker_task = asyncio.create_task(asyncio.to_thread(_synthesize_worker))
        has_audio = False

        try:
            while True:
                chunk = await chunk_queue.get()
                if chunk is None:
                    break
                output_emitter.push(chunk)
                has_audio = True

            await worker_task
            if worker_error:
                raise worker_error[0]

            if has_audio:
                output_emitter.flush()
            else:
                logger.warning("Piper TTS produced empty audio for text: '%s'", text)
                output_emitter.flush()
        except Exception as e:
            logger.error("Error synthesizing speech with Piper TTS: %s", e)
            raise


class PiperTTS(tts.TTS):
    """Local, open-source Text-to-Speech engine using Piper ONNX for LiveKit.

    Features:
    - ₹0 cost: Runs 100% locally on CPU or Apple Silicon.
    - Zero external network requests after model weights are downloaded.
    - Fast: <100ms inference time on Apple Silicon.
    - High quality: Native Indian accent trained on IIT Madras Indic TTS dataset.
    - Model is loaded once and reused across all synthesis calls.
    """

    def __init__(
        self,
        *,
        model_path: Path | str | None = None,
        config_path: Path | str | None = None,
        model_name: str = "hi_IN-rohan-medium",
        sample_rate: int = 22050,
        auto_download: bool = True,
        voice_instance: Any | None = None,
    ) -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=1,
        )
        self._model_name = model_name
        self._model_path = Path(model_path) if model_path else None
        self._config_path = Path(config_path) if config_path else None
        self._auto_download = auto_download
        self._voice: Any | None = voice_instance
        self._load_lock = asyncio.Lock()

        # If voice_instance was provided (e.g., in unit tests), use its sample rate
        if self._voice is not None and hasattr(self._voice, "config"):
            self._sample_rate = self._voice.config.sample_rate

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_or_load_voice(self) -> Any:
        """Synchronously load and return the PiperVoice instance (loaded once)."""
        if self._voice is not None:
            return self._voice

        # Resolve model paths
        if self._model_path is None or not self._model_path.exists():
            if self._auto_download:
                onnx_p, json_p = download_piper_model(self._model_name)
                self._model_path = onnx_p
                self._config_path = json_p
            else:
                raise FileNotFoundError(
                    f"Piper model file not found at {self._model_path} "
                    f"and auto_download is disabled."
                )

        if self._config_path is None or not self._config_path.exists():
            candidate_config = Path(f"{self._model_path}.json")
            if candidate_config.exists():
                self._config_path = candidate_config

        logger.info(
            "Loading Piper TTS model once into memory from %s...",
            self._model_path,
        )
        from piper import PiperVoice

        self._voice = PiperVoice.load(
            str(self._model_path),
            config_path=str(self._config_path) if self._config_path else None,
        )
        self._sample_rate = self._voice.config.sample_rate
        logger.info(
            "Piper TTS model '%s' loaded successfully (sample_rate=%d)",
            self._model_name,
            self._sample_rate,
        )
        return self._voice

    def synthesize_raw_pcm(self, text: str) -> bytes:
        """Synthesize text into raw 16-bit PCM bytes (runs synchronously).

        Args:
            text: Input sentence in Hindi Devanagari, Roman Hindi, or Hinglish.

        Returns:
            bytes: Raw 16-bit mono PCM audio bytes.
        """
        voice = self._get_or_load_voice()
        chunks = list(voice.synthesize(text))
        return b"".join(c.audio_int16_bytes for c in chunks)

    def synthesize(
        self,
        text: str,
        *,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> tts.ChunkedStream:
        """Create a LiveKit ChunkedStream for speech synthesis.

        Args:
            text: Sentence to speak.
            conn_options: LiveKit API connection options.

        Returns:
            tts.ChunkedStream: Audio stream consumed by LiveKit AgentSession.
        """
        return _PiperChunkedStream(
            tts_instance=self,
            input_text=text,
            conn_options=conn_options,
        )


def create_tts(settings: Settings | None = None) -> tts.TTS:
    """Factory function for Text-to-Speech component.

    Checkpoint 2: Instantiates local, ₹0-cost Piper Hindi TTS.

    Args:
        settings: Application settings. If None, loaded from environment.

    Returns:
        tts.TTS: Initialized LiveKit TTS instance.
    """
    if settings is None:
        settings = get_settings()

    model_path = settings.tts_model_path if settings.tts_model_path else None
    config_path = settings.tts_config_path if settings.tts_config_path else None

    # Check default models directory if custom path not specified
    if not model_path:
        default_onnx = Path("models") / f"{settings.tts_model}.onnx"
        default_json = Path("models") / f"{settings.tts_model}.onnx.json"
        if default_onnx.exists():
            model_path = str(default_onnx)
            config_path = str(default_json)

    return PiperTTS(
        model_path=model_path,
        config_path=config_path,
        model_name=settings.tts_model,
        sample_rate=settings.tts_sample_rate,
        auto_download=settings.tts_auto_download,
    )
