# Roxstar AI Voice Room Assistant

A production-quality Python realtime voice assistant project built for the Roxstar AI Voice Room candidate assignment.

## 1. What the Project Is

This project provides an AI Voice Room Assistant designed to participate in multi-user voice rooms, understand bilingual/code-mixed speech (Hindi, Hinglish, and English), and respond naturally and conversationally. The project is constructed incrementally across distinct checkpoints, adhering strictly to a **₹0-cost** architecture utilizing free tiers and open-source models.

---

## 2. Current Checkpoint: Checkpoint 1 (Foundation)

**Checkpoint 1** establishes the core foundation:
- Clean, typed Python architecture with strict separation of concerns (`app/agent.py`, `app/config.py`, `app/logging.py`).
- LiveKit Agents realtime framework integration.
- OpenRouter LLM integration via LiveKit's OpenAI-compatible plugin configured for free models.
- Groq Whisper STT plugin integration with Hindi/Hinglish configuration.
- A clearly marked temporary TTS stub architecture (avoiding paid services while decoupling audio synthesis).
- Environment management via `python-dotenv` with strict validation.
- Modern dependency management using `uv`.
- Full unit test suite with 100% passing tests.

---

## 3. Technology Stack

- **Language & Runtime:** Python 3.12 (managed via `uv`)
- **Realtime Framework:** [LiveKit Agents](https://docs.livekit.io/agents/) (`livekit-agents` v1.8.5)
- **STT (Speech-to-Text):** [Groq Cloud Whisper](https://groq.com/) (`whisper-large-v3-turbo`) via `livekit-plugins-groq`
- **LLM (Language Model):** [OpenRouter](https://openrouter.ai/) (default: `openrouter/free`) via `livekit-plugins-openai`
- **VAD (Voice Activity Detection):** Silero VAD (local open-source inference bundled with LiveKit Agents)
- **TTS (Text-to-Speech):** `TemporaryStubTTS` (placeholder stub; local/open-source model integrated in Checkpoint 2)
- **Dependency Management:** `uv`
- **Configuration:** Typed `Settings` class with `python-dotenv`
- **Testing:** `pytest` & `pytest-asyncio`

---

## 4. Why LiveKit Is Being Used

LiveKit is used exclusively as the **realtime WebRTC transport, room state manager, and agent lifecycle orchestrator**. 
- It handles low-latency duplex audio streaming, room participant tracking, and worker process lifecycle out of the box.
- It abstracts the complexities of WebRTC peer connections, room events, and audio publishing/subscribing.
- **Important:** LiveKit is used solely as the realtime orchestration framework; paid LiveKit Inference features are explicitly **not** used.

---

## 5. Why OpenRouter Is Being Used

OpenRouter serves as a flexible, zero-cost LLM gateway:
- **₹0 Cost:** OpenRouter hosts multiple free models (`openrouter/free`, `meta-llama/llama-3.3-70b-instruct:free`, etc.) without subscription costs.
- **OpenAI-Compatible API:** Operates seamlessly with `livekit-plugins-openai` using the factory pattern `openai.LLM.with_openrouter(...)`.
- **Configurability:** The model identifier is strictly decoupled into an environment variable (`OPENROUTER_MODEL`), allowing instant model swapping without code changes.

---

## 6. Why Groq STT Is Being Used

Groq Whisper (`whisper-large-v3-turbo`) provides ultra-fast speech recognition:
- **Free Tier:** Groq offers a generous free-tier API with high token and audio-second rate limits.
- **Low Latency:** Groq's LPU architecture achieves near real-time transcription speeds (<300ms for short utterances), critical for conversational voice agents.
- **Multilingual Support:** Handles Hindi and Hinglish speech transcription effectively. STT configuration is isolated in `create_stt()` for easy extension.

---

## 7. Why TTS Is Intentionally Deferred

Text-to-Speech (TTS) is intentionally **deferred to Checkpoint 2**:
- **Zero-Cost Constraint:** Commercial TTS services (OpenAI TTS, ElevenLabs, Azure) incur paid API costs.
- **No LiveKit Inference:** LiveKit's managed inference TTS is explicitly excluded to maintain ₹0 cost.
- **Local/Open-Source Focus:** Hindi/Hinglish voice synthesis requires a specialized open-source or local TTS solution (e.g., Kokoro, XTTS, Bark, or Indic-TTS). Checkpoint 2 will integrate a dedicated local/open-source TTS engine.
- **Checkpoint 1 Architecture:** An explicit `TemporaryStubTTS` adapter satisfies LiveKit's `AgentSession` pipeline contract during Checkpoint 1 without calling any paid external service.

---

## 8. ₹0-Cost Architecture & Policy Compliance

| Component | Provider / Tool | Cost | Rationale |
| :--- | :--- | :--- | :--- |
| **Realtime WebRTC** | LiveKit Cloud (Free tier) or self-hosted | ₹0 | Standard developer tier handles dev rooms and agent jobs. |
| **STT** | Groq Whisper (`whisper-large-v3-turbo`) | ₹0 | Generous free tier with ultra-low latency. |
| **LLM** | OpenRouter (`openrouter/free`) | ₹0 | Free-tier models accessed via standard API keys. |
| **VAD** | Silero VAD (local ONNX/Inference) | ₹0 | Runs locally on CPU, no external network requests. |
| **TTS** | Temporary Adapter (Local OSS in Checkpoint 2) | ₹0 | Zero cost; no paid third-party voice APIs. |
| **Paid Inference** | LiveKit Inference / OpenAI Paid API | **NONE** | **Strictly prohibited & omitted.** |

---

## 9. Installation & Setup

### Prerequisites

- Python 3.12+
- `uv` (Fast Python package manager):
  ```bash
  # macOS / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### Step 1: Clone and Navigate
```bash
cd roxstart-ai-voice-room
```

### Step 2: Install Dependencies with uv
```bash
uv sync --all-extras
```
This automatically configures the `.venv` virtual environment with Python 3.12 and installs all production and development dependencies locked in `uv.lock`.

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in your free credentials:
```ini
# LiveKit Cloud credentials (from https://cloud.livekit.io)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# OpenRouter free tier key (from https://openrouter.ai/keys)
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_key
OPENROUTER_MODEL=openrouter/free

# Groq free tier key (from https://console.groq.com/keys)
GROQ_API_KEY=gsk_your_groq_api_key
GROQ_STT_MODEL=whisper-large-v3-turbo
GROQ_STT_LANGUAGE=hi

# Logging
LOG_LEVEL=INFO
```

---

## 10. Running the Application

### View CLI Options
```bash
uv run python -m app.agent --help
```

### Run in Development Mode
To start the LiveKit worker in hot-reload development mode:
```bash
uv run python -m app.agent dev
```

### Run in Console Mode (Interactive Test)
```bash
uv run python -m app.agent console
```

### Run Unit Tests
```bash
uv run pytest -v
```

### Run Linter & Formatter Checks
```bash
uvx ruff check .
uvx ruff format --check .
```

---

## 11. Core LiveKit Architecture & Execution Flow

```text
AgentServer  (Top-level worker process manager listening for job dispatches)
    ↓
JobContext   (Connection to a specific LiveKit room when a participant joins)
    ↓
AgentSession (Orchestrates real-time audio pipeline: STT -> LLM -> TTS + VAD)
    ↓
Agent        (Encapsulates persona instructions and conversational behavior)
    ↓
STT / LLM / TTS (Pluggable components: Groq Whisper, OpenRouter, TemporaryStubTTS)
```

1. **`AgentServer`:** Starts the LiveKit worker, registers the `@server.rtc_session` entrypoint callback, and negotiates jobs from the LiveKit server.
2. **`JobContext`:** Provides access to the room instance (`ctx.room`), job details, and connection handling (`await ctx.connect()`).
3. **`AgentSession`:** Glues audio/text I/O, speech detection (Silero VAD), and the STT-LLM-TTS pipeline.
4. **`Agent`:** Encapsulates the assistant persona instructions:
   > *"You are a helpful voice assistant. Understand Hindi, Hinglish, and English. Respond naturally and conversationally."*
5. **`session.start(agent, room)`:** Attaches the voice pipeline to the room audio streams.
6. **`cli.run_app(server)`:** LiveKit CLI harness managing command arguments (`dev`, `start`, `console`).

---

## 12. What Has NOT Been Implemented Yet (Deferred to Later Checkpoints)

To adhere to incremental checkpoint development, the following features are intentionally out of scope for Checkpoint 1:
- **AI Dost & AI Sathi Dual Personas:** Personality prompt specializations and distinct roles.
- **Two-Bot Turn Routing:** Determining which bot speaks or arbitrating dual-assistant conversations.
- **Conversation Memory:** Short-term and long-term dialogue history and persistence.
- **Speaker-Specific Context:** Tracking individual user profiles, names, or speech turns.
- **Interruption Orchestration:** Custom barge-in arbitration policies beyond standard VAD.
- **Local/Open-Source Hindi TTS:** Integration of a local neural TTS model (e.g. Kokoro, XTTS, Bark) for Hindi synthesis (Checkpoint 2).
- **Frontend Web / Mobile App:** LiveKit client interface for end users.
- **Database / Vector Store / RAG:** External document search or vector storage.
- **Function Calling / Tools:** External API tools (weather, time, web search).
- **Docker & Deployment Infrastructure:** Containerization and production orchestration.
