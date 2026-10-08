"""Secondary LiveKit participant connection management (Checkpoint 5A).

Provides helpers to create, connect, and disconnect a secondary WebRTC participant
in the LiveKit room (e.g. 'ai-sathi') alongside the primary worker participant ('ai-dost').
"""

from __future__ import annotations

import asyncio

from livekit import api, rtc

from app.logging import get_logger

logger = get_logger(__name__)


def create_participant_token(
    api_key: str,
    api_secret: str,
    room_name: str,
    identity: str = "ai-sathi",
    name: str = "AI Sathi",
    kind: str = "agent",
) -> str:
    """Generate a LiveKit JWT access token locally for a participant.

    Args:
        api_key: LiveKit API key.
        api_secret: LiveKit API secret.
        room_name: Name of the room to join.
        identity: Unique participant identity string (default: 'ai-sathi').
        name: Human-readable display name (default: 'AI Sathi').
        kind: Participant kind ('agent' ensures standard participants are distinguished).

    Returns:
        str: Encoded JWT access token.
    """
    token_builder = (
        api.AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_name(name)
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
    )
    if kind:
        token_builder = token_builder.with_kind(kind)  # type: ignore[arg-type]
    return token_builder.to_jwt()


async def connect_secondary_participant(
    livekit_url: str,
    api_key: str,
    api_secret: str,
    room_name: str,
    identity: str = "ai-sathi",
    name: str = "AI Sathi",
    kind: str = "agent",
    auto_subscribe: bool = False,
) -> rtc.Room:
    """Connect a secondary WebRTC participant to the same LiveKit room.

    Args:
        livekit_url: LiveKit server WebSocket URL.
        api_key: LiveKit API key.
        api_secret: LiveKit API secret.
        room_name: Target room name.
        identity: Participant identity (default: 'ai-sathi').
        name: Display name (default: 'AI Sathi').
        kind: Participant kind (default: 'agent').
        auto_subscribe: Whether to subscribe to other participants' tracks (default: False).

    Returns:
        rtc.Room: Connected LiveKit Room instance for the secondary participant.
    """
    token = create_participant_token(
        api_key=api_key,
        api_secret=api_secret,
        room_name=room_name,
        identity=identity,
        name=name,
        kind=kind,
    )

    room = rtc.Room()
    room_options = rtc.RoomOptions(
        auto_subscribe=auto_subscribe,
    )

    logger.info(
        "Connecting secondary participant '%s' (identity: %s) to room '%s'...",
        name,
        identity,
        room_name,
    )
    await room.connect(livekit_url, token, options=room_options)
    logger.info(
        "Secondary participant '%s' connected successfully (SID: %s).",
        identity,
        getattr(room.local_participant, "sid", "unknown"),
    )
    return room


async def disconnect_secondary_participant(room: rtc.Room | None) -> None:
    """Safely disconnect a secondary participant room without raising exceptions."""
    if room is None:
        return

    try:
        if room.isconnected():
            logger.info("Disconnecting secondary participant room...")
            await room.disconnect()
            logger.info("Secondary participant room disconnected.")
    except (RuntimeError, TimeoutError, asyncio.CancelledError) as e:
        logger.warning("Error during secondary participant disconnect: %s", e)
