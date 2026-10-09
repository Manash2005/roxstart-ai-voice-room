"""Tests for Checkpoint 8A Backend API and LiveKit Token Layer."""

from __future__ import annotations

import jwt
import pytest
from aiohttp.test_utils import TestClient, TestServer

from app.api import create_app, generate_livekit_token, validate_token_request
from app.api.token import TokenRequest, TokenValidationError
from app.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    """Fixture providing mock settings with safe test credentials."""
    return Settings(
        livekit_url="wss://test-room.livekit.cloud",
        livekit_api_key="devkey-api-test",
        livekit_api_secret="secret1234567890abcdef1234567890abcdef",
        openrouter_api_key="sk-or-v1-mock",
        groq_api_key="gsk_mock",
        frontend_origin="http://localhost:5173",
        api_host="127.0.0.1",
        api_port=8080,
    )


@pytest.fixture
async def api_client(test_settings: Settings) -> TestClient:
    """Fixture providing an active aiohttp TestClient for API endpoints."""
    app = create_app(test_settings)
    client = TestClient(TestServer(app))
    await client.start_server()
    yield client
    await client.close()


# ==============================================================================
# 1. /health Endpoint Tests
# ==============================================================================


async def test_health_endpoint_returns_200(api_client: TestClient):
    """Verify that GET /health returns HTTP 200 with healthy status."""
    resp = await api_client.get("/health")
    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "roxstar-voice-api"


# ==============================================================================
# 2. Token Generation & Validation Unit Tests
# ==============================================================================


def test_validate_token_request_valid():
    """Verify successful validation for properly formatted payload."""
    payload = {
        "room": "roxstar-room-1",
        "identity": "user_42",
        "name": "Manash Swain",
    }
    req = validate_token_request(payload)
    assert req.room == "roxstar-room-1"
    assert req.identity == "user_42"
    assert req.name == "Manash Swain"


def test_validate_token_request_rejects_non_dict():
    """Verify rejection when payload is not a dictionary."""
    with pytest.raises(TokenValidationError, match="must be a JSON object"):
        validate_token_request(["invalid", "list"])


def test_validate_token_request_rejects_missing_or_empty_room():
    """Verify rejection when room is missing or empty."""
    with pytest.raises(TokenValidationError, match="Field 'room' is required"):
        validate_token_request({"identity": "u1", "name": "User"})

    with pytest.raises(TokenValidationError, match="Field 'room' must not be empty"):
        validate_token_request({"room": "   ", "identity": "u1", "name": "User"})


def test_validate_token_request_rejects_invalid_room_characters():
    """Verify rejection of illegal characters in room name."""
    with pytest.raises(TokenValidationError, match="contain only alphanumeric"):
        validate_token_request(
            {"room": "room$bad#chars!", "identity": "u1", "name": "User"}
        )


def test_validate_token_request_rejects_missing_or_empty_identity():
    """Verify rejection when identity is missing or empty."""
    with pytest.raises(TokenValidationError, match="Field 'identity' is required"):
        validate_token_request({"room": "valid-room", "name": "User"})

    with pytest.raises(
        TokenValidationError, match="Field 'identity' must not be empty"
    ):
        validate_token_request({"room": "valid-room", "identity": "  ", "name": "User"})


def test_validate_token_request_rejects_invalid_identity_characters():
    """Verify rejection of illegal characters in identity."""
    with pytest.raises(TokenValidationError, match="Field 'identity' must be 1-128"):
        validate_token_request(
            {"room": "valid-room", "identity": "bad id with spaces", "name": "User"}
        )


def test_validate_token_request_rejects_missing_or_empty_name():
    """Verify rejection when display name is missing or empty."""
    with pytest.raises(TokenValidationError, match="Field 'name' is required"):
        validate_token_request({"room": "valid-room", "identity": "u1"})

    with pytest.raises(TokenValidationError, match="Field 'name' must not be empty"):
        validate_token_request({"room": "valid-room", "identity": "u1", "name": "  "})


def test_validate_token_request_rejects_client_supplied_permissions():
    """Verify rejection if client attempts to pass arbitrary permission overrides."""
    payload = {
        "room": "demo",
        "identity": "u1",
        "name": "User",
        "admin": True,
    }
    with pytest.raises(
        TokenValidationError, match="permission overrides are prohibited"
    ):
        validate_token_request(payload)

    payload_grants = {
        "room": "demo",
        "identity": "u1",
        "name": "User",
        "permissions": {"can_publish": True},
    }
    with pytest.raises(
        TokenValidationError, match="permission overrides are prohibited"
    ):
        validate_token_request(payload_grants)


