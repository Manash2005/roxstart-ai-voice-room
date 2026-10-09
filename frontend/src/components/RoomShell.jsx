import React, { useState } from 'react';
import {
  LiveKitRoom,
  RoomAudioRenderer,
  StartAudio,
  useConnectionState,
  useParticipants,
} from '@livekit/components-react';
import { ConnectionState } from 'livekit-client';
import { Radio, Users, Sparkles, MessageSquare } from 'lucide-react';

import ConnectionStatus from './ConnectionStatus';
import BotStatus from './BotStatus';
import ParticipantGrid from './ParticipantGrid';
import VoiceControls from './VoiceControls';
import ChatPanel from './ChatPanel';

/**
 * Inner room view rendering active participants, header status, chat panel, and controls.
 */
function RoomInner({ roomName, userName, onLeave }) {
  const connectionState = useConnectionState();
  const participants = useParticipants();
  const [isChatOpen, setIsChatOpen] = useState(true);

  // Map LiveKit ConnectionState to our visual status states
  let visualState = 'connecting';
  if (connectionState === ConnectionState.Connected) {
    visualState = 'connected';
  } else if (connectionState === ConnectionState.Reconnecting) {
    visualState = 'reconnecting';
  } else if (connectionState === ConnectionState.Disconnected) {
    visualState = 'disconnected';
  }

  return (
    <div className="flex flex-col min-h-screen bg-ambient-radial">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-30 px-4 sm:px-8 py-3.5 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          {/* Room Title & Brand */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-600/30">
              <Radio className="w-5 h-5 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-slate-100 font-display">
                  {roomName}
                </h1>
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Connected as <span className="text-purple-300 font-medium">{userName}</span>
              </p>
            </div>
          </div>

          {/* Right status badges */}
          <div className="flex items-center gap-3">
            {/* Participant count */}
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-900 border border-slate-800 text-slate-300">
              <Users className="w-3.5 h-3.5 text-slate-400" />
              <span>{participants.length} Active</span>
            </div>

            {/* AI Bots presence */}
            <BotStatus participants={participants} />

            {/* LiveKit WebRTC state */}
            <ConnectionStatus state={visualState} />

            {/* Chat Panel Toggle Button */}
            <button
              onClick={() => setIsChatOpen(!isChatOpen)}
              aria-label={isChatOpen ? 'Hide text chat' : 'Open text chat'}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition cursor-pointer ${
                isChatOpen
                  ? 'bg-purple-600/30 text-purple-300 border-purple-500/50 shadow-sm shadow-purple-600/20'
                  : 'bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5 text-purple-400" />
              <span>Chat</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Conversation Stage */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-8 py-6 flex flex-col justify-between">
        {/* Helper Tip Card */}
        <div className="mb-6 p-4 rounded-2xl bg-glass border border-purple-900/30 shadow-lg flex items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 shrink-0">
              <Sparkles className="w-5 h-5" />
            </div>
            <p className="text-xs sm:text-sm text-slate-300">
              <strong className="text-slate-100 font-medium">Bilingual Room Active:</strong> Speak naturally or type in Hindi, Hinglish, or English.
              Ask general questions to <strong className="text-purple-300">AI Dost</strong>, or technical comparisons to <strong className="text-teal-300">AI Sathi</strong>.
            </p>
          </div>
          <div className="hidden md:flex items-center gap-1 text-[11px] text-slate-400 bg-slate-900/60 px-3 py-1 rounded-lg border border-slate-800">
            <MessageVoiceHint />
          </div>
        </div>

        {/* Split View: Participant Stage (Left) & Chat Panel (Right) */}
        <div className="flex-1 flex flex-col lg:flex-row gap-6 items-stretch mb-6">
          {/* Participant Grid & Stage */}
          <div className="flex-1 flex flex-col justify-start min-h-[380px]">
            {/* Column Header */}
            <div className="flex items-center justify-between mb-3 px-1">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-purple-400" />
                <h2 className="text-sm font-bold text-slate-200 font-display tracking-tight">
                  Participants
                </h2>
              </div>
              <span className="text-[11px] font-medium text-slate-400 bg-slate-900/80 px-2.5 py-0.5 rounded-full border border-slate-800">
                {participants.length} Active
              </span>
            </div>

            <div className="flex-1 flex flex-col justify-center">
              <ParticipantGrid />
            </div>
          </div>

          {/* Chat / Transcript Side Panel */}
          {isChatOpen && (
            <div className="w-full lg:w-[420px] h-[520px] lg:h-[calc(100vh-230px)] shrink-0 sticky top-24">
              <ChatPanel
                onClose={() => setIsChatOpen(false)}
                localIdentity={userName}
              />
            </div>
          )}
        </div>
      </main>

      {/* Full-width Centered Bottom Controls */}
      <footer className="sticky bottom-0 z-30 py-3.5 px-4 bg-slate-950/85 backdrop-blur-xl border-t border-slate-800/80 flex justify-center shadow-2xl">
        <VoiceControls
          onLeave={onLeave}
          onToggleChat={() => setIsChatOpen(!isChatOpen)}
          isChatOpen={isChatOpen}
        />
      </footer>

      {/* Autoplay fallback prompt if browser restricts audio playback */}
      <StartAudio
        label="Click to Enable Bot Audio Playback"
        className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs shadow-2xl transition cursor-pointer border border-purple-400/40"
      />

      {/* Automatic Audio Playback from AI Bots */}
      <RoomAudioRenderer />
    </div>
  );
}

function MessageVoiceHint() {
  return (
    <>
      <MessageSquare className="w-3 h-3 text-purple-400" />
      <span>₹0-Cost Dual Bot Architecture</span>
    </>
  );
}

/**
 * Top-level RoomShell wrapping the LiveKit room session.
 *
 * @param {Object} props
 * @param {string} props.token - Cryptographically signed JWT from backend
 * @param {string} props.serverUrl - LiveKit WebSocket URL
 * @param {string} props.roomName - Room title
 * @param {string} props.userName - Human user name
 * @param {Function} props.onLeave - Exit room callback
 */
export default function RoomShell({ token, serverUrl, roomName, userName, onLeave }) {
  const [connectError, setConnectError] = useState(null);

  if (connectError) {
    return (
      <div className="min-h-screen bg-ambient-radial flex items-center justify-center p-4">
        <div className="max-w-md w-full p-8 rounded-3xl bg-glass-card border border-rose-500/30 text-center shadow-2xl">
          <div className="w-16 h-16 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center mx-auto mb-4 text-rose-400">
            <Radio className="w-8 h-8" />
          </div>
          <h2 className="text-xl font-bold text-slate-100 mb-2 font-display">
            Connection Failed
          </h2>
          <p className="text-sm text-slate-400 mb-6">{connectError}</p>
          <button
            onClick={onLeave}
            className="w-full py-3 rounded-xl font-medium bg-purple-600 hover:bg-purple-500 text-white transition-all shadow-lg shadow-purple-600/30"
          >
            Return to Lobby
          </button>
        </div>
      </div>
    );
  }

  return (
    <LiveKitRoom
      token={token}
      serverUrl={serverUrl}
      connect={true}
      audio={true}
      video={false}
      onDisconnected={onLeave}
      onError={(err) => setConnectError(err.message || 'Failed to connect to LiveKit')}
      data-lk-theme="default"
    >
      <RoomInner roomName={roomName} userName={userName} onLeave={onLeave} />
    </LiveKitRoom>
  );
}
