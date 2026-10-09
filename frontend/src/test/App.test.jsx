import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within, act } from '@testing-library/react';
import App from '../App';
import * as api from '../api';

const mockSetMicrophoneEnabled = vi.fn();
let mockParticipantsList = [
  { identity: 'user-1', name: 'Manash', isLocal: true, isSpeaking: false, isMicrophoneEnabled: true },
  { identity: 'ai-dost', name: 'AI Dost', isLocal: false, isSpeaking: true, isMicrophoneEnabled: true },
  { identity: 'ai-sathi', name: 'AI Sathi', isLocal: false, isSpeaking: false, isMicrophoneEnabled: true },
];
let mockSpeakingList = [];
let currentConnectionState = 'connected';
let dataReceivedHandlers = [];
const mockPublishData = vi.fn().mockImplementation(() => Promise.resolve(new Uint8Array()));
const mockSendText = vi.fn().mockResolvedValue({ id: 'msg-1' });

let mockRoom = {
  state: 'connected',
  localParticipant: {
    identity: 'user-1',
    name: 'Manash',
    publishData: mockPublishData,
    sendText: mockSendText,
  },
  on(event, handler) {
    dataReceivedHandlers.push(handler);
  },
  off(event, handler) {
    dataReceivedHandlers = dataReceivedHandlers.filter((h) => h !== handler);
  },
};

// Mock LiveKit React components and hooks
vi.mock('@livekit/components-react', () => ({
  LiveKitRoom: ({ children }) => <div data-testid="mock-livekit-room">{children}</div>,
  RoomAudioRenderer: () => <div data-testid="mock-audio-renderer" />,
  StartAudio: () => <div data-testid="mock-start-audio" />,
  useConnectionState: () => currentConnectionState,
  useRoomContext: () => mockRoom,
  useParticipants: () => mockParticipantsList,
  useSpeakingParticipants: () => mockSpeakingList,
  useLocalParticipant: () => ({
    localParticipant: {
      isMicrophoneEnabled: true,
      setMicrophoneEnabled: mockSetMicrophoneEnabled,
    },
  }),
}));

