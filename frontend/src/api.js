/**
 * API client helper for Roxstar AI Voice Room backend.
 * Connects to the lightweight Python HTTP API to request LiveKit access tokens.
 */

export function getApiBaseUrl() {
  const url = import.meta.env.VITE_API_URL || 'http://localhost:8080';
  return url.replace(/\/+$/, '');
}

/**
 * Request a cryptographically signed LiveKit room access token from the backend.
 *
 * @param {Object} params
 * @param {string} params.room - Room name (e.g. 'roxstar-demo')
 * @param {string} params.identity - Unique participant identity string
 * @param {string} params.name - User display name
 * @returns {Promise<{ token: string, url: string }>}
 */
export async function requestRoomToken({ room, identity, name }) {
  const baseUrl = getApiBaseUrl();
  const endpoint = `${baseUrl}/api/token`;

  let response;
  try {
    response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ room, identity, name }),
    });
  } catch {
    throw new Error(
      `Backend is unavailable. Cannot connect to API server at ${baseUrl}. Please ensure the server is running (uv run python -m app.api.server).`
    );
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg = data.error || `Server responded with HTTP ${response.status}`;
    throw new Error(errorMsg);
  }

  if (!data.token || !data.url) {
    throw new Error('Invalid token response received from server.');
  }

  return {
    token: data.token,
    url: data.url,
  };
}

/**
 * Perform a health check query against the backend.
 *
 * @returns {Promise<{ healthy: boolean, data?: any, error?: string }>}
 */
export async function checkBackendHealth() {
  const baseUrl = getApiBaseUrl();
  try {
    const res = await fetch(`${baseUrl}/health`, { method: 'GET' });
    if (!res.ok) {
      return { healthy: false, error: `Health check failed with HTTP ${res.status}` };
    }
    const data = await res.json();
    return { healthy: true, data };
  } catch (err) {
    return { healthy: false, error: err.message };
  }
}
