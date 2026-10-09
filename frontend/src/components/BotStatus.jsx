import React from 'react';
import { Bot, Sparkles, Volume2, Mic, CheckCircle2, Clock, Brain } from 'lucide-react';
import { useBotStates } from '../hooks/useBotState';

/**
 * Visual status pills showing presence and real-time state of AI Dost and AI Sathi.
 *
 * States are derived directly from LiveKit WebRTC participant and audio activity:
 * - Speaking: Bot's audio track is actively emitting speech.
 * - Listening: A human participant in the room is actively speaking.
 * - Thinking: Intermediate state while STT/LLM pipeline processes human turn.
 * - Ready: Bot is connected to the room, idle, and awaiting input.
 * - Connecting...: Bot has not yet joined the LiveKit room session.
 *
 * @param {Object} props
 * @param {Array} [props.participants] - Optional fallback participants
 */
export default function BotStatus({ participants = [] }) {
  const { dostStatus, sathiStatus } = useBotStates(participants);

  const getBadgeConfig = (status) => {
    switch (status) {
      case 'Speaking':
        return {
          icon: Volume2,
          badge: 'text-emerald-300 border-emerald-500/40 bg-emerald-950/40 shadow-sm shadow-emerald-500/20 animate-pulse',
        };
      case 'Listening':
        return {
          icon: Mic,
          badge: 'text-purple-300 border-purple-500/40 bg-purple-950/40',
        };
      case 'Thinking':
        return {
          icon: Brain,
          badge: 'text-amber-300 border-amber-500/40 bg-amber-950/40 shadow-sm shadow-amber-500/20 animate-pulse',
        };
      case 'Ready':
        return {
          icon: CheckCircle2,
          badge: 'text-slate-300 border-slate-700/60 bg-slate-900/60',
        };
      default:
        return {
          icon: Clock,
          badge: 'text-slate-500 border-slate-800 bg-slate-900/50',
        };
    }
  };

  const dostConfig = getBadgeConfig(dostStatus);
  const sathiConfig = getBadgeConfig(sathiStatus);

  const DostIcon = dostConfig.icon;
  const SathiIcon = sathiConfig.icon;

  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* AI Dost pill */}
      <div
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition-all ${dostConfig.badge}`}
        title={`AI Dost: ${dostStatus}`}
      >
        <Bot className="w-3.5 h-3.5 text-purple-400" />
        <span className="font-semibold text-slate-200">AI Dost</span>
        <span className="text-[11px] opacity-80 flex items-center gap-1">
          <DostIcon className="w-3 h-3" />
          <span>{dostStatus}</span>
        </span>
      </div>

      {/* AI Sathi pill */}
      <div
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition-all ${sathiConfig.badge}`}
        title={`AI Sathi: ${sathiStatus}`}
      >
        <Sparkles className="w-3.5 h-3.5 text-teal-400" />
        <span className="font-semibold text-slate-200">AI Sathi</span>
        <span className="text-[11px] opacity-80 flex items-center gap-1">
          <SathiIcon className="w-3 h-3" />
          <span>{sathiStatus}</span>
        </span>
      </div>
    </div>
  );
}
