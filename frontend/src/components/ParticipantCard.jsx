import React from 'react';
import { Bot, Sparkles, User, Mic, MicOff, Volume2, Radio, Brain } from 'lucide-react';

/**
 * Individual participant card displaying identity, role, active speaking state,
 * microphone state, and honest conversational status.
 *
 * Supports multiple humans and distinct AI bot identities (ai-dost, ai-sathi).
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
    bg: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    avatarBg: 'from-blue-600 to-indigo-800',
    borderActive: 'border-blue-500 ring-2 ring-blue-500/40 shadow-lg shadow-blue-500/20',
    icon: User,
  };

  if (isDost) {
    roleBadge = {
      label: 'AI Host & Listener',
      bg: 'bg-purple-500/15 text-purple-300 border-purple-500/40',
      avatarBg: 'from-purple-600 to-indigo-600',
      borderActive: 'border-purple-500 ring-4 ring-purple-500/50 shadow-xl shadow-purple-500/25',
      icon: Bot,
    };
  } else if (isSathi) {
    roleBadge = {
      label: 'AI Specialist',
      bg: 'bg-teal-500/15 text-teal-300 border-teal-500/40',
      avatarBg: 'from-teal-600 to-cyan-700',
      borderActive: 'border-teal-500 ring-4 ring-teal-500/50 shadow-xl shadow-teal-500/25',
      icon: Sparkles,
    };
  }

  const AvatarIcon = roleBadge.icon;
  const isMuted = participant?.isMicrophoneEnabled === false;

  // Render honest status indicator
  let statusContent;
  if (isSpeaking) {
    statusContent = (
      <span className="text-purple-400 font-medium flex items-center gap-1">
        <Volume2 className="w-3.5 h-3.5 animate-pulse" />
        <span>Speaking...</span>
      </span>
    );
  } else if (isBot) {
    if (botStatus === 'Thinking') {
      statusContent = (
        <span className="text-amber-400 font-medium flex items-center gap-1">
          <Brain className="w-3.5 h-3.5 animate-pulse text-amber-400" />
          <span>Thinking...</span>
        </span>
      );
    } else if (botStatus === 'Listening' || anyHumanSpeaking) {
      statusContent = (
        <span className="text-teal-400 font-medium flex items-center gap-1">
          <Radio className="w-3.5 h-3.5 animate-pulse text-teal-400" />
          <span>Listening...</span>
        </span>
      );
    } else {
      statusContent = <span className="text-slate-400">Ready &amp; Listening</span>;
    }
  } else {
    statusContent = <span className="text-slate-400">Connected</span>;
  }

  return (
    <div
      className={`relative flex flex-col items-center justify-center p-6 rounded-2xl bg-glass-card transition-all duration-300 border ${
        isSpeaking ? roleBadge.borderActive : 'border-slate-800/80 hover:border-slate-700'
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
              ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
              : 'bg-slate-800/60 text-slate-400 border border-slate-700/50'
          }`}
          title={isMuted ? 'Microphone Muted' : 'Microphone Active'}
        >
          {isMuted ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5 text-emerald-400" />}
        </div>
      </div>

      {/* Avatar Container with subtle scale pulse when speaking */}
      <div className="relative my-4">
        <div
          className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${roleBadge.avatarBg} flex items-center justify-center shadow-inner transition-transform duration-300 ${
            isSpeaking ? 'scale-105' : ''
          }`}
        >
          <AvatarIcon className="w-10 h-10 text-white drop-shadow-md" />
        </div>

        {/* Realtime speaking wave visualizer overlay */}
        {isSpeaking && (
          <div className="absolute -bottom-2 inset-x-0 flex items-center justify-center gap-1 bg-slate-950/90 px-2 py-0.5 rounded-full border border-slate-700/80 shadow-md">
            <span className="w-1 bg-purple-400 rounded-full animate-wave-1" />
            <span className="w-1 bg-purple-300 rounded-full animate-wave-2" />
            <span className="w-1 bg-teal-300 rounded-full animate-wave-3" />
            <span className="w-1 bg-purple-400 rounded-full animate-wave-4" />
          </div>
        )}
      </div>

      {/* Participant Name and Real-Time State */}
      <div className="text-center w-full truncate">
        <h3 className="text-base font-semibold text-slate-100 truncate">
          {displayName}
        </h3>
        <p className="text-xs text-slate-400 mt-1 flex items-center justify-center gap-1.5">
          {statusContent}
        </p>
      </div>
    </div>
  );
}