describe('Roxstar AI Voice Room Frontend — Checkpoint 8C', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockSetMicrophoneEnabled.mockReset();
    mockParticipantsList = [
      { identity: 'user-1', name: 'Manash', isLocal: true, isSpeaking: false, isMicrophoneEnabled: true },
      { identity: 'ai-dost', name: 'AI Dost', isLocal: false, isSpeaking: true, isMicrophoneEnabled: true },
      { identity: 'ai-sathi', name: 'AI Sathi', isLocal: false, isSpeaking: false, isMicrophoneEnabled: true },
    ];
    mockSpeakingList = [];
  });

  it('renders the Join Page with logo, inputs, and button', () => {
    render(<App />);

    expect(screen.getAllByText(/Roxstar AI Voice Room/i)[0]).toBeInTheDocument();
    expect(screen.getByLabelText(/Your Display Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Room Name/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /(Enter|Join) Voice Room/i })).toBeInTheDocument();
  });

  it('validates empty name input and displays an error message', async () => {
    render(<App />);

    const joinButton = screen.getByRole('button', { name: /(Enter|Join) Voice Room/i });
    const nameInput = screen.getByLabelText(/Your Display Name/i);

    fireEvent.change(nameInput, { target: { value: '' } });
    fireEvent.click(joinButton);

    await waitFor(() => {
      expect(screen.getByText(/Please enter your name to join the room/i)).toBeInTheDocument();
    });
  });

  it('validates empty room name and displays an error message', async () => {
    render(<App />);

    const nameInput = screen.getByLabelText(/Your Display Name/i);
    const roomInput = screen.getByLabelText(/Room Name/i);
    const joinButton = screen.getByRole('button', { name: /(Enter|Join) Voice Room/i });

    fireEvent.change(nameInput, { target: { value: 'Manash' } });
    fireEvent.change(roomInput, { target: { value: '' } });
    fireEvent.click(joinButton);

    await waitFor(() => {
      expect(screen.getByText(/Please enter a room name/i)).toBeInTheDocument();
    });
  });

  it('shows loading state when acquiring token', async () => {
    vi.spyOn(api, 'requestRoomToken').mockImplementation(
      () => new Promise(() => {})
    );

    render(<App />);

    fireEvent.change(screen.getByLabelText(/Your Display Name/i), { target: { value: 'Manash' } });
    fireEvent.click(screen.getByRole('button', { name: /(Enter|Join) Voice Room/i }));

    await waitFor(() => {
      expect(screen.getByText(/Connecting to LiveKit/i)).toBeInTheDocument();
    });
  });

  it('handles backend API network failure gracefully', async () => {
    vi.spyOn(api, 'requestRoomToken').mockRejectedValue(
      new Error('Backend is unavailable. Cannot connect to backend API server at http://localhost:8080.')
    );

    render(<App />);

    fireEvent.change(screen.getByLabelText(/Your Display Name/i), { target: { value: 'Manash' } });
    fireEvent.click(screen.getByRole('button', { name: /(Enter|Join) Voice Room/i }));

    await waitFor(() => {
      expect(screen.getByText(/Backend is unavailable/i)).toBeInTheDocument();
    });
  });

  it('successfully transitions to live room on valid token acquisition', async () => {
    vi.spyOn(api, 'requestRoomToken').mockResolvedValue({
      token: 'mock-jwt-token',
      url: 'wss://test.livekit.cloud',
    });

    render(<App />);

    fireEvent.change(screen.getByLabelText(/Your Display Name/i), { target: { value: 'Manash' } });
    fireEvent.click(screen.getByRole('button', { name: /(Enter|Join) Voice Room/i }));

    await waitFor(() => {
      expect(screen.getByTestId('mock-livekit-room')).toBeInTheDocument();
      expect(screen.getAllByText('Manash').length).toBeGreaterThan(0);
      expect(screen.getAllByText(/AI Dost/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/AI Sathi/i).length).toBeGreaterThan(0);
    });
  });

  it('supports multiple human participants (two-human demo: Manash + Rahul + bots)', async () => {
    mockParticipantsList = [
      { identity: 'user-manash', name: 'Manash', isLocal: true, isSpeaking: false, isMicrophoneEnabled: true },
      { identity: 'user-rahul', name: 'Rahul', isLocal: false, isSpeaking: false, isMicrophoneEnabled: true },
      { identity: 'ai-dost', name: 'AI Dost', isLocal: false, isSpeaking: false, isMicrophoneEnabled: true },
      { identity: 'ai-sathi', name: 'AI Sathi', isLocal: false, isSpeaking: false, isMicrophoneEnabled: true },
    ];

    vi.spyOn(api, 'requestRoomToken').mockResolvedValue({
      token: 'mock-jwt-token',
      url: 'wss://test.livekit.cloud',
    });

    render(<App />);

    fireEvent.change(screen.getByLabelText(/Your Display Name/i), { target: { value: 'Manash' } });
    fireEvent.click(screen.getByRole('button', { name: /(Enter|Join) Voice Room/i }));

    await waitFor(() => {
      // Both humans rendered alongside both bots
      expect(screen.getByTestId('participant-card-user-manash')).toBeInTheDocument();
      expect(screen.getByTestId('participant-card-user-rahul')).toBeInTheDocument();
      expect(screen.getByTestId('participant-card-ai-dost')).toBeInTheDocument();
      expect(screen.getByTestId('participant-card-ai-sathi')).toBeInTheDocument();
      expect(screen.getByText('Rahul')).toBeInTheDocument();
      expect(screen.getByText('AI Host & Listener')).toBeInTheDocument();
      expect(screen.getByText('AI Specialist')).toBeInTheDocument();
    });
  });

  it('displays active speaker indicator and speaking status when a participant speaks', async () => {
    mockParticipantsList = [
      { identity: 'user-1', name: 'Manash', isLocal: true, isSpeaking: false, isMicrophoneEnabled: true },
      { identity: 'ai-dost', name: 'AI Dost', isLocal: false, isSpeaking: true, isMicrophoneEnabled: true },
      { identity: 'ai-sathi', name: 'AI Sathi', isLocal: false, isSpeaking: false, isMicrophoneEnabled: true },
    ];

    vi.spyOn(api, 'requestRoomToken').mockResolvedValue({
      token: 'mock-jwt-token',
      url: 'wss://test.livekit.cloud',
    });

    render(<App />);

    fireEvent.change(screen.getByLabelText(/Your Display Name/i), { target: { value: 'Manash' } });
    fireEvent.click(screen.getByRole('button', { name: /(Enter|Join) Voice Room/i }));

    await waitFor(() => {
      expect(screen.getByTestId('participant-card-ai-dost')).toBeInTheDocument();
      expect(screen.getAllByText(/Speaking.../i).length).toBeGreaterThan(0);
    });
  });

  it('toggles microphone state when Mute button is clicked', async () => {
    mockSetMicrophoneEnabled.mockResolvedValue(true);

    vi.spyOn(api, 'requestRoomToken').mockResolvedValue({
      token: 'mock-jwt-token',
      url: 'wss://test.livekit.cloud',
    });

    render(<App />);

    fireEvent.change(screen.getByLabelText(/Your Display Name/i), { target: { value: 'Manash' } });
    fireEvent.click(screen.getByRole('button', { name: /(Enter|Join) Voice Room/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Mute microphone/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Mute microphone/i }));

    expect(mockSetMicrophoneEnabled).toHaveBeenCalledWith(false);
  });

  it('displays microphone permission error if permission is denied', async () => {
    const permError = new Error('Permission denied');
    permError.name = 'NotAllowedError';
    mockSetMicrophoneEnabled.mockRejectedValue(permError);

    vi.spyOn(api, 'requestRoomToken').mockResolvedValue({
      token: 'mock-jwt-token',
      url: 'wss://test.livekit.cloud',
    });

    render(<App />);

    fireEvent.change(screen.getByLabelText(/Your Display Name/i), { target: { value: 'Manash' } });
    fireEvent.click(screen.getByRole('button', { name: /(Enter|Join) Voice Room/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Mute microphone/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Mute microphone/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/Microphone permission was denied. Please allow microphone access/i)
      ).toBeInTheDocument();
    });
  });

  it('cleans up and returns to lobby when Leave Room button is clicked', async () => {
    vi.spyOn(api, 'requestRoomToken').mockResolvedValue({
      token: 'mock-jwt-token',
      url: 'wss://test.livekit.cloud',
    });

    render(<App />);

    fireEvent.change(screen.getByLabelText(/Your Display Name/i), { target: { value: 'Manash' } });
    fireEvent.click(screen.getByRole('button', { name: /(Enter|Join) Voice Room/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Leave voice room/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Leave voice room/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /(Enter|Join) Voice Room/i })).toBeInTheDocument();
      expect(screen.queryByTestId('mock-livekit-room')).not.toBeInTheDocument();
    });
  });
});

