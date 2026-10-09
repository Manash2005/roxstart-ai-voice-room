# Roxstar AI Voice Room Assistant

A production-quality bilingual (Hindi, Hinglish, English) AI Voice Room Assistant built for the Roxstar AI Voice Room candidate assignment.

Operates with **two genuine LiveKit bot participants** (`ai-dost` and `ai-sathi`), shared contextual memory, deterministic arbitration, and a responsive React web interface adhering strictly to a **₹0-cost** architecture.

---

## 1. Architecture

```text
                                     LIVEKIT CLOUD (WebRTC Room)
                                                 │
                 ┌───────────────────────────────┴───────────────────────────────┐
                 ▼                                                               ▼
      React Web Frontend                                              Python Voice Agent Backend
       [Vite + React 19]                                            [LiveKit Agents 1.8.5 Worker]
        ├── Join Room & Landing Page                                  ├── Primary Room Ear: ai-dost
        │     ├── Name & Room Validation                              │     ├── Silero VAD (Local ONNX)
        │     └── Persona Showcase                                    │     └── Groq Whisper STT
        ├── RoomShell & Stage                                         ├── Secondary Participant: ai-sathi
        │     ├── Participant Grid                                    │     └── Local Piper TTS Output
        │     │     ├── Human 1 (Manash)                              ├── Shared ConversationMemory
        │     │     ├── Human 2 (Rahul)                               │     ├── Bounded FIFO (40 turns)
        │     │     ├── AI Dost (ai-dost)                             │     └── Voice + Text Unified
        │     │     └── AI Sathi (ai-sathi)                           ├── Turn Orchestration Layer
        │     ├── ChatPanel (lk.chat)                                 │     ├── TurnRouter (Dost vs Sathi)
        │     │     ├── Ephemeral Transcripts                         │     ├── ResponseArbitrator (Locking)
        │     │     └── Outgoing Text Chat                            │     └── LanguagePolicy (Bilingual)
        │     └── VoiceControls                                       └── Local Piper TTS Engine
        │           ├── Mute / Unmute                                       (hi_IN-rohan-medium ONNX)
        │           └── Clean Leave Room
        └── Secure HTTP Token API Client ◄─────────────────────────── Lightweight HTTP Server (aiohttp)
              (Zero API Secrets in Browser)                                (GET /health, POST /api/token)
```

### Key Architectural Highlights:
1. **Dual Genuine LiveKit Participants:** Both `ai-dost` and `ai-sathi` join the LiveKit room session simultaneously with genuine participant identities (`ai-dost` and `ai-sathi`).
2. **Unified In-Memory Conversation State:** Spoken voice turns (transcribed via Groq Whisper) and typed text chat messages enter a single shared `ConversationMemory`. Neither bot operates with isolated context.
3. **Deterministic Orchestration & Response Arbitration:** `TurnRouter` analyzes keywords and conversation ownership; `ResponseArbitrator` prevents overlapping bot speech with mutual exclusion locks.
4. **Secure Token Minting:** Browser clients connect via tokens minted by the backend API. Sensitive LiveKit, Groq, and OpenRouter API secrets remain strictly server-side.

---

## 2. Backend Setup

