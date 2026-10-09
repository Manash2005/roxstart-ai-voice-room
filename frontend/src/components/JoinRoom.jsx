import React, { useState } from 'react';
import { Radio, Mic, Sparkles, Bot, ShieldCheck, AlertCircle, ArrowRight, Loader2 } from 'lucide-react';

/**
 * JoinRoom Landing & Lobby Component.
 *
 * Validates user inputs, displays privacy and microphone details, and triggers token acquisition.
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
    <div className="min-h-screen bg-ambient-radial flex flex-col justify-between py-8 px-4 sm:px-6 lg:px-8">
      {/* Top bar with badge */}
      <div className="max-w-7xl mx-auto w-full flex justify-between items-center mb-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-600/30">
            <Radio className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="text-lg font-bold text-slate-100 font-display tracking-tight">
              Roxstar AI Voice Room
            </span>
            <span className="block text-[11px] text-purple-400 font-medium">
              ₹0-Cost Multi-Bot Realtime Assistant
            </span>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>LiveKit Cloud + Open-Source Stack</span>
        </div>
      </div>

      {/* Hero & Join Card */}
      <div className="max-w-xl mx-auto w-full">
        {/* Card Wrapper */}
        <div className="p-8 sm:p-10 rounded-3xl bg-glass border border-slate-800/80 shadow-2xl relative overflow-hidden">
          {/* Subtle top decorative glow */}
          <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-64 h-32 bg-purple-600/20 blur-3xl pointer-events-none rounded-full" />

          {/* Heading */}
          <div className="text-center mb-6">
            <span className="block text-xs font-bold tracking-widest text-purple-400 uppercase mb-1">
              ROXSTAR
            </span>
            <h1 className="text-3xl font-extrabold text-slate-100 font-display tracking-tight sm:text-4xl">
              AI Voice Room Assistant
            </h1>
            <p className="mt-2.5 text-sm text-slate-300 max-w-lg mx-auto leading-relaxed">
              Two AI companions that understand Hindi, Hinglish and English in a shared LiveKit room.
            </p>
          </div>

          {/* AI Personas Showcase */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 mb-6">
            {/* AI Dost */}
            <div className="p-4 rounded-2xl bg-purple-950/30 border border-purple-500/30 text-left flex flex-col gap-2 shadow-sm">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-purple-600/20 border border-purple-500/40 flex items-center justify-center text-purple-400 shrink-0">
                  <Bot className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-slate-100">AI Dost</h3>
                  <p className="text-[11px] text-purple-300 font-medium">Friendly conversational assistant</p>
                </div>
              </div>
              <p className="text-[11px] text-slate-400 leading-snug">
                Friendly, warm, casual, and approachable companion for general questions and discussion.
              </p>
            </div>

            {/* AI Sathi */}
            <div className="p-4 rounded-2xl bg-teal-950/30 border border-teal-500/30 text-left flex flex-col gap-2 shadow-sm">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-teal-600/20 border border-teal-500/40 flex items-center justify-center text-teal-400 shrink-0">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-slate-100">AI Sathi</h3>
                  <p className="text-[11px] text-teal-300 font-medium">Technical analytical assistant</p>
                </div>
              </div>
              <p className="text-[11px] text-slate-400 leading-snug">
                Calm, analytical, technical, and structured specialist for code comparisons and architecture.
              </p>
            </div>
          </div>

          {/* Error Banner */}
          {displayError && (
            <div
              className="mb-6 p-4 rounded-2xl bg-rose-950/60 border border-rose-500/40 text-rose-200 text-xs sm:text-sm flex items-start gap-3 shadow-lg"
              role="alert"
            >
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex-1">
                <strong className="font-semibold block text-rose-100">Unable to Join</strong>
                <span>{displayError}</span>
              </div>
            </div>
          )}

          {/* Join Form */}
          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            {/* Display Name Input */}
            <div>
              <label htmlFor="user-name" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
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
                className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-700/80 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition text-sm disabled:opacity-50"
              />
            </div>

            {/* Room Name Input */}
            <div>
              <label htmlFor="room-name" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
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
                className="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-700/80 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition text-sm disabled:opacity-50"
              />
              <span className="block text-[11px] text-slate-500 mt-1">
                Default: <code className="text-purple-400">roxstar-demo</code> (Auto-matches your running agent)
              </span>
            </div>

            {/* CTA Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              aria-label="Enter Voice Room"
              className="w-full mt-2 py-3.5 px-6 rounded-xl font-semibold text-sm bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-lg shadow-purple-600/30 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Connecting to LiveKit...</span>
                </>
              ) : (
                <>
                  <span>Enter Voice Room</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Permission & Privacy Explainer */}
          <div className="mt-8 pt-6 border-t border-slate-800/80 grid grid-cols-1 sm:grid-cols-2 gap-4 text-[12px] text-slate-400">
            <div className="flex items-start gap-2.5">
              <Mic className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-300 block">Microphone Access</strong>
                <span>Required for LiveKit realtime audio conversation.</span>
              </div>
            </div>
            <div className="flex items-start gap-2.5">
              <ShieldCheck className="w-4 h-4 text-teal-400 shrink-0 mt-0.5" />
              <div>
                <strong className="text-slate-300 block">Zero Audio Storage</strong>
                <span>Microphone streams are ephemeral; no audio files are saved.</span>
              </div>
            </div>
          </div>
        </div>

        {/* Feature Badges below card */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-xs text-slate-400">
          <div className="flex items-center gap-1.5">
            <Bot className="w-4 h-4 text-purple-400" />
            <span>AI Dost (Friendly Host)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-teal-400" />
            <span>AI Sathi (Technical Specialist)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Radio className="w-4 h-4 text-blue-400" />
            <span>Realtime WebRTC</span>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="text-center text-xs text-slate-600 mt-8">
        Roxstar AI Voice Room &bull; Candidate Assignment Demonstration &bull; Checkpoint 8C
      </footer>
    </div>
  );
}
