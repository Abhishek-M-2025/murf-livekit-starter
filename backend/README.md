# Backend — Voice Agent with Murf Falcon TTS

The Python backend for the Voice Agent Starter. It runs a real-time voice AI pipeline using [LiveKit Agents](https://docs.livekit.io/agents), connecting Murf Falcon TTS, Deepgram STT, and Google Gemini into a single conversational agent.

## How It Works

```
User speaks → [Deepgram STT] → text → [Gemini LLM] → response → [Murf Falcon TTS] → audio → User hears
```

LiveKit handles the real-time audio transport. The agent connects to LiveKit as a participant, listens for user speech, and responds with synthesized audio.

## Setup

### 1. Install dependencies

```bash
cd backend
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env.local
```

Fill in your keys in `.env.local`:

| Variable             | Where to get it                                           |
| -------------------- | --------------------------------------------------------- |
| `LIVEKIT_URL`        | [LiveKit Cloud](https://cloud.livekit.io/) → Settings     |
| `LIVEKIT_API_KEY`    | [LiveKit Cloud](https://cloud.livekit.io/) → Settings     |
| `LIVEKIT_API_SECRET` | [LiveKit Cloud](https://cloud.livekit.io/) → Settings     |
| `MURF_API_KEY`       | [murf.ai/api/dashboard](https://murf.ai/api/dashboard)    |
| `DEEPGRAM_API_KEY`   | [deepgram.com](https://console.deepgram.com/)             |
| `GOOGLE_API_KEY`     | [aistudio.google.com](https://aistudio.google.com/apikey) |

For LiveKit Cloud users, you can auto-populate LiveKit credentials:

```bash
lk cloud auth
lk app env -w -d .env.local
```

### 3. Download models

```bash
uv run python src/agent.py download-files
```

This downloads Silero VAD and the LiveKit turn detector models.

### 4. Run the agent

```bash
# Development mode (auto-reload)
uv run python src/agent.py dev

# Or test directly in your terminal (no frontend needed)
uv run python src/agent.py console

# Production
uv run python src/agent.py start
```

## Configuration

All configuration lives in `src/agent.py`.

### System prompt

The `SYSTEM_PROMPT` constant at the top of `agent.py` controls what your agent does. Change it to build any voice-powered use case.

#### Example prompts

**Customer Support (default):**

```
You are a friendly and efficient customer support agent for a tech company. Help users with account issues, billing questions, and product troubleshooting. Be concise, empathetic, and solution-oriented. If you don't know something, say so honestly and offer to escalate.
```

**Language Tutor:**

```
You are a patient and encouraging language tutor helping the user practice conversational Spanish. Speak primarily in Spanish but switch to English to explain grammar or vocabulary when needed. Correct mistakes gently and suggest better phrasing. Keep conversations natural and fun.
```

**AI Receptionist:**

```
You are a professional receptionist for a medical clinic. Help callers schedule appointments, answer questions about office hours and services, and take messages for doctors. Be warm but efficient. Ask for the caller's name and reason for calling upfront.
```

**Interview Coach:**

```
You are an experienced interview coach. Conduct mock interviews with the user for software engineering roles. Ask one behavioral or technical question at a time, let the user answer fully, then give specific feedback on their response — what was strong, what could improve, and a suggested reframe. Keep the tone encouraging but honest.
```

**Sales Assistant:**

```
You are a knowledgeable sales assistant for an electronics store. Help customers find the right product by asking about their needs, budget, and preferences. Compare options clearly, highlight trade-offs, and make a recommendation. Never be pushy — focus on helping the customer make the best decision for them.
```

**Fitness Coach:**

```
You are an upbeat personal fitness coach. Help users plan workouts, suggest exercises for specific muscle groups, and answer questions about form and technique. Ask about their fitness level and any injuries before recommending exercises. Keep instructions clear and motivating.
```

**Storyteller / Bedtime Narrator:**

```
You are a creative storyteller who tells original bedtime stories for children aged 4–8. Ask the child (or parent) for a character name, a favorite animal, and a setting, then weave a short, calming story. Use vivid but simple language. End each story on a peaceful, sleepy note.
```

**Meeting Summarizer:**

```
You are a meeting assistant. The user will describe what happened in a meeting or read you their notes. Summarize the key decisions, action items (with owners if mentioned), and any open questions. Be concise and structured. Ask clarifying questions if something is ambiguous.
```

**Trivia Game Host:**

```
You are an enthusiastic trivia game host. Ask the user one trivia question at a time from a mix of categories — science, history, pop culture, geography, and sports. Wait for their answer, tell them if they're right or wrong, give a brief fun fact, then move to the next question. Keep score and announce it every 5 questions.
```

**Mental Health Check-in Companion:**

```
You are a gentle, non-clinical wellness companion. Help users talk through their day, reflect on how they're feeling, and practice simple grounding exercises like deep breathing or gratitude lists. You are not a therapist — if the user expresses serious distress or mentions self-harm, gently encourage them to reach out to a professional or crisis helpline.
```

### Voice

Set the `voice` argument in the `murf.TTS(...)` call:

```python
tts=murf.TTS(
    voice="en-US-matthew",    # Change this
    style="Conversation",
    tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
    text_pacing=True
)
```

Some voice options:

| Voice ID        | Description                |
| --------------- | -------------------------- |
| `en-US-matthew` | US English, male (default) |
| `en-US-natalie` | US English, female         |
| `en-UK-ruby`    | UK English, female         |
| `en-US-miles`   | US English, male           |

Browse all 150+ voices: [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library).

### STT (Speech-to-Text)

Default is Deepgram Nova-3. Change in the `AgentSession(stt=...)` call:

```python
stt=deepgram.STT(model="nova-3")
```

### LLM

Default is Google Gemini. To switch:

* **Gemini (default):** Set `GOOGLE_API_KEY` in `.env.local`
* **OpenAI:** Set `OPENAI_API_KEY`, install `livekit-agents[openai]`, and change the `llm=` argument

## Testing

The project includes an eval suite based on the LiveKit Agents [testing framework](https://docs.livekit.io/agents/build/testing/):

```bash
uv run pytest
```

Tests are in `tests/test_agent.py` and use LLM-as-judge evaluations to verify the agent behaves correctly (friendly greetings, grounding, refusing harmful requests).

To run tests in CI, you'll need to add `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` as repository secrets.

## Deployment

### Railway

Set these environment variables in Railway:

* `MURF_API_KEY`
* `DEEPGRAM_API_KEY`
* `GOOGLE_API_KEY`
* `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`

### Docker

A production-ready Dockerfile is included:

```bash
docker build -t murf-voice-agent .
docker run --env-file .env.local murf-voice-agent
```

## Project Structure

```
backend/
├── src/
│   └── agent.py          # Agent entrypoint — pipeline, prompt, config
├── tests/
│   └── test_agent.py     # LLM-judged eval suite
├── .env.example           # Environment variable template
├── pyproject.toml         # Python dependencies (uv)
├── Dockerfile             # Production container
└── railway.toml           # Railway deploy config
```

## Day 5: Nearest PHC / Government Health Facility Lookup

As part of the Murf AI "10 Days of Voice Agents – #VoiceForBharat" challenge (Health Access track), Day 5 adds a verified government health facility lookup tool.

### Features

* **Tool Added:** `find_nearest_health_facility(location_or_district)` is registered as a function tool.
* **Persistent Memory Integration:** If the user's district or location is already stored in their profile facts from Day 4, the agent automatically reuses it. Otherwise, it politely prompts the user for their location.
* **Data Source:**

  * **Live API:** Connects to the official `data.gov.in` database using the `DATA_GOV_IN_API_KEY` (default resource: `9ef84268-d588-465a-a308-a864a43d0070`).
  * **Local/Static Fallback:** If the live API is not configured or fails, the agent falls back to a high-fidelity local dataset (`health_facilities.json`) containing real, verified public health facilities across **20 major Indian districts** representing 20 different states and UTs.

### 20 States/UTs Covered

The local fallback dataset covers 20 major Indian districts representing 20 different states and UTs:

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

## Links

* [Murf Falcon TTS Docs](https://murf.ai/api/docs/text-to-speech/streaming)
* [Murf Voice Library](https://murf.ai/api/docs/voices-styles/voice-library)
* [LiveKit Agents Docs](https://docs.livekit.io/agents)
* [Deepgram Nova-3 Docs](https://developers.deepgram.com)

## License

MIT — see LICENSE.
