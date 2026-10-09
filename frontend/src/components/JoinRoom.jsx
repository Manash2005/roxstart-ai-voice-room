import React, { useState } from 'react';
import { Radio, Mic, Sparkles, Bot, ShieldCheck, AlertCircle, ArrowRight, Loader2 } from 'lucide-react';

/**
 * JoinRoom Landing & Lobby Component.
 *
 * Professional, minimalist entrance interface with refined glassmorphism,
 * bespoke typography, and subtle micro-animations.
 *
 * @param {Object} props
 * @param {Function} props.onJoin - Callback receiving { room, identity, name }
 * @param {boolean} [props.isLoading] - True when fetching token or initializing connection
 * @param {string} [props.error] - Error message to display if connection/token fails
 */
export default function JoinRoom({ onJoin, isLoading = false, error = null }) {
  const [name, setName] = useState('');
  const [room, setRoom] = useState('roxstar-demo');
  const [clientError, setClientError] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    setClientError(null);

    const trimmedName = name.trim();
    if (!trimmedName) {
      setClientError('Please enter your name to join the room.');
      return;
    }

    const trimmedRoom = room.trim();
    if (!trimmedRoom) {
      setClientError('Please enter a room name.');
      return;
    }

    // Generate unique participant identity
    const sanitizedName = trimmedName.toLowerCase().replace(/[^a-z0-9]/g, '-').slice(0, 16);
    const randomSuffix = Math.random().toString(36).substring(2, 8);
    const identity = `user-${sanitizedName || 'guest'}-${randomSuffix}`;

    onJoin({
      name: trimmedName,
      room: trimmedRoom,
      identity,
    });
  };

  const displayError = clientError || error;

  return (
    <div className="min-h-screen bg-ambient-radial flex flex-col justify-between py-8 px-4 sm:px-6 lg:px-8 selection:bg-[#4F7D32] selection:text-[#FFD16A]">
      {/* Top bar with refined brand mark */}
      <header className="max-w-7xl mx-auto w-full flex justify-between items-center mb-8">
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-2xl bg-[#4F7D32] border border-[#FFD16A]/25 flex items-center justify-center shadow-lg shadow-[#4F7D32]/25">
            <Radio className="w-5 h-5 text-[#FFD16A]" />
          </div>
          <div>
            <span className="text-lg font-bold text-stone-100 font-display tracking-tight">
              Roxstar AI Voice Room
            </span>
            <span className="block text-[11px] text-[#FFD16A]/90 font-medium tracking-wide">
              ₹0-Cost Multi-Bot Realtime Assistant
            </span>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#121a12]/80 border border-white/[0.08] text-xs text-stone-300">
          <span className="w-2 h-2 rounded-full bg-[#4F7D32] animate-pulse" />
          <span className="text-[11px] font-medium tracking-wide">LiveKit Cloud + Open-Source Stack</span>
        </div>
      </header>

      {/* Hero & Join Card */}
      <main className="max-w-xl mx-auto w-full">
        {/* Card Wrapper */}
        <div className="p-8 sm:p-10 rounded-3xl bg-glass border border-white/[0.08] shadow-2xl relative overflow-hidden">
          {/* Subtle top ambient glow */}
          <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-72 h-36 bg-[#4F7D32]/15 blur-3xl pointer-events-none rounded-full" />

          {/* Heading */}
          <div className="text-center mb-7">
            <span className="block text-[11px] font-bold tracking-[0.25em] text-[#FFD16A] uppercase mb-1.5">
              ROXSTAR
            </span>
            <h1 className="text-3xl font-extrabold text-stone-100 font-display tracking-tight sm:text-4xl">
              AI Voice Room Assistant
            </h1>
            <p className="mt-2.5 text-sm text-stone-300 max-w-lg mx-auto leading-relaxed font-normal">
              Two AI companions that understand Hindi, Hinglish and English in a shared LiveKit room.
            </p>
          </div>

          {/* AI Personas Showcase */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 mb-7">
            {/* AI Dost */}
            <div className="p-4 rounded-2xl bg-[#1c180e]/60 border border-[#F5B52E]/30 text-left flex flex-col gap-2 shadow-sm transition-all hover:border-[#F5B52E]/50">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[#F5B52E]/15 border border-[#F5B52E]/35 flex items-center justify-center text-[#FFD16A] shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-stone-100">AI Dost</h3>
                  <p className="text-[11px] text-[#FFD16A] font-medium">Friendly conversational assistant</p>
                </div>
              </div>
              <p className="text-[11px] text-stone-400 leading-snug">
                Friendly, warm, casual, and approachable companion for general questions and discussion.
              </p>
            </div>

            {/* AI Sathi */}
            <div className="p-4 rounded-2xl bg-[#0f1a0f]/60 border border-[#4F7D32]/40 text-left flex flex-col gap-2 shadow-sm transition-all hover:border-[#4F7D32]/60">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[#4F7D32]/25 border border-[#4F7D32]/45 flex items-center justify-center text-[#a3d98b] shrink-0">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-stone-100">AI Sathi</h3>
                  <p className="text-[11px] text-[#a3d98b] font-medium">Technical analytical assistant</p>
                </div>
              </div>
              <p className="text-[11px] text-stone-400 leading-snug">
                Calm, analytical, technical, and structured specialist for code comparisons and architecture.
              </p>
            </div>
          </div>

          {/* Error Banner */}
          {displayError && (
            <div
              className="mb-6 p-4 rounded-2xl bg-[#D9361E]/15 border border-[#D9361E]/40 text-[#ffb0a3] text-xs sm:text-sm flex items-start gap-3 shadow-lg"
              role="alert"
            >
              <AlertCircle className="w-5 h-5 text-[#D9361E] shrink-0 mt-0.5" />
              <div className="flex-1">
                <strong className="font-semibold block text-stone-100">Unable to Join</strong>
                <span>{displayError}</span>
              </div>
            </div>
          )}

          {/* Join Form */}
          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            {/* Display Name Input */}
            <div>
              <label htmlFor="user-name" className="block text-[11px] font-semibold text-stone-300 uppercase tracking-wider mb-2">
                Your Display Name
              </label>
              <input
                id="user-name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Manash"
                disabled={isLoading}
                maxLength={64}
                required
                className="w-full px-4 py-3 rounded-xl bg-[#0c120c] border border-white/10 text-stone-100 placeholder-stone-500 focus:outline-none focus:border-[#4F7D32] focus:ring-1 focus:ring-[#4F7D32] transition text-sm disabled:opacity-50"
              />
            </div>

            {/* Room Name Input */}
            <div>
              <label htmlFor="room-name" className="block text-[11px] font-semibold text-stone-300 uppercase tracking-wider mb-2">
                Room Name
              </label>
              <input
                id="room-name"
                type="text"
                value={room}
                onChange={(e) => setRoom(e.target.value)}
                placeholder="roxstar-demo"
                disabled={isLoading}
                maxLength={64}
                required
                className="w-full px-4 py-3 rounded-xl bg-[#0c120c] border border-white/10 text-stone-100 placeholder-stone-500 focus:outline-none focus:border-[#4F7D32] focus:ring-1 focus:ring-[#4F7D32] transition text-sm disabled:opacity-50"
              />
              <span className="block text-[11px] text-stone-500 mt-1.5">
                Default: <code className="text-[#FFD16A] font-mono">roxstar-demo</code> (Auto-matches your running agent)
              </span>
            </div>

            {/* CTA Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              aria-label="Enter Voice Room"
              className="w-full mt-3 py-3.5 px-6 rounded-xl font-semibold text-sm bg-[#4F7D32] hover:bg-[#5a8c39] active:bg-[#436b2b] text-[#FFD16A] border border-[#FFD16A]/20 shadow-lg shadow-[#4F7D32]/25 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-[#FFD16A]" />
                  <span>Connecting to LiveKit...</span>
                </>
              ) : (
                <>
                  <span>Enter Voice Room</span>
                  <ArrowRight className="w-4 h-4 text-[#FFD16A]" />
                </>
              )}
            </button>
          </form>

          {/* Permission & Privacy Explainer */}
          <div className="mt-8 pt-6 border-t border-white/[0.08] grid grid-cols-1 sm:grid-cols-2 gap-4 text-[12px] text-stone-400">
            <div className="flex items-start gap-2.5">
              <Mic className="w-4 h-4 text-[#FFD16A] shrink-0 mt-0.5" />
              <div>
                <strong className="text-stone-300 block font-medium">Microphone Access</strong>
                <span>Required for LiveKit realtime audio conversation.</span>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <ShieldCheck className="w-4 h-4 text-[#4F7D32] shrink-0 mt-0.5" />
              <div>
                <strong className="text-stone-300 block font-medium">Zero Audio Storage</strong>
                <span>Microphone streams are ephemeral; no audio files are saved.</span>
              </div>
            </div>
          </div>
        </div>

        {/* Feature Badges below card */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-stone-400">
          <div className="flex items-center gap-1.5">
            <Bot className="w-4 h-4 text-[#FFD16A]" />
            <span>AI Dost (Friendly Host)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-[#4F7D32]" />
            <span>AI Sathi (Technical Specialist)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Radio className="w-4 h-4 text-[#F5B52E]" />
            <span>Realtime WebRTC</span>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="text-center text-xs text-stone-600 mt-8">
        Roxstar AI Voice Room &bull; Candidate Assignment Demonstration &bull; Checkpoint 8E
      </footer>
    </div>
  );
}
