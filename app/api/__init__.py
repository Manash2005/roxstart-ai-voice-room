"""HTTP API layer for Roxstar AI Voice Room."""

from typing import TYPE_CHECKING

from app.api.token import (
    TokenRequest,
    TokenValidationError,
    generate_livekit_token,
    validate_token_request,
)

if TYPE_CHECKING:
    from app.api.server import create_app, run_api_server


def __getattr__(name: str):
    if name in ("create_app", "run_api_server"):
        from app.api import server

        return getattr(server, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "TokenRequest",
    "TokenValidationError",
    "create_app",
    "generate_livekit_token",
    "run_api_server",
    "validate_token_request",
]