function simulateDataReceived(payloadObj, participant = null) {
  act(() => {
    const encoded = new TextEncoder().encode(JSON.stringify(payloadObj));
    dataReceivedHandlers.forEach((handler) => handler(encoded, participant));
  });
}

describe('Roxstar AI Voice Room Frontend — Checkpoint 8D Text Chat & Conversation Transcript', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mockSetMicrophoneEnabled.mockReset();
    mockPublishData.mockReset().mockImplementation(() => Promise.resolve(new Uint8Array()));
    mockSendText.mockReset().mockResolvedValue({ id: 'msg-1' });
    dataReceivedHandlers = [];
    currentConnectionState = 'connected';
    mockParticipantsList = [
      { identity: 'user-1', name: 'Manash', isLocal: true, isSpeaking: false, isMicrophoneEnabled: true },
      { identity: 'ai-dost', name: 'AI Dost', isLocal: false, isSpeaking: false, isMicrophoneEnabled: true },
      { identity: 'ai-sathi', name: 'AI Sathi', isLocal: false, isSpeaking: false, isMicrophoneEnabled: true },
    ];
    mockSpeakingList = [];
    vi.spyOn(api, 'requestRoomToken').mockResolvedValue({
      token: 'mock-jwt-token',
      url: 'wss://test.livekit.cloud',
    });
  });

  const joinLiveRoom = async () => {
    render(<App />);
    fireEvent.change(screen.getByLabelText(/Your Display Name/i), { target: { value: 'Manash' } });
    fireEvent.click(screen.getByRole('button', { name: /(Enter|Join) Voice Room/i }));
    await waitFor(() => {
      expect(screen.getByTestId('chat-panel')).toBeInTheDocument();
    });
  };

  it('allows user to type "Explain React in simple terms." and send via LiveKit text/data mechanism', async () => {
    await joinLiveRoom();

    const input = screen.getByPlaceholderText(/Ask in Hindi, English, or Hinglish/i);
    const sendButton = screen.getByRole('button', { name: /Send text message/i });

    fireEvent.change(input, { target: { value: 'Explain React in simple terms.' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockPublishData).toHaveBeenCalled();
    });

    const chatCall = mockPublishData.mock.calls.find(([payload]) => {
      try {
        const decoded = JSON.parse(new TextDecoder().decode(payload));
        return decoded.type === 'chat_message';
      } catch {
        return false;
      }
    });
    expect(chatCall).toBeDefined();
    const [payload, opts] = chatCall;
    const decoded = JSON.parse(new TextDecoder().decode(payload));
    expect(decoded.type).toBe('chat_message');
    expect(decoded.text).toBe('Explain React in simple terms.');
    expect(decoded.speaker_id).toBe('user-1');
    expect(decoded.input_type).toBe('text');
    expect(opts.topic).toBe('lk.chat');

    await waitFor(() => {
      expect(screen.getByText('Explain React in simple terms.')).toBeInTheDocument();
      expect(screen.getByText('sent')).toBeInTheDocument();
    });
  });

  it('receives voice transcript turn and displays speaker, voice modality badge, and timestamp', async () => {
    await joinLiveRoom();

    simulateDataReceived({
      type: 'conversation_turn',
      id: 'turn-dost-voice-1',
      speaker_id: 'ai-dost',
      speaker_name: 'AI Dost',
      speaker_type: 'ai-dost',
      text: 'React mein state management simple hooks se shuru hota hai.',
      input_type: 'voice',
      timestamp: 1710000000000,
    });

    const chat = within(screen.getByTestId('chat-panel'));
    await waitFor(() => {
      expect(chat.getByText('React mein state management simple hooks se shuru hota hai.')).toBeInTheDocument();
      expect(chat.getByText('AI Dost')).toBeInTheDocument();
      expect(chat.getByText('voice')).toBeInTheDocument();
    });
  });

  it('displays multi-speaker conversation with correct speaker attribution and modalities', async () => {
    await joinLiveRoom();

    // 1. Manash voice turn
    simulateDataReceived({
      type: 'conversation_turn',
      id: 'turn-1',
      speaker_id: 'user-1',
      speaker_name: 'Manash',
      speaker_type: 'human',
      text: 'React mein state management kaise karte hain?',
      input_type: 'voice',
      timestamp: 1000,
    });

    // 2. AI Dost voice turn
    simulateDataReceived({
      type: 'conversation_turn',
      id: 'turn-2',
      speaker_id: 'ai-dost',
      speaker_name: 'AI Dost',
      speaker_type: 'ai-dost',
      text: 'React mein useState hook sabse basic tarika hai!',
      input_type: 'voice',
      timestamp: 2000,
    });

    // 3. AI Sathi voice turn
    simulateDataReceived({
      type: 'conversation_turn',
      id: 'turn-3',
      speaker_id: 'ai-sathi',
      speaker_name: 'AI Sathi',
      speaker_type: 'ai-sathi',
      text: 'Technically, server state ke liye React Query aur complex state ke liye Redux/Zustand standard hain.',
      input_type: 'voice',
      timestamp: 3000,
    });

    // 4. Rahul (another human participant) text turn
    simulateDataReceived({
      type: 'conversation_turn',
      id: 'turn-4',
      speaker_id: 'user-rahul',
      speaker_name: 'Rahul',
      speaker_type: 'human',
      text: 'Can you explain that again?',
      input_type: 'text',
      timestamp: 4000,
    });

    const chat = within(screen.getByTestId('chat-panel'));
    await waitFor(() => {
      expect(chat.getByText('React mein state management kaise karte hain?')).toBeInTheDocument();
      expect(chat.getByText('React mein useState hook sabse basic tarika hai!')).toBeInTheDocument();
      expect(chat.getByText('Technically, server state ke liye React Query aur complex state ke liye Redux/Zustand standard hain.')).toBeInTheDocument();
      expect(chat.getByText('Can you explain that again?')).toBeInTheDocument();

      expect(chat.getByText('Manash (You)')).toBeInTheDocument();
      expect(chat.getByText('AI Dost')).toBeInTheDocument();
      expect(chat.getByText('AI Sathi')).toBeInTheDocument();
      expect(chat.getByText('Rahul')).toBeInTheDocument();

      const voiceBadges = chat.getAllByText('voice');
      const textBadges = chat.getAllByText('text');
      expect(voiceBadges.length).toBe(3);
      expect(textBadges.length).toBe(1);
    });
  });

  it('orders messages chronologically even when turns arrive out of order', async () => {
    await joinLiveRoom();

    simulateDataReceived({
      type: 'conversation_turn',
      id: 'turn-later',
      speaker_id: 'ai-dost',
      speaker_name: 'AI Dost',
      speaker_type: 'ai-dost',
      text: 'Second message in time',
      input_type: 'voice',
      timestamp: 5000,
    });

    simulateDataReceived({
      type: 'conversation_turn',
      id: 'turn-earlier',
      speaker_id: 'user-1',
      speaker_name: 'Manash',
      speaker_type: 'human',
      text: 'First message in time',
      input_type: 'text',
      timestamp: 2000,
    });

    await waitFor(() => {
      const container = screen.getByTestId('chat-messages-container');
      const messageElements = container.querySelectorAll('[data-testid^="chat-message-"]');
      expect(messageElements.length).toBe(2);
      expect(messageElements[0]).toHaveTextContent('First message in time');
      expect(messageElements[1]).toHaveTextContent('Second message in time');
    });
  });

  it('handles message send failure with retry capability', async () => {
    await joinLiveRoom();

    mockPublishData.mockRejectedValueOnce(new Error('Network error on send'));

    const input = screen.getByPlaceholderText(/Ask in Hindi, English, or Hinglish/i);
    const sendButton = screen.getByRole('button', { name: /Send text message/i });

    fireEvent.change(input, { target: { value: 'Why does useEffect run twice?' } });
    fireEvent.click(sendButton);

    const chat = within(screen.getByTestId('chat-panel'));
    await waitFor(() => {
      expect(chat.getByText('failed')).toBeInTheDocument();
      expect(chat.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
    });

    mockPublishData.mockResolvedValueOnce(new Uint8Array());
    fireEvent.click(chat.getByRole('button', { name: /Retry/i }));

    await waitFor(() => {
      expect(chat.getByText('sent')).toBeInTheDocument();
      expect(chat.queryByText('failed')).not.toBeInTheDocument();
    });
  });

  it('displays reconnecting status banner when WebRTC reconnects', async () => {
    currentConnectionState = 'reconnecting';
    await joinLiveRoom();

    expect(
      screen.getByText(/Reconnecting to room... messages will sync automatically/i)
    ).toBeInTheDocument();
  });

  it('hydrates full conversation history when backend sends conversation_history packet', async () => {
    await joinLiveRoom();

    simulateDataReceived({
      type: 'conversation_history',
      turns: [
        {
          id: 'hist-1',
          speaker_id: 'user-1',
          speaker_name: 'Manash',
          speaker_type: 'human',
          text: 'Pehle ka sawal',
          input_type: 'voice',
          timestamp: 100,
        },
        {
          id: 'hist-2',
          speaker_id: 'ai-dost',
          speaker_name: 'AI Dost',
          speaker_type: 'ai-dost',
          text: 'Pehle ka jawab',
          input_type: 'voice',
          timestamp: 200,
        },
      ],
    });

    await waitFor(() => {
      expect(screen.getByText('Pehle ka sawal')).toBeInTheDocument();
      expect(screen.getByText('Pehle ka jawab')).toBeInTheDocument();
    });
  });
});
