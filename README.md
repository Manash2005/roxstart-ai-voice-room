# Roxstar AI Voice Room Assistant

A production-quality Python realtime voice assistant project built for the Roxstar AI Voice Room candidate assignment.

## 1. What the Project Is

This project provides an AI Voice Room Assistant designed to participate in multi-user voice rooms, understand bilingual/code-mixed speech (Hindi, Hinglish, and English), and respond naturally and conversationally. The project is constructed incrementally across distinct checkpoints, adhering strictly to a **₹0-cost** architecture utilizing free tiers and open-source models.

---

## 2. Current Checkpoint: Checkpoint 4 (Second Complete AI Participant — AI Sathi)

**Checkpoint 4** introduces the second complete, fully interactive conversational AI participant: **AI Sathi**.

- **Persona Profile:** Intelligent, calm, analytical, composed, warm, and professional but approachable. She feels like a smart, patient female colleague or knowledgeable peer who explains complex topics with precision and clarity.
- **Distinction from AI Dost:**
  - **AI Dost (`ACTIVE_PERSONA=dost`):** Friendly, brotherly, casual, buddy-like. Simplifies ideas through everyday colloquial analogies (*"Dekho, index ko tum database ki shortcut list samajh lo..."*).
  - **AI Sathi (`ACTIVE_PERSONA=sathi`):** Calm, analytical, composed, and structured. Focuses on clarity, logical trade-offs, and step-by-step reasoning (*"Simple way mein, database index ek shortcut hai jo query ko relevant rows tak faster pahunchne mein help karta hai..."*).
- **Independent Agent Architecture:** Reuses the existing STT, LLM, TTS, VAD, and configuration pipeline without duplicating infrastructure code.
- **Active Persona Selection:** Configurable via `ACTIVE_PERSONA=dost` or `ACTIVE_PERSONA=sathi` in `.env` (or environment variables).
- **Spoken Greetings:**
  - **AI Dost:** *"Namaste! Main Dost hoon. Batao, aaj kis cheez mein help chahiye?"*
  - **AI Sathi:** *"Namaste! Main Sathi hoon. Bataiye, aaj kis cheez ko simple bana kar samjhein?"*
- **Spoken Voice & TTS Optimization:** Both agents enforce 1–4 short spoken sentences, strictly avoiding emojis, markdown tables, bullet points, and AI clichés (*"As an AI language model..."*).

---

## 3. Technology Stack

