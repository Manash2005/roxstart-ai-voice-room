import React from 'react';
import ParticipantCard from './ParticipantCard';
import { useBotStates } from '../hooks/useBotState';

/**
 * Grid layout rendering all active voice room participants:
 * - Local Human User
 * - AI Dost (ai-dost)
 * - AI Sathi (ai-sathi)
 * - Additional Remote Human Peers (multi-human support)
 *
 * @param {Object} props
 * @param {Array} [props.fallbackParticipants] - Optional static participants for testing or disconnected states
 */
export default function ParticipantGrid({ fallbackParticipants }) {
  const {
    participants,
    speakingIdentities,
    anyHumanSpeaking,
    dostStatus,
    sathiStatus,
  } = useBotStates(fallbackParticipants);

  // Sort participants predictably: Local user first, then AI Dost, AI Sathi, then other humans
  const sortedParticipants = [...participants].sort((a, b) => {
    if (a.isLocal) return -1;
    if (b.isLocal) return 1;
    if (a.identity === 'ai-dost') return -1;
    if (b.identity === 'ai-dost') return 1;
    if (a.identity === 'ai-sathi') return -1;
    if (b.identity === 'ai-sathi') return 1;
    return (a.name || a.identity || '').localeCompare(b.name || b.identity || '');
  });

  return (
    <div className="w-full">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
        {sortedParticipants.map((p, index) => {
          const isParticipantSpeaking = Boolean(p.isSpeaking) || speakingIdentities.has(p.identity);
          const botStatus =
            p.identity === 'ai-dost'
              ? dostStatus
              : p.identity === 'ai-sathi'
              ? sathiStatus
              : 'Ready';

          return (
            <ParticipantCard
              key={p.identity || p.sid || `participant-${index}`}
              participant={p}
              isLocal={p.isLocal}
              isSpeaking={isParticipantSpeaking}
              anyHumanSpeaking={anyHumanSpeaking}
              botStatus={botStatus}
            />
          );
        })}
      </div>
    </div>
  );
}
