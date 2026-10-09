"""Lightweight HTTP API server for Roxstar AI Voice Room.

Provides health checks and secure token generation endpoints for frontend clients.
Runs on aiohttp (already installed as part of the LiveKit stack) with ₹0 added dependencies.
"""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Awaitable, Callable

from aiohttp import web

from app.api.token import (
    TokenValidationError,
    generate_livekit_token,
    validate_token_request,
)
from app.config import Settings, get_settings

logger = logging.getLogger("roxstar.api")

# Strongly-typed aiohttp AppKey for application settings
SETTINGS_KEY: web.AppKey[Settings] = web.AppKey("settings", Settings)


def create_cors_middleware(
    settings: Settings,
) -> Callable[
    [web.Request, Callable[[web.Request], Awaitable[web.StreamResponse]]],
    Awaitable[web.StreamResponse],
]:
    """Create a scoped CORS middleware based on configured allowed origins.

    Restricts Access-Control-Allow-Origin strictly to configured frontend origins
    (e.g., http://localhost:5173) without using wildcards.
    """
    allowed_origins = set(settings.allowed_origins)

    @web.middleware
    async def cors_middleware(
        request: web.Request,
        handler: Callable[[web.Request], Awaitable[web.StreamResponse]],
    ) -> web.StreamResponse:
        origin = request.headers.get("Origin")

        # Handle preflight OPTIONS request
        if request.method == "OPTIONS":
            if origin and origin in allowed_origins:
                return web.Response(
                    status=204,
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Authorization",
                        "Access-Control-Max-Age": "86400",
                    },
                )
            if origin:
                # Disallowed origin requesting preflight
                return web.Response(status=403, text="CORS origin not allowed.")
            return web.Response(
                status=204,
                headers={"Allow": "GET, POST, OPTIONS"},
            )

        # Process actual request
        try:
            response = await handler(request)
        except web.HTTPException as exc:
            response = exc

        # Attach CORS headers if origin is authorized
        if origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization"
            )

        return response

    return cors_middleware


async def handle_health(request: web.Request) -> web.Response:
    """GET /health - Service health verification endpoint."""
    return web.json_response(
        {
            "status": "healthy",
            "service": "roxstar-voice-api",
            "version": "0.1.0",
        }
    )


async def handle_create_token(request: web.Request) -> web.Response:
    """POST /api/token - Issue a cryptographically signed LiveKit room token.

    Expects JSON body:
    {
        "room": "roxstar-demo",
        "identity": "user-unique-id",
        "name": "Manash"
    }

    Returns:
    {
        "token": "...",
        "url": "wss://..."
    }
    """
    settings: Settings = request.app[SETTINGS_KEY]

    # Parse and validate JSON request body
    try:
        body = await request.json()
    except (json.JSONDecodeError, web.HTTPBadRequest, ValueError, TypeError):
        return web.json_response(
            {"error": "Invalid JSON body in request."},
            status=400,
        )

    # Validate input data and security constraints
    try:
        token_request = validate_token_request(body)
    except TokenValidationError as err:
        return web.json_response(
            {"error": str(err)},
            status=400,
        )

    # Generate token using installed LiveKit SDK
    try:
        jwt_token = generate_livekit_token(
            request=token_request,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        )
    except Exception:
        logger.exception("Failed to generate LiveKit access token")
        return web.json_response(
            {
                "error": "Failed to generate room token. Please check server configuration."
            },
            status=500,
        )

    # Return signed token and WebSocket connection URL
    # Secrets (LIVEKIT_API_SECRET, OPENROUTER_API_KEY, GROQ_API_KEY) are NEVER returned
    return web.json_response(
        {
            "token": jwt_token,
            "url": settings.livekit_url,
        },
        status=200,
    )


def create_app(settings: Settings | None = None) -> web.Application:
    """Create and configure the aiohttp web application.

    Args:
        settings: Optional Settings instance. If omitted, loaded from environment.

    Returns:
        web.Application: Configured application with routes and CORS middleware.
    """
    app_settings = settings or get_settings()

    app = web.Application(
        middlewares=[create_cors_middleware(app_settings)],
    )
    app[SETTINGS_KEY] = app_settings

    # Register API endpoints
    app.router.add_get("/health", handle_health)
    app.router.add_post("/api/token", handle_create_token)

    return app


def run_api_server(
    host: str | None = None,
    port: int | None = None,
    settings: Settings | None = None,
) -> None:
    """Run the API server synchronously via aiohttp.web.run_app."""
    app_settings = settings or get_settings()
    server_host = host or app_settings.api_host
    server_port = port if port is not None else app_settings.api_port

    logging.basicConfig(
        level=getattr(logging, app_settings.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info(
        "Starting Roxstar Voice API on http://%s:%d (Allowed CORS Origins: %s)",
        server_host,
        server_port,
        app_settings.allowed_origins,
    )

    app = create_app(app_settings)
    web.run_app(app, host=server_host, port=server_port)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Roxstar AI Voice Room HTTP API Server"
    )
    parser.add_argument(
        "--host", default=None, help="Host interface to bind (default: from config/env)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to listen on (default: from config/env)",
    )
    args = parser.parse_args()

    run_api_server(host=args.host, port=args.port)
