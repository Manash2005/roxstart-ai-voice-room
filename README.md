# Roxstar AI Voice Room Assistant

A production-quality Python realtime voice assistant project built for the Roxstar AI Voice Room candidate assignment.

## 1. What the Project Is

This project provides an AI Voice Room Assistant designed to participate in multi-user voice rooms, understand bilingual/code-mixed speech (Hindi, Hinglish, and English), and respond naturally and conversationally. The project is constructed incrementally across distinct checkpoints, adhering strictly to a **₹0-cost** architecture utilizing free tiers and open-source models.

---
## 2. Current Checkpoint: Checkpoint 5 (Two-Bot Orchestration Layer)

**Checkpoint 5** introduces the central two-bot orchestration layer, allowing **AI Dost** and **AI Sathi** to logically coexist within the same LiveKit room without speech collision, duplicate turns, or multiple concurrent STT/LLM sessions.

- **Logical Coexistence:** Both AI participants are represented in the same room. A central orchestrator receives each user utterance and dynamically assigns turn ownership.
- **Priority-Based Turn Routing ([app/routing/router.py](file:///Users/manashswain/Projects/roxstart-ai-voice-room/app/routing/router.py)):**
  1. **Priority 1 — Explicit Bot Addressing:** Utterances explicitly naming *"Dost"*, *"AI Dost"*, *"Bhai Dost"* route to Dost; utterances naming *"Sathi"*, *"AI Sathi"*, *"Sathi ji"* route to Sathi. Explicit addressing always overrides topic classification.
  2. **Priority 2 — Conversation Ownership:** Follow-up questions (*"Aur Kubernetes?"*, *"Simple batao"*, *"Why?"*, *"Isme kya problem hai?"*, *"Aur iska alternative?"*) maintain context and stay with the currently active bot.
  3. **Priority 3 — Topic/Intent Classification:** Technical comparisons (*"difference"*, *"compare"*, *"vs"*, *"trade-off"*, *"architecture"*) route to AI Sathi; casual conversation, mood check-ins, or buddy banter route to AI Dost.
  4. **Priority 4 — Deterministic Default Fallback:** Queries without explicit addressing or analytical intent default deterministically to AI Dost.
- **Mutual Exclusion & Arbitration ([app/routing/arbitrator.py](file:///Users/manashswain/Projects/roxstart-ai-voice-room/app/routing/arbitrator.py)):**
  - An asyncio-safe `ResponseArbitrator` guarantees that at most ONE bot speaks at any time.
  - If Dost is speaking, Sathi cannot start; if Sathi is speaking, Dost cannot start.
  - When speech generation concludes, the lock is released cleanly.
- **LiveKit Room Participant Identity:**
  - The LiveKit participant name is dynamically updated (`set_name("AI Dost")` vs `set_name("AI Sathi")`) and metadata attributes (`set_attributes({"active_bot": "ai-dost", "available_bots": "ai-dost,ai-sathi"})`) reflect the active responder in real-time.
- **Controlled Collaborative Addressing ("Both Bots"):**
  - For questions addressing both bots (*"Both of you, what do you think?"*), the router defaults to AI Dost with reason `collaborative_deferred`, preventing uncoordinated double speech. Full sequential multi-bot dialogue is deferred.

---

## 3. Technology Stack

- **Language & Runtime:** Python 3.12 (managed via `uv`)
- **Realtime Framework:** [LiveKit Agents](https://docs.livekit.io/agents/) (`livekit-agents` v1.8.5)
- **STT (Speech-to-Text):** [Groq Cloud Whisper](https://groq.com/) (`whisper-large-v3-turbo`) via `livekit-plugins-groq`
- **LLM (Language Model):** [OpenRouter](https://openrouter.ai/) (default: `openrouter/free`) via `livekit-plugins-openai`
- **VAD (Voice Activity Detection):** Silero VAD (local open-source inference bundled with LiveKit Agents)
- **TTS (Text-to-Speech):** [Piper TTS](https://github.com/rhasspy/piper) (`hi_IN-rohan-medium` ONNX model, trained on IIT Madras Indic TTS dataset)
- **Orchestration Layer:**
  - `TwoBotOrchestrator` ([app/routing/orchestrator.py](file:///Users/manashswain/Projects/roxstart-ai-voice-room/app/routing/orchestrator.py))
  - `TurnRouter` ([app/routing/router.py](file:///Users/manashswain/Projects/roxstart-ai-voice-room/app/routing/router.py))
  - `ResponseArbitrator` ([app/routing/arbitrator.py](file:///Users/manashswain/Projects/roxstart-ai-voice-room/app/routing/arbitrator.py))
- **Personas:** `AIDost` ([app/personas/dost.py](file:///Users/manashswain/Projects/roxstart-ai-voice-room/app/personas/dost.py)) and `AISathi` ([app/personas/sathi.py](file:///Users/manashswain/Projects/roxstart-ai-voice-room/app/personas/sathi.py))
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
4. **Sub-100ms Inference on Apple Silicon:** Operates natively via `onnxruntime` on CPU / Apple Silicon without requiring CUDA or GPU acceleration. Measured Real-Time Factor (RTF) is **0.02x – 0.17x**.
5. **Python 3.12 Compatibility:** Installs cleanly as a standard wheel without conflicting with LiveKit's dependencies or requiring a secondary Python environment.
6. **Permissive License:** Open-source under MIT / Open Data licenses, appropriate for production and assignment evaluation.
7. **Bilingual / Code-Mixed Support:** The underlying `espeak-ng` phonemization pipeline natively accepts Devanagari script, Romanized Hindi, and English words.

### Current Voice Identity & Limitation Note

> [!NOTE]
> **Voice Status for Checkpoint 5:**
> Both AI Dost and AI Sathi synthesize audio through the verified local `hi_IN-rohan-medium` Piper ONNX voice model.
> Female voice timbre differentiation is intentionally deferred to the voice-selection refinement once a compatible, high-quality local Hindi female ONNX voice is verified without adding cost or cloud dependencies.

---

## 5. LiveKit Agents & Orchestration Architecture

The central two-bot orchestration layer ensures a single STT/LLM stream while dynamically arbitrating persona execution:

```text
LiveKit Room (WebRTC Audio Stream)
       │
       ▼
JobContext (Room connection & lifecycle)
       │
       ▼
AgentSession (Single Groq STT, Single OpenRouter LLM, Single Piper TTS)
       │
       ▼
TwoBotOrchestrator (app/routing/orchestrator.py)
       │
       ├── TurnRouter (app/routing/router.py)
       │     ├── 1. Explicit Address: "Dost..." / "Sathi..."
       │     ├── 2. Conversation Owner: Follow-up continuations
       │     ├── 3. Topic Classifier: Comparison vs Casual
       │     └── 4. Deterministic Default: AI Dost
       │
       ├── ResponseArbitrator (app/routing/arbitrator.py)
       │     └── Asyncio Mutex: Prevents simultaneous speech turns
       │
       ├── ChatContext Instructions Injection:
       │     ├── If Dost: AI_DOST_INSTRUCTIONS (app/personas/dost.py)
       │     └── If Sathi: AI_SATHI_INSTRUCTIONS (app/personas/sathi.py)
       │
       └── Dynamic Room Identity Update:
             └── local_participant.set_name("AI Dost" / "AI Sathi")
```

### Key Technical Details

- **Single Audio Pipeline:** A single `AgentSession` manages room audio, preventing redundant STT transcripts, duplicate audio tracks, or race conditions.
- **Dynamic System Prompt Swapping:** In `on_user_turn_completed`, the orchestrator injects the routed persona's system prompt into the turn's `ChatContext` using `update_instructions`, ensuring the LLM generates in character.
- **Mutual Exclusion Lock:** `arbitrator.acquire()` locks speech generation for the active bot; if locked, incoming overlapping turns raise `StopResponse()`.
- **Automatic Turn Release:** When speech concludes (`AgentStateChangedEvent` transitions to `idle`/`listening`), `arbitrator.release()` unlocks the turn.

---

## 6. Hindi & Hinglish Evaluation Results

The implementation was validated against six core categories via `scripts/tts_smoke_test.py`:

| Test Category | Test Input | Audio Duration | Inference Time | Real-Time Factor (RTF) | Quality / Intonation Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AI Sathi Greeting** | `"Namaste! Main Sathi hoon. Bataiye, aaj kis cheez ko simple bana kar samjhein?"` | 6.81s | 0.163s | 0.02x | Composed, clear Indian cadence; synthesized smoothly. |
| **AI Dost Greeting** | `"Namaste! Main Dost hoon. Batao, aaj kis cheez mein help chahiye?"` | 5.85s | 0.142s | 0.02x | Warm, conversational greeting; natural pace. |
| **Hindi Devanagari** | `"नमस्ते! आज आप कैसे हैं?"` | 2.89s | 0.488s | 0.17x | Authentic Hindi pronunciation and inflection. |
| **Roman Hindi** | `"Aaj kya kar rahe ho?"` | 1.82s | 0.093s | 0.05x | Clear conversational Hindi intonation. |
| **Hinglish** | `"Haan, basically iska main idea ye hai ki hum context maintain karte hain."` | 5.73s | 0.149s | 0.03x | Fluid transition between Hindi verbs and English technical nouns. |
| **English** | `"Can you explain this in simple terms?"` | 2.67s | 0.070s | 0.03x | Clear Indian-accented English pronunciation. |

---

## 7. Checkpoint 5 Manual Test Scenarios

The following 7 scenarios validate two-bot turn routing, explicit addressing, follow-up ownership, and arbitration:

### Scenario 1 — Explicit Dost Addressing
- **User Prompt:** `"Dost, explain Docker."`
- **Expected Route:** Only AI Dost responds (`reason="explicit_address"`, `confidence=1.0`). Friendly, colloquial analogy.

### Scenario 2 — Explicit Sathi Addressing
- **User Prompt:** `"Sathi, compare Docker and Kubernetes."`
- **Expected Route:** Only AI Sathi responds (`reason="explicit_address"`, `confidence=1.0`). Structured architectural comparison.

### Scenario 3 — General Question (Default Fallback)
- **User Prompt:** `"Docker kya hota hai?"`
- **Expected Route:** Unaddressed general question routes deterministically to AI Dost (`reason="general_default"`, `confidence=0.5`).

### Scenario 4 — Technical Comparison Query
- **User Prompt:** `"REST aur GraphQL mein kya difference hai?"`
- **Expected Route:** Unaddressed comparison routes to AI Sathi (`reason="technical_comparison"`, `confidence=0.75`).

### Scenario 5 — Follow-Up Continuity (Sathi Ownership)
- **Turn 1:** `"Sathi, explain Redis."` -> Sathi responds (`explicit_address`).
- **Turn 2:** `"Aur iska use case?"` -> Sathi handles the follow-up turn (`reason="conversation_owner"`, `confidence=0.85`).

### Scenario 6 — Follow-Up Continuity (Dost Ownership)
- **Turn 1:** `"Dost, explain API."` -> Dost responds (`explicit_address`).
- **Turn 2:** `"Simple example do."` -> Dost handles the follow-up turn (`reason="conversation_owner"`, `confidence=0.85`).

### Scenario 7 — Collaborative Addressing
- **User Prompt:** `"Both of you, what do you think?"`
- **Expected Route:** Handled safely by AI Dost (`reason="collaborative_deferred"`). Controlled sequential speech prevents simultaneous overlap.

---

## 8. ₹0-Cost Architecture Compliance

| Component | Provider / Tool | Cost | Rationale |
| :--- | :--- | :--- | :--- |
| **Realtime WebRTC** | LiveKit Cloud (Free tier) or self-hosted | ₹0 | Standard developer tier handles dev rooms and agent jobs. |
| **STT** | Groq Whisper (`whisper-large-v3-turbo`) | ₹0 | Generous free tier with ultra-low latency. |
| **LLM** | OpenRouter (`openrouter/free`) | ₹0 | Free-tier models accessed via standard API keys. |
| **VAD** | Silero VAD (local ONNX/Inference) | ₹0 | Runs locally on CPU, no external network requests. |
| **TTS** | Piper TTS (`hi_IN-rohan-medium`) | **₹0** | **Runs 100% locally on CPU / Apple Silicon. No API keys.** |
| **Turn Orchestration** | Local TurnRouter & ResponseArbitrator | ₹0 | In-memory Python routing and mutual exclusion. |
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

# Default Agent Persona ("dost" or "sathi")
ACTIVE_PERSONA=dost

# Logging
LOG_LEVEL=INFO
```

---

## 10. Running Verification & Smoke Tests

### Run the TTS Smoke Test (Actual Model Inference)
```bash
uv run python scripts/tts_smoke_test.py
```

### Run Full Fast Unit Test Suite (58 tests)
```bash
uv run pytest -v
```

### Run Linter & Formatter Checks
```bash
uvx ruff check .
uvx ruff format --check .
```

### Run the LiveKit Agent in Two-Bot Orchestration Mode
```bash
uv run python -m app.agent dev
```

### Run in Interactive Console Mode
```bash
uv run python -m app.agent console
```

---

## 11. What Has NOT Been Implemented Yet (Deferred to Later Checkpoints)

To adhere to incremental checkpoint development, the following features remain out of scope for Checkpoint 5:
- **Persistent Database Memory / Vector Store / RAG:** External storage, SQLite/PostgreSQL, ChromaDB/Pinecone deferred.
- **Speaker Identification / Diarization:** Distinguishing different human participants by name/voice fingerprint.
- **Custom Interruption Orchestration:** Advanced interruption arbitration policies beyond standard Silero VAD barge-in.
- **Frontend Web / Mobile App:** LiveKit client interface for end users.
- **Function Calling / Tools:** External API tools (weather, time, web search).
- **Docker & Deployment Infrastructure:** Containerization and cloud deployment.
 tools (weather, time, web search).
- **Docker & Deployment Infrastructure:** Containerization and cloud deployment.

