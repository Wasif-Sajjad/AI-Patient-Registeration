# CloudCare - Voice AI Patient Registration

This project is an AI-powered voice agent system that allows patients to call a phone number and register their demographic information conversationally. The agent collects all required details, validates them, and pushes them to a FastAPI backend which stores them in a PostgreSQL database.

## 🚀 Features
- **Conversational Voice AI**: Powered by Vapi, enabling real-time STT/TTS and natural conversation flow.
- **Strict Data Validation**: Agent validates data (like past Date of Birth) before invoking backend tools.
- **Next.js Dashboard**: Live, real-time dashboard displaying patients fetched via the API.
- **Browser Web Dialer**: Integrated Vapi Web SDK for testing directly from the browser.

---

## 🖥️ The CloudCare Dashboard
The frontend is a custom-built Next.js (App Router) application designed to manage the patient data collected by the AI.
- **Premium UI/UX**: Built with Tailwind CSS utilizing a modern glassmorphism aesthetic, dark mode gradients, and micro-animations.
- **Real-Time Data**: Directly pulls live patient data from the FastAPI backend.
- **Integrated Dialer**: Features a built-in Vapi dialer widget right on the dashboard, bypassing browser autoplay restrictions so you can test the AI agent natively.
- **Record Management**: Includes a soft-delete function to safely remove test records from the UI without losing underlying database history.

---

## Architecture & Tech Stack

The architecture follows a standard webhook integration model where a third-party Voice AI platform handles real-time audio and STT/TTS, and defers business logic (database updates) to a custom API via tool calls.

### Tech Stack Justification
- **Backend: FastAPI (Python)**
  FastAPI was chosen for its native asynchronous support, auto-generated OpenAPI documentation, and strict Pydantic data validation. Voice AI webhooks require sub-second latency to prevent awkward pauses in conversation; asynchronous Python with `asyncpg` ensures non-blocking database queries to meet this constraint.
- **Try it Live!**
  - **Call the Agent:** `+1 (860) 483 9208`
  - **Dashboard:** `http://localhost:3000`
- **Database: PostgreSQL + SQLAlchemy (Alembic)**
  PostgreSQL provides strict schema constraints (e.g., UUIDs, timezone-aware datetimes, ENUM types) ensuring data integrity. SQLAlchemy ORM abstracts complex SQL operations and Alembic manages safe database migrations.
- **Frontend: Next.js (App Router) + Tailwind CSS**
  A modern, responsive, server-rendered dashboard was chosen for the frontend to quickly and securely fetch patient data directly from the FastAPI backend and render it with premium glassmorphism aesthetics. The `@vapi-ai/web` SDK (pinned to v1.x for Next.js SSR compatibility) is embedded to allow browser-based testing.
- **Voice Platform: Vapi**
  Vapi abstracts away Twilio telephony, Deepgram STT, and OpenAI integration, allowing us to focus on the prompt engineering and backend tool schema.

---

## Setup Instructions

### 1. Prerequisites
- Docker and Docker Compose
- Python 3.10+
- Node.js 18+

### 2. Backend Setup
1. Open a terminal in the `backend/` directory.
2. Create a virtual environment: `python -m venv venv` and activate it.
3. Install dependencies: `pip install -r requirements.txt`.
4. Start the database: `docker-compose up -d`.
5. Run database migrations: `alembic upgrade head`.
6. Start the FastAPI server: `uvicorn app.main:app --reload`.

### 3. Frontend Setup
1. Open a terminal in the `frontend/` directory.
2. Install dependencies: `npm install`.
3. Start the Next.js server: `npm run dev`.
4. Visit `http://localhost:3000` to view the dashboard.

---

## Required Environment Variables

You need a `.env` file in the `backend/` directory:

```env
DEBUG=True
API_BASE_URL=http://localhost:8000
VOICE_WEBHOOK_SECRET=mwstesting

# Database Connection (FastAPI uses this)
DATABASE_URL=postgresql+asyncpg://voiceai:voiceai@localhost:5433/voiceai

# Docker Compose Database Settings
POSTGRES_USER=voiceai
POSTGRES_PASSWORD=voiceai
POSTGRES_DB=voiceai
```

---

## System Prompt (Vapi LLM Instructions)

The following prompt was heavily engineered to ensure strict data collection, conversational flow, and resilience against edge cases:

```text
You are Alex, a warm and highly efficient intake coordinator for CloudCare.
You are speaking on the phone. Your tone must be friendly, professional, and conversational. 
Never sound like a robot, an IVR menu, or read raw JSON errors aloud.

GOAL: Collect the caller's demographic info to register them as a new patient, or update their record if they already exist.

FLOW:
1. Greet: "Hi, thanks for calling CloudCare. This is Alex — I can help get you registered today. Can I start with your first and last name?"
2. As soon as you hear a name and a phone number (often provided via caller ID), silently call `find_patient_by_phone`.
   - If found: "It looks like we already have a record for {first} {last}. Would you like to update your information instead?" If yes, switch to update flow.
3. Collect REQUIRED fields one at a time. Ask a maximum of 1 or 2 questions per turn to keep the conversation flowing. You MUST collect:
   - first_name and last_name (Verify spelling if it's unusual)
   - date_of_birth (Format: YYYY-MM-DD. Ask for the year if omitted)
   - biological sex (Must be exactly "Male", "Female", or "Other")
   - phone_number (10 digits)
   - address_line_1, city, state (State MUST be a 2-letter abbreviation, e.g., "NY" for New York), zip_code
4. Validate conversationally:
   - If the date of birth is in the future: "Hmm, that date doesn't look quite right — could you repeat your date of birth for me?"
   - If the state is provided as a full word, silently convert it to the 2-letter abbreviation for the system.
5. CONFIRMATION (Critical): Before saving, you MUST read back ALL collected fields for accuracy: 
   "Let me just read that back to make sure I have everything right: {full name}, born {DOB}, phone {number}, living at {address}... Did I get that all correct?"
   - If the caller corrects anything, acknowledge the correction gently ("Oh, my apologies, let me fix that"), update only that field, and re-confirm it.
6. Once confirmed, call `register_patient` (or `update_patient`) with the final data payload.
7. Relay the outcome:
   - Success: "You're all set, {first_name}! Your registration is complete. Thanks for calling, and have a great day."
   - Failure: "I'm sorry, I'm having a little trouble saving your info on my end. Let me try that one more time." Retry once. If it fails again: "I apologize for the trouble — our system seems to be down. A team member will follow up with you shortly." Then end the call.

RULES:
- If the caller wants to start over, say "No problem, let's take it from the top" and clear your context.
- If the user interrupts you, stop speaking and listen.
- Accept information out of order naturally (e.g., if they give their zip code with their city).
- Keep every response under 2 sentences unless reading back the full confirmation.
```

---

## Known Limitations & Trade-offs

1. **Mid-Call Drops:** If a call drops before the user confirms their information and the `register_patient` tool is called, all progress is lost. Implementing a Redis-backed session state to persist partial information across calls was considered but omitted to reduce architectural complexity for this MVP.
2. **Strict Webhook Schema:** The FastAPI backend relies on Vapi's specific JSON payload schema (`message.toolCalls`). If we were to switch to another voice provider (like Retell or Bland AI), the parsing logic in `app/routers/voice.py` would need to be rewritten to support the new schema.
3. **Database Migrations during Active Traffic:** Alembic runs migrations synchronously. In a production environment with high voice traffic, database schema changes might block the webhook thread temporarily, resulting in higher latency for the LLM. A blue-green deployment strategy would be needed.
