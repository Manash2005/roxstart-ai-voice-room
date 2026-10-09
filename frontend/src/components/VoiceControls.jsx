import React, { useState } from 'react';
import { Mic, MicOff, PhoneOff, AlertTriangle, MessageSquare } from 'lucide-react';
import { useLocalParticipant } from '@livekit/components-react';

/**
 * Bottom control bar providing microphone mute/unmute, chat toggle, and room disconnect buttons.
 *
 * Implemented with minimalist executive styling, frosted glassmorphism,
 * and high-contrast ergonomic controls:
 * - Active / Muted mic: #4F7D32 vs #D9361E
 * - Chat toggle: #FFD16A & #4F7D32
 * - Leave room: #D9361E
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
        <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#D9361E]/15 border border-[#D9361E]/40 text-[#ffb0a3] text-xs shadow-lg animate-fade-in">
          <AlertTriangle className="w-4 h-4 text-[#D9361E] shrink-0" />
          <span>{deviceError}</span>
        </div>
      )}

      {/* Main bottom floating controls */}
      <div className="flex items-center gap-3 sm:gap-4 px-5 sm:px-6 py-3 rounded-2xl bg-glass border border-white/[0.08] shadow-2xl backdrop-blur-2xl">
        {/* Mic Toggle Button */}
        <button
          onClick={toggleMicrophone}
          type="button"
          aria-label={isMicrophoneEnabled ? 'Mute microphone' : 'Unmute microphone'}
          className={`flex items-center gap-2.5 px-4 sm:px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 shadow-md cursor-pointer ${
            isMicrophoneEnabled
              ? 'bg-white/[0.06] hover:bg-white/[0.12] text-stone-100 border border-white/10'
              : 'bg-[#D9361E] hover:bg-[#bd2a13] text-white shadow-[#D9361E]/30'
          }`}
        >
          {isMicrophoneEnabled ? (
            <>
              <Mic className="w-4 h-4 text-[#a3d98b]" />
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
                ? 'bg-[#4F7D32]/25 text-[#FFD16A] border-[#4F7D32]/50 shadow-[#4F7D32]/20'
                : 'bg-white/[0.06] hover:bg-white/[0.12] text-stone-300 border-white/10'
            }`}
          >
            <MessageSquare className="w-4 h-4 text-[#FFD16A]" />
            <span className="hidden sm:inline">Chat</span>
          </button>
        )}

        {/* Leave Room Button */}
        <button
          onClick={onLeave}
          type="button"
          aria-label="Leave voice room"
          className="flex items-center gap-2 px-4 sm:px-5 py-2.5 rounded-xl font-medium text-sm bg-[#D9361E]/15 hover:bg-[#D9361E] text-[#ff8e7d] hover:text-white border border-[#D9361E]/30 hover:border-[#D9361E] transition-all duration-200 shadow-md cursor-pointer"
        >
          <PhoneOff className="w-4 h-4" />
          <span>Leave</span>
        </button>
      </div>
    </div>
  );
}
