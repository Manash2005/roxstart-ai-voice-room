import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Mic,
  MessageSquare,
  Bot,
  Sparkles,
  User,
  AlertCircle,
  Clock,
  Check,
  RotateCw,
  ArrowDown,
  X,
  WifiOff,
} from 'lucide-react';
import { useRoomChat } from '../hooks/useRoomChat';

/**
 * Real-time Text Chat & Unified Conversation Transcript Panel.
 *
 * Displays both voice-transcribed turns and typed chat messages chronologically.
 * Features executive frosted glass styling and the bespoke 4-color palette:
 * - #4F7D32 (Forest Green)
 * - #FFD16A (Soft Cream)
 * - #F5B52E (Warm Amber Gold)
 * - #D9361E (Crimson Danger)
 *
 * @param {Object} props
 * @param {Function} [props.onClose] - Optional callback to close or dock the panel
 * @param {string} [props.localIdentity] - Current local participant identity for alignment
 */
export default function ChatPanel({ onClose, localIdentity = '' }) {
  const {
    messages,
    sendMessage,
    retryMessage,
    isSending,
    sendError,
    isReconnecting,
    localIdentity: hookLocalIdentity,
  } = useRoomChat();

  const effectiveLocalIdentity = hookLocalIdentity || localIdentity;

  const [inputText, setInputText] = useState('');
  const [userScrolledUp, setUserScrolledUp] = useState(false);
  const scrollContainerRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll logic: only auto-scroll if user has not scrolled up manually
  const scrollToBottom = (smooth = true) => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({
        behavior: smooth ? 'smooth' : 'auto',
        block: 'end',
      });
    }
  };

  const handleScroll = () => {
    const el = scrollContainerRef.current;
    if (!el) return;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 75;
    setUserScrolledUp(!isNearBottom);
  };

  useEffect(() => {
    if (!userScrolledUp) {
      scrollToBottom(true);
    }
  }, [messages, userScrolledUp]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const textToSend = inputText.trim();
    if (!textToSend || isSending) return;

    setInputText('');
    await sendMessage(textToSend);
    setUserScrolledUp(false);
    scrollToBottom(true);
  };

  const formatTimestamp = (ts) => {
    try {
      const date = new Date(ts);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  return (
    <div
      className="flex flex-col h-full bg-[#0c130c]/90 border border-white/[0.08] rounded-3xl shadow-2xl overflow-hidden backdrop-blur-2xl"
      data-testid="chat-panel"
    >
      {/* Top Chat Header */}
      <div className="px-5 py-4 border-b border-white/[0.08] flex items-center justify-between bg-[#121c12]/70">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#4F7D32]/25 border border-[#4F7D32]/40 flex items-center justify-center text-[#FFD16A]">
            <MessageSquare className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-stone-100 font-display">
              Room Conversation
            </h2>
            <span className="text-[11px] text-stone-400">
              Voice Transcripts &amp; Text Chat
            </span>
          </div>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            aria-label="Close Chat Panel"
            className="p-1.5 rounded-lg text-stone-400 hover:text-stone-100 hover:bg-white/[0.08] transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Reconnecting banner if WebRTC connection is temporarily disrupted */}
      {isReconnecting && (
        <div className="px-4 py-2 bg-[#F5B52E]/15 border-b border-[#F5B52E]/35 text-[#FFD16A] text-xs flex items-center gap-2">
          <WifiOff className="w-3.5 h-3.5 animate-pulse text-[#F5B52E] shrink-0" />
          <span>Reconnecting to room... messages will sync automatically.</span>
        </div>
      )}

      {/* Message List */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4"
        data-testid="chat-messages-container"
      >
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-stone-500">
            <div className="w-12 h-12 rounded-2xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center mb-3 text-stone-400">
              <MessageSquare className="w-6 h-6" />
            </div>
            <p className="text-sm font-medium text-stone-300">No messages yet</p>
            <p className="text-xs text-stone-500 mt-1 max-w-xs leading-relaxed">
              Speak into your microphone or type a question below in Hindi, Hinglish, or English.
            </p>
          </div>
        ) : (
          messages.map((msg) => {
            const isLocal =
              (effectiveLocalIdentity && msg.speakerId === effectiveLocalIdentity) ||
              (effectiveLocalIdentity && msg.speakerId.includes(effectiveLocalIdentity)) ||
              (localIdentity && msg.speakerName === localIdentity);
            const isDost =
              msg.speakerType === 'ai-dost' || msg.speakerId === 'ai-dost';
            const isSathi =
              msg.speakerType === 'ai-sathi' || msg.speakerId === 'ai-sathi';
            const isBot = isDost || isSathi;

            // Speaker badge styling
            let badgeStyle = {
              label: msg.speakerName || 'Participant',
              color: 'text-stone-300',
              bg: 'bg-white/[0.06] border-white/10',
              icon: User,
              bubbleBg: isLocal
                ? 'bg-[#4F7D32]/25 border-[#4F7D32]/45 text-stone-100'
                : 'bg-[#141d14]/80 border-white/[0.08] text-stone-200',
            };

            if (isDost) {
              badgeStyle = {
                label: 'AI Dost',
                color: 'text-[#FFD16A]',
                bg: 'bg-[#F5B52E]/15 border-[#F5B52E]/35',
                icon: Bot,
                bubbleBg: 'bg-[#1c180e]/80 border-[#F5B52E]/30 text-stone-100',
              };
            } else if (isSathi) {
              badgeStyle = {
                label: 'AI Sathi',
                color: 'text-[#a3d98b]',
                bg: 'bg-[#4F7D32]/20 border-[#4F7D32]/40',
                icon: Sparkles,
                bubbleBg: 'bg-[#0f1a0f]/80 border-[#4F7D32]/40 text-stone-100',
              };
            }

            const Icon = badgeStyle.icon;

            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isLocal && !isBot ? 'items-end' : 'items-start'}`}
                data-testid={`chat-message-${msg.id}`}
              >
                {/* Meta header: Speaker Name, Modality Badge, Timestamp */}
                <div className="flex items-center gap-2 mb-1 text-[11px] text-stone-400">
                  <span
                    className={`inline-flex items-center gap-1 font-semibold ${badgeStyle.color}`}
                  >
                    <Icon className="w-3 h-3" />
                    <span>{isLocal && !isBot ? `${msg.speakerName} (You)` : badgeStyle.label}</span>
                  </span>

                  {/* Input modality indicator: Voice vs Text */}
                  <span
                    className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] bg-white/[0.05] text-stone-400 border border-white/10"
                    title={msg.inputType === 'voice' ? 'Transcribed Voice Audio' : 'Typed Text Chat'}
                  >
                    {msg.inputType === 'voice' ? (
                      <>
                        <Mic className="w-2.5 h-2.5 text-[#4F7D32]" />
                        <span>voice</span>
                      </>
                    ) : (
                      <>
                        <MessageSquare className="w-2.5 h-2.5 text-[#FFD16A]" />
                        <span>text</span>
                      </>
                    )}
                  </span>

                  <span>{formatTimestamp(msg.timestamp)}</span>
                </div>

                {/* Message Bubble */}
                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 border text-sm leading-relaxed shadow-sm ${badgeStyle.bubbleBg}`}
                >
                  <p className="whitespace-pre-wrap break-words">{msg.text}</p>
                </div>

                {/* Status indicator for local outgoing message */}
                {isLocal && !isBot && (
                  <div className="flex items-center gap-1 mt-1 text-[10px] text-stone-500">
                    {msg.status === 'sending' && (
                      <span className="flex items-center gap-1 text-stone-400">
                        <Clock className="w-3 h-3 animate-spin text-[#FFD16A]" />
                        <span>sending...</span>
                      </span>
                    )}
                    {msg.status === 'sent' && (
                      <span className="flex items-center gap-0.5 text-[#4F7D32]">
                        <Check className="w-3 h-3" />
                        <span>sent</span>
                      </span>
                    )}
                    {msg.status === 'failed' && (
                      <span className="flex items-center gap-1 text-[#ff8e7d]">
                        <AlertCircle className="w-3 h-3 text-[#D9361E]" />
                        <span>failed</span>
                        <button
                          onClick={() => retryMessage(msg.id)}
                          className="ml-1 text-[11px] underline hover:text-white cursor-pointer flex items-center gap-0.5"
                        >
                          <RotateCw className="w-2.5 h-2.5" />
                          <span>Retry</span>
                        </button>
                      </span>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Floating 'Scroll to latest' button if user scrolled up */}
      {userScrolledUp && (
        <div className="flex justify-center -mt-8 mb-2 relative z-20">
          <button
            onClick={() => {
              setUserScrolledUp(false);
              scrollToBottom(true);
            }}
            className="px-3 py-1 rounded-full text-xs font-medium bg-[#121c12]/95 text-[#FFD16A] border border-[#FFD16A]/30 shadow-lg hover:bg-[#1a261a] transition flex items-center gap-1 cursor-pointer"
          >
            <ArrowDown className="w-3 h-3" />
            <span>Latest messages</span>
          </button>
        </div>
      )}

      {/* Send Error Notice */}
      {sendError && (
        <div className="px-4 py-1.5 bg-[#D9361E]/15 border-t border-[#D9361E]/35 text-[#ffb0a3] text-xs flex items-center gap-2">
          <AlertCircle className="w-3.5 h-3.5 text-[#D9361E] shrink-0" />
          <span className="truncate">{sendError}</span>
        </div>
      )}

      {/* Bottom Message Input Bar */}
      <form
        onSubmit={handleSubmit}
        className="p-3 border-t border-white/[0.08] bg-[#121c12]/80 flex items-center gap-2"
      >
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Ask in Hindi, English, or Hinglish..."
          maxLength={1000}
          disabled={isSending}
          className="flex-1 px-4 py-2.5 rounded-xl bg-[#090d09]/90 border border-white/10 text-stone-100 placeholder-stone-500 text-xs sm:text-sm focus:outline-none focus:border-[#4F7D32] focus:ring-1 focus:ring-[#4F7D32] transition"
        />
        <button
          type="submit"
          disabled={!inputText.trim() || isSending}
          aria-label="Send text message"
          className="px-3.5 py-2.5 rounded-xl font-medium text-xs bg-[#4F7D32] hover:bg-[#5a8c39] active:bg-[#436b2b] disabled:opacity-40 disabled:cursor-not-allowed text-[#FFD16A] border border-[#FFD16A]/20 shadow-md shadow-[#4F7D32]/25 transition flex items-center justify-center cursor-pointer"
        >
          {isSending ? (
            <Clock className="w-4 h-4 animate-spin text-[#FFD16A]" />
          ) : (
            <Send className="w-4 h-4 text-[#FFD16A]" />
          )}
        </button>
      </form>
    </div>
  );
}
