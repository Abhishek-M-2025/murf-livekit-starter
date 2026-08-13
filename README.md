# Voice Agent Starter — Powered by Murf Falcon

Build a production voice AI agent in 5 minutes. Powered by the fastest TTS on the market - swap the system prompt to build anything from customer support to language tutors.

---

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Murf Falcon](https://img.shields.io/badge/TTS-Murf%20Falcon-6366F1)](https://murf.ai/api/docs/text-to-speech/streaming) [![LiveKit](https://img.shields.io/badge/Transport-LiveKit-002cf2)](https://docs.livekit.io) [![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript\&logoColor=white)](https://www.typescriptlang.org/) [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python\&logoColor=white)](https://www.python.org/)

---

## Why Murf Falcon

* **55ms model latency** - fastest production TTS
* **130ms time-to-first-audio** across 10+ global regions
* **$0.01/1000 characters** - up to 10x cheaper than alternatives
* **150+ voices** across 35+ languages
* **99.38% pronunciation accuracy**

---

## Architecture

```mermaid
flowchart LR
    A[🎙️ User speaks] -->|audio| B[Deepgram STT]
    B -->|text| C[LLM]
    C -->|response text| D[Murf Falcon TTS]
    D -->|audio| E[LiveKit]
    E -->|stream| F[🔊 User hears]

    style A fill:#444441,stroke:#888780,color:#fff
    style B fill:#185FA5,stroke:#85B7EB,color:#fff
    style C fill:#534AB7,stroke:#AFA9EC,color:#fff
    style D fill:#0F6E56,stroke:#5DCAA5,color:#fff
    style E fill:#D85A30,stroke:#F0997B,color:#fff
    style F fill:#444441,stroke:#888780,color:#fff
```

---

## UI Preview: 👇

<img width="1916" height="918" alt="Image" src="https://github.com/user-attachments/assets/f17f871f-d1ec-4ee3-b505-9f46d6d13a9f" />

---

## Quickstart

### Prerequisites

* **Python** 3.10+
* **[uv](https://docs.astral.sh/uv/)** - fast Python package manager

  ```bash
  # macOS/Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
* **Node.js** 18+
* **pnpm** — fast Node package manager

  ```bash
  npm install -g pnpm
  ```
* A [LiveKit](https://cloud.livekit.io/) project (free tier available)

### Step 1: Clone the repo

```bash
git clone https://github.com/murf-ai/murf-livekit-starter.git
cd murf-livekit-starter
```

### Step 2: Set up environment variables

Create `.env.local` in both `backend/` and `frontend/` (copy from `.env.example` in each). You need:

| Variable                               | Where to get it                                        | Required |
| -------------------------------------- | ------------------------------------------------------ | -------- |
| `LIVEKIT_URL`                          | LiveKit Cloud dashboard                                | Yes      |
| `LIVEKIT_API_KEY`                      | LiveKit Cloud dashboard                                | Yes      |
| `LIVEKIT_API_SECRET`                   | LiveKit Cloud dashboard                                | Yes      |
| `MURF_API_KEY`                         | [murf.ai/api/dashboard](https://murf.ai/api/dashboard) | Yes      |
| `DEEPGRAM_API_KEY`                     | [deepgram.com](https://deepgram.com)                   | Yes      |
| `GOOGLE_API_KEY` (or `OPENAI_API_KEY`) | Depends on LLM choice                                  | Yes      |

### Step 3: Install backend dependencies

```bash
cd backend
uv sync
uv run python src/agent.py download-files
```

### Step 4: Install frontend dependencies

```bash
cd frontend
pnpm install
```

### Step 5: Run it

**Option A - All-in-one (from repo root):**

```bash
# macOS/Linux
chmod +x start_app.sh
./start_app.sh

# Windows (PowerShell)
.\start_app.ps1
```

**Option B - Separate terminals:**

```bash
# Terminal 1 — LiveKit Server
livekit-server --dev

# Terminal 2 — Backend agent
cd backend && uv run python src/agent.py dev

# Terminal 3 — Frontend
cd frontend && pnpm dev
```

Then open **http://localhost:3000** in your browser.

You should now see the voice agent UI. Click **Start talking**, allow microphone access, and speak — the agent will respond with Murf Falcon TTS. Ensure your backend and (if using Option B) LiveKit server are running.

---

## Deploy

Want to deploy this beyond localhost? You'll need to deploy **two services**: the backend agent and the frontend. Both must use the same LiveKit project.

> This is a two-service app — the backend agent and the frontend UI deploy separately. You'll need both running and connected to the same LiveKit project.

### Backend (Python agent) — Deploy to Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/tIVCF1?referralCode=cNjn2P&utm_medium=integration&utm_source=template&utm_campaign=generic)

Set these environment variables in Railway:

* `MURF_API_KEY`
* `DEEPGRAM_API_KEY`
* `GOOGLE_API_KEY` or `OPENAI_API_KEY`
* `LIVEKIT_URL`
* `LIVEKIT_API_KEY`
* `LIVEKIT_API_SECRET`

The backend runs as a long-lived Python process that connects to LiveKit as an agent. Railway handles this well.

### Frontend (Next.js) — Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/murf-ai/murf-livekit-starter&root-directory=frontend&env=LIVEKIT_URL,LIVEKIT_API_KEY,LIVEKIT_API_SECRET&project-name=murf-voice-agent&repository-name=murf-voice-agent)

Set these environment variables in Vercel:

* `LIVEKIT_URL`
* `LIVEKIT_API_KEY`
* `LIVEKIT_API_SECRET`
* `AGENT_NAME` (optional — for explicit agent dispatch)

The frontend is a standard Next.js app. Point it at the same LiveKit instance your backend agent is connected to.

### Connecting them

The frontend and backend don't call each other directly — they both connect to **LiveKit**, which handles the real-time audio transport.

1. Use the **same** `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` on both Railway and Vercel
2. Set `AGENT_NAME=my-agent` on Vercel — this matches the `agent_name="my-agent"` registered in `backend/src/agent.py`
3. Verify: Railway logs should show the agent connected to LiveKit. Open your Vercel URL, click **Start talking** — the agent should respond

If the agent doesn't connect, double-check that both services point to the same LiveKit project and that the backend is running (check Railway logs).

---

## Change the Use Case

The default system prompt makes this a **customer support agent**. You can change the agent’s behavior by editing the prompt.

**Where the prompt lives:** `backend/src/agent.py`- the `SYSTEM_PROMPT` constant (near the top of the file, after the imports). Change that string to change what your voice agent does.

### Example prompts (copy-paste)

**Customer Support (default):**

```text
You are a friendly and efficient customer support agent for a tech company. Help users with account issues, billing questions, and product troubleshooting. Be concise, empathetic, and solution-oriented. If you don't know something, say so honestly and offer to escalate.
```

**Language Tutor:**

```text
You are a patient and encouraging language tutor helping the user practice conversational Spanish. Speak primarily in Spanish but switch to English to explain grammar or vocabulary when needed. Correct mistakes gently and suggest better phrasing. Keep conversations natural and fun.
```

**AI Receptionist:**

```text
You are a professional receptionist for a medical clinic. Help callers schedule appointments, answer questions about office hours and services, and take messages for doctors. Be warm but efficient. Ask for the caller's name and reason for calling upfront.
```

See the Configuration section below for voice, STT, and LLM options.

---

## Configuration

### Murf voice

Edit the `tts=murf.TTS(...)` call in `backend/src/agent.py`. Set the `voice` argument to any Murf voice ID. Examples:

* `en-US-natalie` — US English (female)
* `en-UK-ruby` — UK English (female)
* `en-US-miles` — US English (male)
* `en-US-matthew` — US English (male, default in this starter)

Browse all voices: [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library).

### STT provider

STT is configured in `backend/src/agent.py` in the `AgentSession(stt=...)` call. The default is Deepgram (`deepgram.STT(model="nova-3")`). You can swap to another LiveKit-compatible STT plugin if needed.

### LLM (Gemini vs OpenAI)

* **Gemini (default):** Set `GOOGLE_API_KEY` and use `llm=google.LLM(model="gemini-2.5-flash")` in `agent.py`.
* **OpenAI:** Set `OPENAI_API_KEY`, add the OpenAI plugin, and use the corresponding `llm=openai.LLM(...)` in `agent.py`.

### Audio format

Murf Falcon and LiveKit handle audio format internally. For advanced options, see [Murf API docs](https://murf.ai/api/docs) and [LiveKit docs](https://docs.livekit.io).

---

## Project Structure

```text
murf-livekit-starter/
├── backend/                 # Python voice agent (LiveKit Agents + Murf Falcon)
│   ├── src/
│   │   └── agent.py         # Agent entrypoint, pipeline (STT/LLM/TTS), system prompt
│   ├── tests/               # Agent tests
│   ├── .env.example         # Backend env template
│   ├── pyproject.toml       # Python deps (uv)
│   └── railway.toml         # Railway deploy config
├── frontend/                # Next.js UI for voice sessions
│   ├── app/
│   │   ├── page.tsx         # Main page
│   │   └── api/token/       # LiveKit token endpoint (dev)
│   ├── components/          # UI (agents-ui, app config, theme)
│   ├── app-config.ts        # Branding, title, button text, accent
│   ├── .env.example         # Frontend env template
│   └── package.json         # Node deps (pnpm)
├── start_app.sh             # Start LiveKit + backend + frontend (macOS/Linux)
├── start_app.ps1            # Start LiveKit + backend + frontend (Windows)
├── README.md                # This file
```

For deeper documentation on each part, see:

* [Backend Documentation](./backend/README.md) — agent pipeline, voice/LLM/STT configuration, testing, deployment
* [Frontend Documentation](./frontend/README.md) — UI customization, visualizers, theming, component architecture

---

## Day 5: Nearest PHC / Government Health Facility Lookup

As part of the Murf AI "10 Days of Voice Agents – #VoiceForBharat" challenge (Health Access track), Day 5 adds a verified government health facility lookup tool.

### Features

* **Tool Added:** `find_nearest_health_facility(location_or_district)` is registered as a function tool.

* **Persistent Memory Integration:** If the user's district or location is already stored in their profile facts from Day 4, the agent automatically reuses it. Otherwise, it politely prompts the user for their location.

* **Data Source:**

  * **Live API:** Connects to the official `data.gov.in` database using the `DATA_GOV_IN_API_KEY` (default resource: `9ef84268-d588-465a-a308-a864a43d0070`).
  * **Local/Static Fallback:** If the live API is not configured or fails, the agent falls back to a high-fidelity local dataset (`health_facilities.json`) containing real, verified public health facilities across **20 major Indian districts** representing 20 different states and UTs.

  **20 States/UTs Covered:**

  1. Andhra Pradesh
  2. Assam
  3. Bihar
  4. Chhattisgarh
  5. Gujarat
  6. Haryana
  7. Himachal Pradesh
  8. Jharkhand
  9. Karnataka
  10. Kerala
  11. Madhya Pradesh
  12. Maharashtra
  13. Odisha
  14. Punjab
  15. Rajasthan
  16. Tamil Nadu
  17. Telangana
  18. Uttar Pradesh
  19. Uttarakhand
  20. West Bengal

* **Data Freshness:** The voice response states whether the information is retrieved from "live government data" or the "local fallback dataset".

* **Failure/No-Result Handling:** If both the API and the local database have no record of the location or fail, the agent says: *"I’m unable to access the health facility data right now, so I don’t want to give you an unverified location. Please try again later."* The agent never hallucinates facility names.

### Environment Variables

To enable live API lookup, add the following variables to `backend/.env.local`:

```env
DATA_GOV_IN_API_KEY=your_data_gov_in_api_key_here
DATA_GOV_IN_RESOURCE_ID=9ef84268-d588-465a-a308-a864a43d0070
```

### Running and Testing

1. Start the LiveKit agent:

   ```bash
   cd backend
   uv run python src/agent.py dev
   ```

2. Speak to the agent using the browser UI or console, and ask:

   * *"Mere nearest government health centre kaunsa hai?"*
   * *"Mere district mein nearest PHC kahan hai?"*

3. Run the automated tests verifying this behavior:

   ```bash
   uv run pytest
   ```

---

## Day 6: Outbound SIP Calling

Day 6 adds **outbound SIP calling**, allowing the voice agent to initiate phone calls and communicate with users through a SIP/telephony connection.

### Features

* The agent can initiate outbound SIP calls.
* Voice conversations can use the same STT → LLM → Murf Falcon TTS pipeline.
* This extends the Health Access agent from browser-based conversations to phone-based interactions.

### Run Outbound Call

From the `backend` directory, run:

```bash
uv run python src/outbound_call.py
```

This starts the outbound calling flow configured for the project.

---

## Day 7: Human Support Escalation

Day 7 adds a **human-support escalation flow** for cases where the voice agent cannot confidently resolve the user's request.

### Features

* The agent can identify conversations that require human assistance.
* It can politely inform the user that the request needs to be escalated.
* This provides a safe fallback instead of guessing or providing unreliable information.

---

## Day 8: Health Access Dashboard

Day 8 adds a dedicated **frontend dashboard** for the Health Access voice agent.

### Features

* Provides a central dashboard for the voice agent.
* Displays call/session activity and status.
* Shows successful and failed call outcomes.
* Makes the Health Access agent easier to monitor and demonstrate.

---

## Links

* [Murf API Docs](https://murf.ai/api/docs)
* [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library)
* [LiveKit Docs](https://docs.livekit.io)
* [Deepgram Docs](https://developers.deepgram.com)
* [Murf Falcon Benchmarks](https://murf.ai/falcon/benchmarks)
* [TTS Latency Benchmarker](https://github.com/sahilsgupta/tts-latency-benchmarker) — run your own p50/p95 tests across providers
* [Murf Discord](https://discord.gg/FbKAy96Sz7)
* [Murf Startup Incubator](https://murf.ai/api) — 50M free characters for startups

---

## License

MIT
