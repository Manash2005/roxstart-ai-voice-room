import React, { useState } from 'react';
import JoinRoom from './components/JoinRoom';
import RoomShell from './components/RoomShell';
import { requestRoomToken } from './api';

/**
 * Main application root for Roxstar AI Voice Room.
 * Controls routing between the Lobby (JoinRoom) and the live voice room (RoomShell).
 */
export default function App() {
  const [session, setSession] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleJoin = async ({ room, identity, name }) => {
    setIsLoading(true);
    setError(null);

    try {
      // Securely acquire token from our Python backend without exposing LIVEKIT_API_SECRET
      const { token, url } = await requestRoomToken({ room, identity, name });
      setSession({
        token,
        url,
        roomName: room,
        userName: name,
        identity,
      });
    } catch (err) {
      setError(err.message || 'Failed to acquire room credentials from server.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLeave = () => {
    setSession(null);
    setError(null);
  };

  if (session) {
    return (
      <RoomShell
        token={session.token}
        serverUrl={session.url}
        roomName={session.roomName}
        userName={session.userName}
        onLeave={handleLeave}
      />
    );
  }

  return <JoinRoom onJoin={handleJoin} isLoading={isLoading} error={error} />;
}
