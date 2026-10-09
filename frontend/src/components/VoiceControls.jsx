import React, { useState } from 'react';
import { Mic, MicOff, PhoneOff, AlertTriangle, MessageSquare } from 'lucide-react';
import { useLocalParticipant } from '@livekit/components-react';

/**
 * Bottom control bar providing microphone mute/unmute, chat toggle, and room disconnect buttons.
 *
 * @param {Object} props
 * @param {Function} props.onLeave - Callback triggered when user clicks Leave Room
 * @param {Function} [props.onToggleChat] - Callback to toggle chat panel visibility
 * @param {boolean} [props.isChatOpen] - Current chat panel open state
 */
export default function VoiceControls({ onLeave, onToggleChat, isChatOpen = false }) {
  const [deviceError, setDeviceError] = useState(null);
  const localParticipantContext = useLocalParticipant();
  const localParticipant = localParticipantContext?.localParticipant;

  const isMicrophoneEnabled = localParticipant ? localParticipant.isMicrophoneEnabled : true;

  const toggleMicrophone = async () => {
    if (!localParticipant) return;
    try {
      await localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled);
      setDeviceError(null);
    } catch (err) {
      setDeviceError(
        err.name === 'NotAllowedError'
          ? 'Microphone permission was denied. Please allow microphone access in your browser settings.'
          : `Microphone error: ${err.message}`
      );
    }
  };

  return (
    <div className="flex flex-col items-center gap-3">
      {/* Device error banner if permission denied */}
      {deviceError && (
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-rose-950/70 border border-rose-500/40 text-rose-200 text-xs shadow-lg animate-fade-in">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{deviceError}</span>
        </div>
      )}

      {/* Main bottom floating controls */}
      <div className="flex items-center gap-3 sm:gap-4 px-5 sm:px-6 py-3 rounded-2xl bg-glass border border-slate-800/80 shadow-2xl backdrop-blur-xl">
        {/* Mic Toggle Button */}
        <button
          onClick={toggleMicrophone}
          type="button"
          aria-label={isMicrophoneEnabled ? 'Mute microphone' : 'Unmute microphone'}
          className={`flex items-center gap-2.5 px-4 sm:px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 shadow-md cursor-pointer ${
            isMicrophoneEnabled
              ? 'bg-slate-800/80 hover:bg-slate-700/80 text-slate-100 border border-slate-700/60'
              : 'bg-rose-600 hover:bg-rose-700 text-white shadow-rose-600/30'
          }`}
        >
          {isMicrophoneEnabled ? (
            <>
              <Mic className="w-4 h-4 text-emerald-400" />
              <span>Mute</span>
            </>
          ) : (
            <>
              <MicOff className="w-4 h-4 text-white" />
              <span>Unmute</span>
            </>
          )}
        </button>

        {/* Chat Toggle Button */}
        {onToggleChat && (
          <button
            onClick={onToggleChat}
            type="button"
            aria-label={isChatOpen ? 'Hide text chat' : 'Open text chat'}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 border shadow-md cursor-pointer ${
              isChatOpen
                ? 'bg-purple-600/30 text-purple-300 border-purple-500/50 shadow-purple-600/20'
                : 'bg-slate-800/80 hover:bg-slate-700/80 text-slate-300 border-slate-700/60'
            }`}
          >
            <MessageSquare className="w-4 h-4 text-purple-400" />
            <span className="hidden sm:inline">Chat</span>
          </button>
        )}

        {/* Leave Room Button */}
        <button
          onClick={onLeave}
          type="button"
          aria-label="Leave voice room"
          className="flex items-center gap-2 px-4 sm:px-5 py-2.5 rounded-xl font-medium text-sm bg-rose-500/15 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/30 hover:border-rose-600 transition-all duration-200 shadow-md cursor-pointer"
        >
          <PhoneOff className="w-4 h-4" />
          <span>Leave</span>
        </button>
      </div>
    </div>
  );
}
