import { useState, useEffect, useCallback, useRef } from 'react';
import { useRoomContext, useConnectionState } from '@livekit/components-react';
import { RoomEvent, ConnectionState } from 'livekit-client';

/**
 * Hook to manage real-time text chat and unified conversation transcript in the LiveKit room.
 *
 * Supports:
 * - Sending text messages via publishData & sendText to the LiveKit room
 * - Receiving unified conversation turns (voice transcripts + text messages) from backend
 * - Hydrating history on initial connection via request_history
 * - Message statuses: 'sending' | 'sent' | 'failed'
 * - Preserving speaker attribution and chronological ordering
 */
export function useRoomChat() {
  const room = useRoomContext();
  const connectionState = useConnectionState();
  const [messages, setMessages] = useState([]);
  const [isSending, setIsSending] = useState(false);
  const [sendError, setSendError] = useState(null);
  const pendingQueueRef = useRef(new Map());

  // Helper to add or merge a message into chronological list without duplicates
  const mergeMessage = useCallback((newMsg) => {
    setMessages((prev) => {
      // Deduplicate by message ID
      const existingIdx = prev.findIndex((m) => m.id === newMsg.id);
      if (existingIdx !== -1) {
        const updated = [...prev];
        updated[existingIdx] = { ...updated[existingIdx], ...newMsg };
        return updated.sort((a, b) => a.timestamp - b.timestamp);
      }

      // Or deduplicate by matching speaker_id, text, and close timestamp (within 2s)
      const isDuplicate = prev.some(
        (m) =>
          m.speakerId === newMsg.speakerId &&
          m.text === newMsg.text &&
          Math.abs(m.timestamp - newMsg.timestamp) < 2000
      );
      if (isDuplicate) {
        return prev;
      }

      return [...prev, newMsg].sort((a, b) => a.timestamp - b.timestamp);
    });
  }, []);

  // Listen for incoming data channel packets
  useEffect(() => {
    if (!room) return;

    const handleDataReceived = (payload, participant) => {
      try {
        const text = new TextDecoder().decode(payload);
        const data = JSON.parse(text);

        if (data.type === 'conversation_turn') {
          mergeMessage({
            id: data.id || `turn-${Date.now()}`,
            speakerId: data.speaker_id || participant?.identity || 'unknown',
            speakerName: data.speaker_name || participant?.name || 'Participant',
            speakerType:
              data.speaker_type ||
              (data.speaker_id?.startsWith('ai-') ? data.speaker_id : 'human'),
            text: data.text || '',
            inputType: data.input_type || 'voice',
            timestamp: data.timestamp || Date.now(),
            status: 'sent',
          });
        } else if (data.type === 'conversation_history' && Array.isArray(data.turns)) {
          // Hydrate past conversation turns from backend memory
          setMessages((prev) => {
            const map = new Map();
            for (const t of data.turns) {
              map.set(t.id, {
                id: t.id,
                speakerId: t.speaker_id,
                speakerName: t.speaker_name,
                speakerType: t.speaker_type,
                text: t.text,
                inputType: t.input_type,
                timestamp: t.timestamp,
                status: 'sent',
              });
            }
            // Retain any pending local messages
            for (const m of prev) {
              if (!map.has(m.id)) {
                map.set(m.id, m);
              }
            }
            return Array.from(map.values()).sort((a, b) => a.timestamp - b.timestamp);
          });
        }
      } catch {
        // Non-JSON packet, ignore
      }
    };

    room.on(RoomEvent.DataReceived, handleDataReceived);

    // Request conversation history on initial mount / connection
    if (room.state === ConnectionState.Connected) {
      try {
        const req = JSON.stringify({ type: 'request_history' });
        room.localParticipant.publishData(new TextEncoder().encode(req), {
          reliable: true,
          topic: 'lk.chat',
        });
      } catch {
        // Ignore initial request failure
      }
    }

    return () => {
      room.off(RoomEvent.DataReceived, handleDataReceived);
    };
  }, [room, mergeMessage]);

  // Send a text chat message
  const sendMessage = useCallback(
    async (text) => {
      const trimmed = text.trim();
      if (!trimmed || !room || !room.localParticipant) return;

      const localP = room.localParticipant;
      const msgId = `msg-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
      const now = Date.now();

      const newMsg = {
        id: msgId,
        speakerId: localP.identity,
        speakerName: localP.name || 'You',
        speakerType: 'human',
        text: trimmed,
        inputType: 'text',
        timestamp: now,
        status: 'sending',
      };

      // Optimistically add to UI in 'sending' state
      setMessages((prev) => [...prev, newMsg]);
      pendingQueueRef.current.set(msgId, newMsg);
      setIsSending(true);
      setSendError(null);

      const packet = {
        type: 'chat_message',
        id: msgId,
        speaker_id: localP.identity,
        speaker_name: localP.name || 'User',
        speaker_type: 'human',
        text: trimmed,
        input_type: 'text',
        timestamp: now,
      };

      try {
        const encoded = new TextEncoder().encode(JSON.stringify(packet));
        await localP.publishData(encoded, {
          reliable: true,
          topic: 'lk.chat',
        });

        // Also send as standard text stream if supported
        if (typeof localP.sendText === 'function') {
          localP.sendText(trimmed, { topic: 'lk.chat' }).catch(() => {});
        }

        // Mark as sent
        setMessages((prev) =>
          prev.map((m) => (m.id === msgId ? { ...m, status: 'sent' } : m))
        );
        pendingQueueRef.current.delete(msgId);
      } catch (err) {
        setSendError(err.message || 'Failed to send message');
        // Mark as failed
        setMessages((prev) =>
          prev.map((m) => (m.id === msgId ? { ...m, status: 'failed' } : m))
        );
      } finally {
        setIsSending(false);
      }
    },
    [room]
  );

  // Retry a failed message
  const retryMessage = useCallback(
    async (msgId) => {
      const msg = messages.find((m) => m.id === msgId);
      if (!msg) return;

      setMessages((prev) =>
        prev.map((m) => (m.id === msgId ? { ...m, status: 'sending' } : m))
      );

      if (!room || !room.localParticipant) {
        setMessages((prev) =>
          prev.map((m) => (m.id === msgId ? { ...m, status: 'failed' } : m))
        );
        return;
      }

      const packet = {
        type: 'chat_message',
        id: msg.id,
        speaker_id: msg.speakerId,
        speaker_name: msg.speakerName,
        speaker_type: 'human',
        text: msg.text,
        input_type: 'text',
        timestamp: Date.now(),
      };

      try {
        const encoded = new TextEncoder().encode(JSON.stringify(packet));
        await room.localParticipant.publishData(encoded, {
          reliable: true,
          topic: 'lk.chat',
        });
        setMessages((prev) =>
          prev.map((m) => (m.id === msgId ? { ...m, status: 'sent' } : m))
        );
      } catch {
        setMessages((prev) =>
          prev.map((m) => (m.id === msgId ? { ...m, status: 'failed' } : m))
        );
      }
    },
    [messages, room]
  );

  return {
    messages,
    sendMessage,
    retryMessage,
    isSending,
    sendError,
    isReconnecting: connectionState === ConnectionState.Reconnecting,
    localIdentity: room?.localParticipant?.identity || '',
  };
}
