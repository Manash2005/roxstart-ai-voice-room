#!/usr/bin/env bash
set -e

echo "=================================================="
echo " Starting Roxstar AI Voice Room (Render Deployment)"
echo "=================================================="

# 1. Start LiveKit Voice Agent Worker in background
echo "-> Starting LiveKit Agent Worker (ai-dost & ai-sathi)..."
python -m app.agent start &
AGENT_PID=$!

# Trap signals for graceful shutdown on Render deploys/restarts
cleanup() {
    echo "Received shutdown signal. Stopping worker (PID: $AGENT_PID)..."
    kill -TERM "$AGENT_PID" 2>/dev/null || true
    wait "$AGENT_PID" 2>/dev/null || true
    exit 0
}
trap cleanup SIGTERM SIGINT EXIT

# 2. Start HTTP API Server in foreground (binds to Render $PORT)
echo "-> Starting HTTP API Server on port ${PORT:-8080}..."
python -m app.api.server