def test_generate_livekit_token_grants_and_claims(test_settings: Settings):
    """Verify JWT token claims and permissions generated by generate_livekit_token."""
    req = TokenRequest(room="engineering-sync", identity="emp-101", name="Alice")
    jwt_token = generate_livekit_token(
        request=req,
        api_key=test_settings.livekit_api_key,
        api_secret=test_settings.livekit_api_secret,
    )
    assert isinstance(jwt_token, str)

    # Decode claims without verification to inspect content
    claims = jwt.decode(jwt_token, options={"verify_signature": False})

    assert claims["sub"] == "emp-101"
    assert claims["name"] == "Alice"
    assert claims["iss"] == test_settings.livekit_api_key

    # Verify VideoGrants permissions
    video_grants = claims.get("video", {})
    assert video_grants["room"] == "engineering-sync"
    assert video_grants["roomJoin"] is True
    assert video_grants["canPublish"] is True
    assert video_grants["canSubscribe"] is True
    assert video_grants["canPublishData"] is True

    # Verify NO admin permissions were granted
    assert video_grants.get("roomAdmin") is not True
    assert video_grants.get("ingressAdmin") is not True


# ==============================================================================
# 3. POST /api/token HTTP Endpoint Integration Tests
# ==============================================================================


async def test_create_token_success(api_client: TestClient, test_settings: Settings):
    """Verify successful POST /api/token returns token and url, without exposing secrets."""
    payload = {
        "room": "roxstar-demo",
        "identity": "user-unique-id",
        "name": "Manash",
    }
    resp = await api_client.post("/api/token", json=payload)
    assert resp.status == 200

    data = await resp.json()
    assert "token" in data
    assert "url" in data
    assert data["url"] == test_settings.livekit_url

    # Security check: Secret must NEVER be present anywhere in the response
    assert test_settings.livekit_api_secret not in str(data)
    assert "secret" not in data
    assert "api_key" not in data

    # Verify JWT validity
    token_str = data["token"]
    claims = jwt.decode(token_str, options={"verify_signature": False})
    assert claims["sub"] == "user-unique-id"
    assert claims["name"] == "Manash"
    assert claims["video"]["room"] == "roxstar-demo"


async def test_create_token_missing_identity(api_client: TestClient):
    """Verify that omitting identity returns HTTP 400 Bad Request."""
    payload = {
        "room": "roxstar-demo",
        "name": "Manash",
    }
    resp = await api_client.post("/api/token", json=payload)
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data
    assert "identity" in data["error"].lower()


async def test_create_token_missing_room(api_client: TestClient):
    """Verify that omitting room returns HTTP 400 Bad Request."""
    payload = {
        "identity": "user-unique-id",
        "name": "Manash",
    }
    resp = await api_client.post("/api/token", json=payload)
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data
    assert "room" in data["error"].lower()


async def test_create_token_invalid_json(api_client: TestClient):
    """Verify that invalid/malformed JSON returns HTTP 400 Bad Request."""
    resp = await api_client.post(
        "/api/token",
        data="not-valid-json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data


async def test_create_token_rejects_injected_admin_privileges(api_client: TestClient):
    """Verify that requests attempting to inject admin permissions are rejected."""
    payload = {
        "room": "roxstar-demo",
        "identity": "user-unique-id",
        "name": "Manash",
        "admin": True,
    }
    resp = await api_client.post("/api/token", json=payload)
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data
    assert "permission" in data["error"].lower()


# ==============================================================================
# 4. CORS Behavior Tests
# ==============================================================================


async def test_cors_headers_with_allowed_origin(api_client: TestClient):
    """Verify that requests from configured FRONTEND_ORIGIN receive CORS headers."""
    headers = {"Origin": "http://localhost:5173"}
    resp = await api_client.get("/health", headers=headers)
    assert resp.status == 200
    assert resp.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    assert "GET, POST, OPTIONS" in resp.headers.get("Access-Control-Allow-Methods", "")


async def test_cors_headers_omitted_for_disallowed_origin(api_client: TestClient):
    """Verify that requests from an unauthorized origin do not receive CORS allow header."""
    headers = {"Origin": "http://malicious-site.com"}
    resp = await api_client.get("/health", headers=headers)
    assert resp.status == 200
    assert resp.headers.get("Access-Control-Allow-Origin") is None


async def test_cors_options_preflight_allowed_origin(api_client: TestClient):
    """Verify that OPTIONS preflight from allowed origin returns 204 with CORS headers."""
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
    }
    resp = await api_client.options("/api/token", headers=headers)
    assert resp.status == 204
    assert resp.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"
    assert "POST" in resp.headers.get("Access-Control-Allow-Methods", "")
    assert "Content-Type" in resp.headers.get("Access-Control-Allow-Headers", "")


async def test_cors_options_preflight_disallowed_origin(api_client: TestClient):
    """Verify that OPTIONS preflight from unauthorized origin is blocked (HTTP 403)."""
    headers = {
        "Origin": "http://unauthorized-domain.org",
        "Access-Control-Request-Method": "POST",
    }
    resp = await api_client.options("/api/token", headers=headers)
    assert resp.status == 403
    assert resp.headers.get("Access-Control-Allow-Origin") is None
