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
          badge: 'text-[#FFD16A] border-[#FFD16A]/40 bg-[#FFD16A]/10 shadow-sm animate-pulse',
        };
      case 'Listening':
        return {
          icon: Mic,
          badge: 'text-[#a3d98b] border-[#4F7D32]/40 bg-[#4F7D32]/15',
        };
      case 'Thinking':
        return {
          icon: Brain,
          badge: 'text-[#F5B52E] border-[#F5B52E]/40 bg-[#F5B52E]/15 shadow-sm animate-pulse',
        };
      case 'Ready':
        return {
          icon: CheckCircle2,
          badge: 'text-stone-300 border-white/10 bg-white/[0.04]',
        };
      default:
        return {
          icon: Clock,
          badge: 'text-stone-500 border-white/[0.06] bg-white/[0.02]',
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
        <Bot className="w-3.5 h-3.5 text-[#FFD16A]" />
        <span className="font-semibold text-stone-200">AI Dost</span>
        <span className="text-[11px] opacity-90 flex items-center gap-1">
          <DostIcon className="w-3 h-3" />
          <span>{dostStatus}</span>
        </span>
      </div>

      {/* AI Sathi pill */}
      <div
        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition-all ${sathiConfig.badge}`}
        title={`AI Sathi: ${sathiStatus}`}
      >
        <Sparkles className="w-3.5 h-3.5 text-[#a3d98b]" />
        <span className="font-semibold text-stone-200">AI Sathi</span>
        <span className="text-[11px] opacity-90 flex items-center gap-1">
          <SathiIcon className="w-3 h-3" />
          <span>{sathiStatus}</span>
        </span>
      </div>
    </div>
  );
}
