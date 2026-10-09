import React from 'react';
import { Bot, Sparkles, User, Mic, MicOff, Volume2, Radio, Brain } from 'lucide-react';

/**
 * Individual participant card displaying identity, role, active speaking state,
 * microphone state, and honest conversational status.
 *
 * Designed with minimalist glassmorphism and the bespoke 4-color palette:
 * - #4F7D32 (Forest Green)
 * - #FFD16A (Soft Cream)
 * - #F5B52E (Warm Amber Gold)
 * - #D9361E (Crimson Danger/Mute)
 *
 * @param {Object} props
 * @param {Object} props.participant - LiveKit participant object or mock
 * @param {boolean} [props.isLocal] - True if this represents the local user
 * @param {boolean} [props.isSpeaking] - True if this participant is actively producing audio
 * @param {boolean} [props.anyHumanSpeaking] - True if any human in room is actively speaking
 * @param {string} [props.botStatus] - Honest bot status ('Speaking' | 'Listening' | 'Thinking' | 'Ready')
 */
export default function ParticipantCard({
  participant,
  isLocal = false,
  isSpeaking = false,
  anyHumanSpeaking = false,
  botStatus = 'Ready',
}) {
  const identity = participant?.identity || '';
  const displayName = participant?.name || identity || (isLocal ? 'You' : 'Participant');

  // Identify bots strictly by identity as required by specification
  const isDost = identity === 'ai-dost';
  const isSathi = identity === 'ai-sathi';
  const isBot = isDost || isSathi;

  // Determine role styling and visual identity attributes
  let roleBadge = {
    label: isLocal ? 'You' : 'Participant',
    bg: 'bg-white/[0.06] text-stone-300 border-white/10',
    avatarBg: 'from-stone-700 to-stone-900',
    borderActive: 'border-[#4F7D32] ring-2 ring-[#4F7D32]/40 shadow-lg shadow-[#4F7D32]/20',
    icon: User,
  };

  if (isDost) {
    roleBadge = {
      label: 'AI Host & Listener',
      bg: 'bg-[#F5B52E]/15 text-[#FFD16A] border-[#F5B52E]/40',
      avatarBg: 'from-[#F5B52E] to-[#ad6d0c]',
      borderActive: 'border-[#F5B52E] ring-2 ring-[#F5B52E]/50 shadow-xl shadow-[#F5B52E]/25',
      icon: Bot,
    };
  } else if (isSathi) {
    roleBadge = {
      label: 'AI Specialist',
      bg: 'bg-[#4F7D32]/25 text-[#a3d98b] border-[#4F7D32]/50',
      avatarBg: 'from-[#4F7D32] to-[#284419]',
      borderActive: 'border-[#4F7D32] ring-2 ring-[#4F7D32]/50 shadow-xl shadow-[#4F7D32]/25',
      icon: Sparkles,
    };
  }

  const AvatarIcon = roleBadge.icon;
  const isMuted = participant?.isMicrophoneEnabled === false;

  // Render honest status indicator
  let statusContent;
  if (isSpeaking) {
    statusContent = (
      <span className="text-[#FFD16A] font-medium flex items-center gap-1">
        <Volume2 className="w-3.5 h-3.5 animate-pulse text-[#FFD16A]" />
        <span>Speaking...</span>
      </span>
    );
  } else if (isBot) {
    if (botStatus === 'Thinking') {
      statusContent = (
        <span className="text-[#F5B52E] font-medium flex items-center gap-1">
          <Brain className="w-3.5 h-3.5 animate-pulse text-[#F5B52E]" />
          <span>Thinking...</span>
        </span>
      );
    } else if (botStatus === 'Listening' || anyHumanSpeaking) {
      statusContent = (
        <span className="text-[#a3d98b] font-medium flex items-center gap-1">
          <Radio className="w-3.5 h-3.5 animate-pulse text-[#4F7D32]" />
          <span>Listening...</span>
        </span>
      );
    } else {
      statusContent = <span className="text-stone-400">Ready &amp; Listening</span>;
    }
  } else {
    statusContent = <span className="text-stone-400">Connected</span>;
  }

  return (
    <div
      className={`relative flex flex-col items-center justify-center p-6 rounded-2xl bg-glass-card transition-all duration-300 border ${
        isSpeaking ? roleBadge.borderActive : 'border-white/[0.08] hover:border-white/15'
      }`}
      data-testid={`participant-card-${identity || 'local'}`}
    >
      {/* Role badge in top left corner */}
      <div className="absolute top-3.5 left-3.5">
        <span
          className={`px-2.5 py-0.5 rounded-full text-[11px] font-medium border backdrop-blur-sm ${roleBadge.bg}`}
        >
          {roleBadge.label}
        </span>
      </div>

      {/* Mic status in top right corner */}
      <div className="absolute top-3.5 right-3.5">
        <div
          className={`p-1.5 rounded-full text-xs transition-colors ${
            isMuted
              ? 'bg-[#D9361E]/20 text-[#ff8e7d] border border-[#D9361E]/40'
              : 'bg-[#4F7D32]/20 text-[#a3d98b] border border-[#4F7D32]/40'
          }`}
          title={isMuted ? 'Microphone Muted' : 'Microphone Active'}
        >
          {isMuted ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5 text-[#a3d98b]" />}
        </div>
      </div>

      {/* Avatar Container with subtle scale pulse when speaking */}
      <div className="relative my-4">
        <div
          className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${roleBadge.avatarBg} border border-white/10 flex items-center justify-center shadow-lg transition-transform duration-300 ${
            isSpeaking ? 'scale-105' : ''
          }`}
        >
          <AvatarIcon className="w-10 h-10 text-white drop-shadow-md" />
        </div>

        {/* Realtime speaking wave visualizer overlay */}
        {isSpeaking && (
          <div className="absolute -bottom-2 inset-x-0 flex items-center justify-center gap-1 bg-[#090d09]/95 px-2 py-0.5 rounded-full border border-white/10 shadow-md">
            <span className="w-1 bg-[#4F7D32] rounded-full animate-wave-1" />
            <span className="w-1 bg-[#FFD16A] rounded-full animate-wave-2" />
            <span className="w-1 bg-[#F5B52E] rounded-full animate-wave-3" />
            <span className="w-1 bg-[#4F7D32] rounded-full animate-wave-4" />
          </div>
        )}
      </div>

      {/* Participant Name and Real-Time State */}
      <div className="text-center w-full truncate">
        <h3 className="text-base font-semibold text-stone-100 truncate">
          {displayName}
        </h3>
        <p className="text-xs text-stone-400 mt-1 flex items-center justify-center gap-1.5">
          {statusContent}
        </p>
      </div>
    </div>
  );
}
