import { useState, useEffect, useRef } from 'react';
import { useParticipants, useSpeakingParticipants } from '@livekit/components-react';

/**
 * Custom hook to derive real-time, honest conversational states for AI Bots (ai-dost, ai-sathi):
 *
 * States:
 * - 'Speaking': The bot's audio track is actively emitting speech.
 * - 'Listening': A human participant in the room is actively producing speech.
 * - 'Thinking': Intermediate state immediately after human finishes speaking, while the backend
 *               STT (Whisper) and LLM (OpenRouter) pipeline processes the turn (~3.5s window).
 * - 'Ready': Idle, connected, listening and awaiting human speech.
 * - 'Connecting...': The bot has not yet connected to the room.
 */
export function useBotStates(fallbackParticipants = []) {
  const livekitParticipants = useParticipants();
  const speakingParticipants = useSpeakingParticipants();

  const participants =
    livekitParticipants && livekitParticipants.length > 0
      ? livekitParticipants
      : fallbackParticipants;

  const speakingIdentities = new Set(
    (speakingParticipants || []).map((p) => p.identity)
  );

  // Identify bots strictly by their unique identity
  const dost = participants.find((p) => p.identity === 'ai-dost');
  const sathi = participants.find((p) => p.identity === 'ai-sathi');

  const isDostSpeaking = Boolean(dost?.isSpeaking || speakingIdentities.has('ai-dost'));
  const isSathiSpeaking = Boolean(sathi?.isSpeaking || speakingIdentities.has('ai-sathi'));

  const anyHumanSpeaking = participants.some(
    (p) =>
      p.identity !== 'ai-dost' &&
      p.identity !== 'ai-sathi' &&
      (Boolean(p.isSpeaking) || speakingIdentities.has(p.identity))
  );

  const [isThinking, setIsThinking] = useState(false);
  const wasHumanSpeakingRef = useRef(false);

  useEffect(() => {
    let timer = null;

    if (anyHumanSpeaking) {
      wasHumanSpeakingRef.current = true;
    } else if (wasHumanSpeakingRef.current && !isDostSpeaking && !isSathiSpeaking) {
      wasHumanSpeakingRef.current = false;
      setIsThinking(true);
      timer = setTimeout(() => {
        setIsThinking(false);
      }, 3500);
    }

    return () => {
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [anyHumanSpeaking, isDostSpeaking, isSathiSpeaking]);

  const getBotStatus = (botParticipant, isSpeaking) => {
    if (!botParticipant) return 'Connecting...';
    if (isSpeaking) return 'Speaking';
    if (anyHumanSpeaking) return 'Listening';
    if (isThinking) return 'Thinking';
    return 'Ready';
  };

  return {
    participants,
    speakingIdentities,
    dost,
    sathi,
    isDostSpeaking,
    isSathiSpeaking,
    anyHumanSpeaking,
    isThinking,
    dostStatus: getBotStatus(dost, isDostSpeaking),
    sathiStatus: getBotStatus(sathi, isSathiSpeaking),
  };
}