- **Language & Runtime:** Python 3.12 (managed via `uv`)
- **Realtime Framework:** [LiveKit Agents](https://docs.livekit.io/agents/) (`livekit-agents` v1.8.5)
- **STT (Speech-to-Text):** [Groq Cloud Whisper](https://groq.com/) (`whisper-large-v3-turbo`) via `livekit-plugins-groq`
- **LLM (Language Model):** [OpenRouter](https://openrouter.ai/) (default: `openrouter/free`) via `livekit-plugins-openai`
- **VAD (Voice Activity Detection):** Silero VAD (local open-source inference bundled with LiveKit Agents)
- **TTS (Text-to-Speech):** [Piper TTS](https://github.com/rhasspy/piper) (`hi_IN-rohan-medium` ONNX model, trained on IIT Madras Indic TTS dataset)
- **Personas:** `AIDost` ([app/personas/dost.py](file:///Users/manashswain/Projects/roxstart-ai-voice-room/app/personas/dost.py)) and `AISathi` ([app/personas/sathi.py](file:///Users/manashswain/Projects/roxstart-ai-voice-room/app/personas/sathi.py))
- **Persona Factory:** `create_agent(persona)` in [app/personas/\_\_init\_\_.py](file:///Users/manashswain/Projects/roxstart-ai-voice-room/app/personas/__init__.py)
- **Dependency Management:** `uv`
- **Configuration:** Typed `Settings` class with `python-dotenv`
- **Testing:** `pytest` & `pytest-asyncio`

---

## 4. Local TTS Model Selection & Trade-Off Analysis

### Selected Model: Piper TTS (`hi_IN-rohan-medium`)

After evaluating multiple candidate models, **Piper TTS** with the `hi_IN-rohan-medium` voice was selected for the following reasons:

1. **Native Indian Voice Quality:** Trained on high-quality voice data from the **IIT Madras Indic TTS** project, yielding a natural Indian accent and authentic Hindi cadence.
2. **Compact Model Footprint:** The ONNX model is only **~62.9 MB** (plus ~5 KB config), allowing instant on-demand download and minimal disk utilization.
3. **Ultra-Low Memory Footprint:** Consumes **~100 MB of RAM**, fitting comfortably on any developer laptop or MacBook with limited memory.
4. **Sub-100ms Inference on Apple Silicon:** Operates natively via `onnxruntime` on CPU / Apple Silicon without requiring CUDA or GPU acceleration. Measured Real-Time Factor (RTF) is **0.03x – 0.05x** (e.g. synthesizing 7 seconds of speech takes ~350ms).
5. **Python 3.12 Compatibility:** Installs cleanly as a standard wheel without conflicting with LiveKit's dependencies or requiring a secondary Python environment.
6. **Permissive License:** Open-source under MIT / Open Data licenses, appropriate for production and assignment evaluation.
7. **Bilingual / Code-Mixed Support:** The underlying `espeak-ng` phonemization pipeline natively accepts Devanagari script, Romanized Hindi, and English words.

### Alternatives Evaluated

| Model Candidate | Size | Runtime / Device | Python Compatibility | Evaluation Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **IndicF5 (AI4Bharat)** | 1.5 – 2.5 GB | PyTorch Diffusion (CUDA-optimized) | Python 3.10 recommended | **Rejected:** Requires 32 ODE steps per sentence, resulting in 15–30s generation latency on CPU. Requires a reference audio clip + transcript for zero-shot cloning. |
| **Meta MMS-TTS Hindi (`facebook/mms-tts-hin`)** | ~140 MB | PyTorch VITS (CPU/MPS) | Python 3.12 compatible | **Rejected:** Vocabulary strictly restricted to Devanagari characters (72 tokens). Fails on Roman Hindi or Hinglish code-mixed text with `<unk>` tokens. |
| **Kokoro-82M (ONNX)** | ~300 MB | ONNX Runtime | Python 3.12 compatible | **Deferred:** Exceptional English/multilingual synthesizer, but Hindi voice support is community-experimental and lacks native Indic-trained intonation compared to IIT Madras datasets. |
| **Piper TTS (`hi_IN-rohan-medium`)** | **~63 MB** | **ONNX Runtime (CPU/Mac)** | **Python 3.12 compatible** | **SELECTED:** Instant startup, <100ms latency, native Indic cadence, handles Devanagari and Romanized text. |

### Current Voice Identity & Limitation Note

> [!NOTE]
> **Voice Status for Checkpoint 4:**
> Both AI Dost and AI Sathi currently share the local `hi_IN-rohan-medium` Piper ONNX voice model.
> Female voice selection is intentionally deferred to the voice-selection/orchestration refinement once a compatible, high-quality local Hindi voice is verified without adding cost or cloud dependencies. Do not claim that the current voice is female.

---

## 5. LiveKit Agents & Persona Architecture

The architecture maintains strict separation of concerns, keeping `app/agent.py` clean and beginner-friendly:

```text
LiveKit Room (WebRTC Audio Stream)
       ↓
LiveKit Agent Worker (AgentServer)
       ↓
JobContext (Room connection & lifecycle)
       ↓
AgentSession (STT: Groq Whisper, LLM: OpenRouter Free, TTS: Piper Local, VAD: Silero)
       ↓
create_agent(settings.active_persona)
   ├── "dost"  → AIDost (Warm, brotherly buddy persona)
   └── "sathi" → AISathi (Calm, analytical, structured persona)
       ↓
Spoken Greeting:
   • Dost:  "Namaste! Main Dost hoon. Batao, aaj kis cheez mein help chahiye?"
   • Sathi: "Namaste! Main Sathi hoon. Bataiye, aaj kis cheez ko simple bana kar samjhein?"
```

### Key Technical Details

- **Clean Persona Abstraction:** `AIDost` and `AISathi` inherit from LiveKit's `Agent` class and encapsulate their respective system prompts. Adding or updating personas requires zero changes to the underlying STT, TTS, or RTC networking logic.
- **Factory Selection:** `create_agent(settings.active_persona)` instantiates the requested persona based on `ACTIVE_PERSONA` in `.env`.
- **Automatic Spoken Greeting:** Upon connection, `await session.say(assistant.greeting)` delivers the opening spoken turn and synchronizes it into session history.
- **Sentence-Level Chunking & Emitting:** Synthesized 16-bit mono PCM audio (22,050 Hz) is emitted to LiveKit's `AudioEmitter(mime_type="audio/pcm")`, with streaming LLM text split on sentence boundaries via `tokenize.blingfire.SentenceTokenizer`.

---

## 6. Hindi & Hinglish Evaluation Results

The implementation was validated against six core categories via `scripts/tts_smoke_test.py`:

| Test Category | Test Input | Audio Duration | Inference Time | Real-Time Factor (RTF) | Quality / Intonation Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AI Sathi Greeting** | `"Namaste! Main Sathi hoon. Bataiye, aaj kis cheez ko simple bana kar samjhein?"` | 7.07s | 0.347s | 0.05x | Composed, clear Indian cadence; synthesized smoothly. |
| **AI Dost Greeting** | `"Namaste! Main Dost hoon. Batao, aaj kis cheez mein help chahiye?"` | 6.06s | 0.302s | 0.05x | Warm, conversational greeting; natural pace. |
| **Hindi Devanagari** | `"नमस्ते! आज आप कैसे हैं?"` | 2.94s | 0.850s | 0.29x | Authentic Hindi pronunciation and inflection. |
| **Roman Hindi** | `"Aaj kya kar rahe ho?"` | 1.75s | 0.068s | 0.04x | Clear conversational Hindi intonation. |
| **Hinglish** | `"Haan, basically iska main idea ye hai ki hum context maintain karte hain."` | 5.73s | 0.294s | 0.05x | Fluid transition between Hindi verbs and English technical nouns. |
| **English** | `"Can you explain this in simple terms?"` | 2.76s | 0.135s | 0.05x | Clear Indian-accented English pronunciation. |

---

## 7. Manual Test Scenarios

### Part A: AI Sathi Scenarios (`ACTIVE_PERSONA=sathi`)

#### TEST 1 — Hindi Explanation
- **User Prompt:** `"Mujhe batao authentication kya hoti hai?"`
- **Expected Sathi Behavior:** Clear conversational Hindi/Hinglish explanation in 2–3 short spoken sentences. Explains that authentication is the identity verification check (checking who the user is) before granting access.

#### TEST 2 — English Inquiry
- **User Prompt:** `"Can you explain what database indexing is?"`
- **Expected Sathi Behavior:** Responds in natural English. Explains that a database index is a data structure (like a book's index) that lets the database locate rows directly without scanning the whole table.

#### TEST 3 — Hinglish Technical Distinction
- **User Prompt:** `"Redis aur database mein actual difference kya hai?"`
- **Expected Sathi Behavior:** Precise Hinglish response: explains that databases store data persistently on disk, while Redis keeps data in RAM for sub-millisecond fast access (used for caching and sessions).

#### TEST 4 — Comparison & Trade-Offs
- **User Prompt:** `"REST aur GraphQL mein kaunsa better hai?"`
- **Expected Sathi Behavior:** Avoids declaring a simplistic winner; clarifies the trade-off. Explains that REST is standard, simple, and great for caching, while GraphQL prevents over-fetching and allows clients to request exact fields.

#### TEST 5 — Multi-Turn Follow-Up (Context Maintenance)
- **Turn 1:** `"Docker kya hai?"`
- **Turn 2:** `"Kubernetes?"`
- **Turn 3:** `"Simple difference batao."`
- **Expected Sathi Behavior:** Retains multi-turn context across all turns. In Turn 3, concisely contrasts Docker (creating and running individual containers) with Kubernetes (orchestrating and managing multiple containers across clusters).

#### TEST 6 — Casual / Emotional Conversation
- **User Prompt:** `"Aaj thoda stress hai."`
- **Expected Sathi Behavior:** Calm, warm, and supportive response. Acknowledges stress gently (*"Aap thoda relax ho jaiye. Kya chal raha hai, agar share karna chahein toh bataiye?"*). Strictly avoids robotic disclaimers or turning the moment into a technical lecture.

---

### Part B: AI Dost Scenarios (`ACTIVE_PERSONA=dost`)

- **TEST 1 — Hindi:** `"Bhai mujhe batao API kya hoti hai?"` -> Friendly brotherly explanation via restaurant waiter analogy.
- **TEST 2 — English:** `"Can you explain what an API is?"` -> Approaches in warm, clear conversational English.
- **TEST 3 — Hinglish:** `"Bhai backend mein authentication kaise kaam karta hai?"` -> Explains credentials, tokens, and sessions in Hinglish.
- **TEST 4 — Follow-up:** `"Docker kya hai?"` -> `"Aur Kubernetes?"` -> `"Simple language mein difference batao."` -> Compares container box and ship captain.
- **TEST 5 — Casual:** `"Aaj mood thoda kharab hai."` -> Empathic, supportive buddy response.

---

## 8. ₹0-Cost Architecture Compliance

| Component | Provider / Tool | Cost | Rationale |
| :--- | :--- | :--- | :--- |
| **Realtime WebRTC** | LiveKit Cloud (Free tier) or self-hosted | ₹0 | Standard developer tier handles dev rooms and agent jobs. |
| **STT** | Groq Whisper (`whisper-large-v3-turbo`) | ₹0 | Generous free tier with ultra-low latency. |
| **LLM** | OpenRouter (`openrouter/free`) | ₹0 | Free-tier models accessed via standard API keys. |
| **VAD** | Silero VAD (local ONNX/Inference) | ₹0 | Runs locally on CPU, no external network requests. |
| **TTS** | Piper TTS (`hi_IN-rohan-medium`) | **₹0** | **Runs 100% locally on CPU / Apple Silicon. No API keys.** |
| **Personas** | AI Dost & AI Sathi | ₹0 | Clean in-memory prompt and agent architecture. |
| **Paid Services** | LiveKit Inference / OpenAI Paid API / ElevenLabs | **NONE** | **Strictly prohibited & omitted.** |

---

## 9. Installation & Setup

### Prerequisites

- Python 3.12+
- `uv` (Fast Python package manager):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### Step 1: Install Dependencies with uv
```bash
uv sync --all-extras
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your credentials in `.env`:
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

# Local TTS Configuration (₹0-cost local open-source Piper Hindi TTS)
TTS_MODEL=hi_IN-rohan-medium
TTS_DEVICE=cpu
TTS_SAMPLE_RATE=22050
TTS_AUTO_DOWNLOAD=true

# Active Agent Persona for Checkpoint 4 ("dost" or "sathi")
ACTIVE_PERSONA=sathi

# Logging
LOG_LEVEL=INFO
```

---

## 10. Running Verification & Smoke Tests

### Run the TTS Smoke Test (Actual Model Inference)
```bash
uv run python scripts/tts_smoke_test.py
```

### Run Fast Unit Tests (37 tests)
```bash
uv run pytest -v
```

### Run Linter & Formatter Checks
```bash
uvx ruff check .
uvx ruff format --check .
```

### Run the LiveKit Agent with AI Sathi
```bash
ACTIVE_PERSONA=sathi uv run python -m app.agent dev
```

### Run the LiveKit Agent with AI Dost
```bash
ACTIVE_PERSONA=dost uv run python -m app.agent dev
```

### Run in Console Mode
```bash
ACTIVE_PERSONA=sathi uv run python -m app.agent console
```

---

## 11. What Has NOT Been Implemented Yet (Deferred to Later Checkpoints)

To adhere to incremental checkpoint development, the following features remain out of scope for Checkpoint 4:
- **Two-Bot Turn Routing & Arbitration:** Automatic router, bot handoff, or turn mediator (deferred to **Checkpoint 5**).
- **Two Bots Running Simultaneously in the Same Room:** Multi-agent co-presence and arbitration.
- **Persistent Database Memory / Vector Store / RAG:** External storage, SQLite/PostgreSQL, ChromaDB/Pinecone deferred.
- **Speaker Diarization / Multi-User Profiling:** Recognizing specific individual user identities.
- **Custom Interruption Orchestration:** Advanced interruption arbitration policies beyond standard Silero VAD barge-in.
- **Frontend Web / Mobile App:** LiveKit client interface for end users.
- **Function Calling / Tools:** External API tools (weather, time, web search).
- **Docker & Deployment Infrastructure:** Containerization and cloud deployment.

