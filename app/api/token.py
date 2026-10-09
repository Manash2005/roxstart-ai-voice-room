"""LiveKit AccessToken generation and validation service.

Issues secure, constrained LiveKit WebRTC access tokens for frontend clients
without ever exposing the LiveKit API secret.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from livekit.api import AccessToken, VideoGrants


class TokenValidationError(ValueError):
    """Raised when token request parameters fail security or format validation."""


# Allowed character patterns for room and participant identity
_ROOM_NAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{1,128}$")
_IDENTITY_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.:@]{1,128}$")
_MAX_NAME_LENGTH = 128
_DISALLOWED_PRIVILEGE_KEYS = {
    "permissions",
    "grants",
    "admin",
    "role",
    "is_admin",
    "video",
    "sip",
}


@dataclass(frozen=True)
class TokenRequest:
    """Validated input parameters for issuing a room access token."""

    room: str
    identity: str
    name: str


def validate_token_request(data: Any) -> TokenRequest:
    """Validate and sanitize token request data.

    Args:
        data: Raw parsed JSON body from client.

    Returns:
        TokenRequest: Strongly-typed, validated request parameters.

    Raises:
        TokenValidationError: If any field is missing, invalid, or client attempts
                              to inject arbitrary permissions.
    """
    if not isinstance(data, dict):
        raise TokenValidationError("Request body must be a JSON object.")

    # Reject any client-supplied permission or grant overrides
    injected_privileges = [k for k in data if k.lower() in _DISALLOWED_PRIVILEGE_KEYS]
    if injected_privileges:
        raise TokenValidationError(
            f"Client-supplied permission overrides are prohibited: {', '.join(injected_privileges)}."
        )

    # Validate room name
    room = data.get("room")
    if not isinstance(room, str):
        raise TokenValidationError("Field 'room' is required and must be a string.")
    room = room.strip()
    if not room:
        raise TokenValidationError("Field 'room' must not be empty.")
    if not _ROOM_NAME_REGEX.match(room):
        raise TokenValidationError(
            "Field 'room' must be 1-128 characters and contain only alphanumeric, dash, underscore, or period characters."
        )

    # Validate participant identity
    identity = data.get("identity")
    if not isinstance(identity, str):
        raise TokenValidationError("Field 'identity' is required and must be a string.")
    identity = identity.strip()
    if not identity:
        raise TokenValidationError("Field 'identity' must not be empty.")
    if not _IDENTITY_REGEX.match(identity):
        raise TokenValidationError(
            "Field 'identity' must be 1-128 characters and contain only alphanumeric, dash, underscore, colon, at, or period characters."
        )

    # Validate display name
    name = data.get("name")
    if not isinstance(name, str):
        raise TokenValidationError("Field 'name' is required and must be a string.")
    name = name.strip()
    if not name:
        raise TokenValidationError("Field 'name' must not be empty.")
    if len(name) > _MAX_NAME_LENGTH:
        raise TokenValidationError(
            f"Field 'name' must not exceed {_MAX_NAME_LENGTH} characters."
        )
    if any(c in "\r\n\t\x00" for c in name):
        raise TokenValidationError(
            "Field 'name' must not contain control characters or newlines."
        )

    return TokenRequest(room=room, identity=identity, name=name)


def generate_livekit_token(
    request: TokenRequest,
    api_key: str,
    api_secret: str,
) -> str:
    """Generate a cryptographically signed LiveKit AccessToken for a room participant.

    The backend grants ONLY minimum necessary permissions:
    - Joining the requested room (room_join=True, room=room)
    - Publishing microphone tracks (can_publish=True)
    - Subscribing to AI and peer audio tracks (can_subscribe=True)
    - Publishing data packets for text chat (can_publish_data=True)

    No administrative or management permissions are granted.

    Args:
        request: Validated TokenRequest instance.
        api_key: LiveKit API key.
        api_secret: LiveKit API secret (used for HMAC signing, never returned).

    Returns:
        str: Cryptographically signed JWT token string.
    """
    grants = VideoGrants(
        room_join=True,
        room=request.room,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
        room_admin=False,
        room_record=False,
        ingress_admin=False,
    )

    token = (
        AccessToken(api_key, api_secret)
        .with_identity(request.identity)
        .with_name(request.name)
        .with_grants(grants)
    )

    return token.to_jwt()