### Prerequisites
- Python 3.12+
- `uv` package manager ([astral.sh/uv](https://astral.sh/uv)):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### Step-by-Step Backend Installation
```bash
# 1. Navigate to project root
cd roxstar-ai-voice-room

# 2. Synchronize virtual environment and dependencies
uv sync --all-extras
```

### Automatic Model Download
Local Piper TTS models (`hi_IN-rohan-medium.onnx` and config) download automatically into `models/tts/` on initial run or synthesis if not already present.

---

## 3. Frontend Setup

### Prerequisites
- Node.js 18+ (verified on Node.js 20, 22, and 24)
- npm or pnpm

### Step-by-Step Frontend Installation
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install
```

### Frontend Technology Stack
- **Framework:** React + Vite
- **WebRTC Engine:** Official LiveKit React SDK (`@livekit/components-react`, `livekit-client`)
- **Styling:** Vanilla CSS + Tailwind CSS v4 with glassmorphism and ambient gradients
- **Icons:** Lucide React (`lucide-react`)
- **Testing:** Vitest + React Testing Library (18 automated tests)

---

## 4. Environment Variables

Create `.env.local` (takes precedence) or `.env` in the root repository directory:
```bash
cp .env.example .env.local
```

### Configuration Keys & Descriptions
```ini
# =====================================================================
# LIVEKIT CLOUD CONFIGURATION (WebRTC)
# Obtain from https://cloud.livekit.io
# =====================================================================
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# =====================================================================
# FREE-TIER AI PROVIDERS (₹0 Cost)
# =====================================================================
# OpenRouter Free LLM (from https://openrouter.ai/keys)
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_key
OPENROUTER_MODEL=openrouter/free

# Groq Cloud Whisper STT (from https://console.groq.com/keys)
GROQ_API_KEY=gsk_your_groq_key
GROQ_STT_MODEL=whisper-large-v3-turbo
# Leave blank for auto multilingual detection (Hindi, English, Hinglish)
GROQ_STT_LANGUAGE=

# =====================================================================
# LOCAL OPEN-SOURCE PIPER TTS (₹0 Cost, Local CPU / Apple Silicon)
# =====================================================================
TTS_MODEL=hi_IN-rohan-medium
TTS_DEVICE=cpu
TTS_SAMPLE_RATE=22050
TTS_AUTO_DOWNLOAD=true

# =====================================================================
# AGENT DEFAULTS & LOGGING
# =====================================================================
ACTIVE_PERSONA=dost
LOG_LEVEL=INFO
```

> [!IMPORTANT]
> **Zero Frontend Secrets:** The React frontend contains **NO** API keys or secrets (`LIVEKIT_API_SECRET`, `GROQ_API_KEY`, or `OPENROUTER_API_KEY`). Only the backend contains credentials.

---

## 5. LiveKit Cloud Setup

1. Sign up for a free developer account at [cloud.livekit.io](https://cloud.livekit.io).
2. Create a new project (e.g. `roxstar-demo`).
3. Under **Project Settings -> Keys**, retrieve:
   - **WebSocket URL** (`wss://<project>.livekit.cloud`)
   - **API Key** (`API...`)
   - **API Secret** (`secret...`)
4. Add these credentials to your `.env.local` file.

---

## 6. Running Locally

Running the complete application requires 3 terminal processes:

### Terminal 1: Token & Health HTTP API Server
```bash
uv run python -m app.api.server
```
*Listens on `http://0.0.0.0:8080`. Serves `GET /health` and `POST /api/token`.*

### Terminal 2: LiveKit Voice Agent Worker
```bash
uv run python -m app.agent dev
```
*Connects to LiveKit Cloud, initializes `ai-dost` and `ai-sathi`, and orchestrates room interactions.*

### Terminal 3: React Web Frontend
```bash
cd frontend
npm run dev
```
*Listens at `http://localhost:5173`.*

---

## 7. Two-Human Demo

Demonstrates multiple human participants conversing simultaneously alongside both AI bots:

1. **User 1 (Manash):**
   - Open `http://localhost:5173`.
   - Enter Display Name: `"Manash"`, Room: `"roxstar-demo"`.
   - Click **Enter Voice Room**.
2. **User 2 (Rahul):**
   - Open `http://localhost:5173` in a private window or separate browser.
   - Enter Display Name: `"Rahul"`, Room: `"roxstar-demo"`.
   - Click **Enter Voice Room**.
3. **Verify Participant Grid:**
   - Both human cards render: `"Manash (You)"` and `"Rahul"`.
   - Both AI bots appear: **AI Dost** (`ai-dost`) and **AI Sathi** (`ai-sathi`).
   - Active speaker rings activate whenever either human speaks.
   - Both human spoken turns enter shared `ConversationMemory` with correct speaker attribution.

---

## 8. Voice Demo

Test natural bilingual conversation, routing, and speech synthesis:

1. **Casual English Question (Routes to AI Dost):**
   - Speak: *"Hey Dost, explain what React is in simple terms."*
   - **Result:** AI Dost answers in friendly, accessible English.
2. **Technical Comparative Question (Routes to AI Sathi):**
   - Speak: *"Sathi, what is the architectural difference between PostgreSQL and MongoDB?"*
   - **Result:** Explicit routing directs turn to AI Sathi; answers with structured technical analysis.
3. **Conversational Hinglish Question:**
   - Speak: *"React mein state management ke liye Redux kyu use karte hain?"*
   - **Result:** Bot answers in natural, code-mixed Hinglish matching the user's cadence.
4. **Persistent Language Switch:**
   - Speak: *"Ab se purely English mein answer karo."*
   - **Result:** Dynamic `LanguagePolicy` locks conversation to English for subsequent turns.

---

## 9. Text Demo

Test unified text chat and transcript streaming via LiveKit data channel (`lk.chat`):

1. Click the **Chat** button in the header or bottom control bar.
2. Type in the input field:
   ```text
   Explain React in simple terms.
   ```
3. Click **Send** (or press Enter).
4. **Result:**
   - User message displays `sent` status with a `text` modality badge.
   - Backend ingests text into `ConversationMemory` and dispatches turn to AI Dost.
   - AI Dost synthesizes reply and broadcasts `conversation_turn` packet.
   - Bot reply displays in `ChatPanel` chronologically with a `voice` modality badge.

---

## 10. AI Dost & AI Sathi Behavior

| Persona | Identity | Display Name | Role & Style | Primary Routing Triggers |
| :--- | :--- | :--- | :--- | :--- |
| **AI Dost** | `ai-dost` | AI Dost | Friendly, warm, casual, approachable conversational companion. | Greetings, casual questions, general concepts, collaborative queries, default fallback. |
| **AI Sathi** | `ai-sathi` | AI Sathi | Calm, analytical, technical, structured specialist. | Architecture, benchmarking, code comparisons, technical trade-offs, explicit address. |

### Collision Handling & Mutual Exclusion
- When AI Dost is speaking, AI Sathi will not interrupt.
- When AI Sathi is speaking, user speech triggers a barge-in interrupt, releasing the mutual exclusion lock cleanly.

---

## 11. Language Behavior

The application natively supports **Hindi**, **English**, **Hinglish**, and **Roman Hindi**:
- **Automatic Detection:** `LanguagePolicy` inspects transcribed tokens for Devanagari script and Romanized Hindi marker terms (e.g., `hai`, `kya`, `karo`, `kaise`).
- **Dynamic Matching:**
  - Pure English input -> Pure English output.
  - Devanagari Hindi input -> Devanagari Hindi output.
  - Hinglish / Mixed input -> Natural conversational Hinglish output.
- **Zero Frontend Translation:** The frontend never modifies or translates user messages; all text is preserved verbatim.

---

## 12. Latency Logging

Every conversational turn outputs structured monotonic latency instrumentation in worker logs:
```text
[latency] turn=e1a47b stt=412ms routing=2ms llm=541ms tts_first=168ms total_first_audio=1123ms
```
- `stt`: Speech-to-text transcript turnaround (Groq Whisper turbo).
- `routing`: Turn routing & mutual exclusion arbitration.
- `llm`: OpenRouter streaming time-to-first-token.
- `tts_first`: Local Piper ONNX synthesis latency for the first sentence chunk.
- `total_first_audio`: Total turnaround time from end of human speech to first emitted WebRTC audio sample.

---

## 13. Known Limitations

1. **Single Voice Model:** Both AI Dost and AI Sathi synthesize speech using the local Hindi ONNX voice (`hi_IN-rohan-medium`). Sathi does not currently have a separate female voice model, avoiding paid or unverified cloud TTS services.
2. **Primary Room Ear:** `ai-dost` transcribes speech for the room; `ai-sathi` is connected as a genuine participant for output speech. This satisfies the ₹0-cost constraint without doubling STT costs.
3. **WebRTC Speaker Attribution:** Participant attribution is based on WebRTC participant IDs (`speaker_id`), not acoustic voiceprint biometrics.
4. **Sequential Turn Focus:** LiveKit RoomIO focuses on the dominant active human speaker when multiple humans speak at the same instant.
5. **Upstream Rate Limits:** Free-tier services (Groq Whisper, OpenRouter Free) are subject to upstream RPM limits during peak hours.

---

## 14. ₹0-Cost Architecture Compliance

| Component | Provider / Tool | Cost | Rationale |
| :--- | :--- | :--- | :--- |
| **Realtime WebRTC** | LiveKit Cloud (Free Developer Tier) | ₹0 | Generous free bandwidth and WebRTC room sessions. |
| **STT** | Groq Whisper (`whisper-large-v3-turbo`) | ₹0 | Ultra-low latency transcription on free tier. |
| **LLM** | OpenRouter (`openrouter/free`) | ₹0 | Free-tier models with zero credit card requirements. |
| **VAD** | Silero VAD (Local ONNX) | ₹0 | Runs 100% locally on CPU without external requests. |
| **TTS** | Piper TTS (`hi_IN-rohan-medium`) | **₹0** | **Runs 100% locally on CPU / Apple Silicon. No API keys.** |
| **Token API & Routing** | Python in-memory API & Orchestrator | ₹0 | Self-contained local execution. |
| **Paid Services** | LiveKit Inference / OpenAI Paid API / ElevenLabs | **NONE** | **Strictly prohibited & omitted.** |

---

## 15. Deployment Instructions

### Production Frontend Build
```bash
cd frontend
npm run build
```
Generates optimized static assets in `frontend/dist/`. Can be served with Nginx, Caddy, or Cloudflare Pages.

### Running Backend Services with Process Supervision
Run the 2 backend services using Docker, systemd, or supervisord:
1. **API Service:**
   ```bash
   uv run python -m app.api.server
   ```
2. **LiveKit Agent Worker:**
   ```bash
   uv run python -m app.agent start
   ```

### Verification Test Commands
```bash
# Run all frontend tests (18 tests)
cd frontend && npm test

# Run frontend linter
cd frontend && npm run lint

# Run all backend unit tests (117 tests)
uv run pytest -v

# Run backend linter & formatter
uvx ruff check .
uvx ruff format --check .
```
