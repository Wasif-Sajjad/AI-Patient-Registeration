# Voice AI Agent — Patient Registration System
## Complete Project Plan, Architecture & Build Guide

**Stack:** FastAPI (backend) + Next.js (frontend/dashboard) + PostgreSQL (database) + Voice AI platform (Vapi/Retell)
**Time Budget:** 3 hours (hard cap, per assessment rules)

---

## Table of Contents

1. [Goals & Evaluation Mapping](#1-goals--evaluation-mapping)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Tech Stack Decisions & Justification](#3-tech-stack-decisions--justification)
4. [Database Recommendation](#4-database-recommendation)
5. [Data Model & Schema](#5-data-model--schema)
6. [Backend Design (FastAPI)](#6-backend-design-fastapi)
7. [REST API Specification](#7-rest-api-specification)
8. [Voice AI Agent Design](#8-voice-ai-agent-design)
9. [Voice Agent ↔ Backend Integration Workflow](#9-voice-agent--backend-integration-workflow)
10. [Frontend Design (Next.js Dashboard)](#10-frontend-design-nextjs-dashboard)
11. [Error Handling & Edge Cases](#11-error-handling--edge-cases)
12. [Security](#12-security)
13. [Deployment Plan](#13-deployment-plan)
14. [Testing Plan](#14-testing-plan)
15. [Cost Breakdown & Free Alternatives](#15-cost-breakdown--free-alternatives)
16. [3-Hour Execution Timeline](#16-3-hour-execution-timeline)
17. [README.md Template](#17-readmemd-template)
18. [Bonus Challenges (If Time Remains)](#18-bonus-challenges-if-time-remains)
19. [Repository Structure](#19-repository-structure)

---

## 1. Goals & Evaluation Mapping

The assessment scores five dimensions at 20% each. Every architectural decision below is made to explicitly serve one of these:

| Dimension (20% each) | What This Plan Does About It |
|---|---|
| Working System | Voice platform (Vapi/Retell) handles telephony reliably out of the box; FastAPI + Postgres guarantees persistence across restarts and calls. |
| Conversational Quality | Dedicated system prompt design (Section 8) with correction handling, natural phrasing, confirmation step. |
| Technical Architecture | Clean 4-layer separation: Telephony/Voice → LLM/Prompt → API layer → Data layer. RESTful, validated endpoints. |
| Code Quality & Docs | Structured FastAPI project (routers/services/models/schemas), typed Pydantic schemas, documented prompt, README template included. |
| Edge Cases & Resilience | Explicit table of failure modes and handling (Section 11). |

**Golden rule from the brief:** a simple system that works end-to-end beats an ambitious one that breaks. Do not over-build — follow the timeline in Section 16 strictly.

---

## 2. High-Level Architecture

```
                         ┌─────────────────────────────┐
                         │        Caller (Phone)        │
                         └───────────────┬──────────────┘
                                          │ PSTN call
                                          ▼
                         ┌─────────────────────────────┐
                         │   Telephony + Voice Layer     │
                         │   (Vapi / Retell AI)          │
                         │   - Number provisioning        │
                         │   - STT (speech→text)          │
                         │   - TTS (text→speech)           │
                         │   - Turn-taking / interruption │
                         └───────────────┬──────────────┘
                                          │ LLM completions +
                                          │ "function/tool calls"
                                          ▼
                         ┌─────────────────────────────┐
                         │        LLM Layer               │
                         │   (GPT-4o-mini / Claude)       │
                         │   - System prompt (conversation │
                         │     policy, validation rules)   │
                         │   - Tool defs: create_patient,  │
                         │     find_patient, update_patient│
                         └───────────────┬──────────────┘
                                          │ HTTPS (tool call → webhook)
                                          ▼
                         ┌─────────────────────────────┐
                         │     FastAPI Backend            │
                         │  ┌───────────────────────┐    │
                         │  │  /voice-webhook (tool  │    │
                         │  │  execution endpoint)   │    │
                         │  └───────────┬────────────┘    │
                         │  ┌───────────▼────────────┐    │
                         │  │  Service layer          │    │
                         │  │  (validation, business   │    │
                         │  │   logic, dup. detection) │    │
                         │  └───────────┬────────────┘    │
                         │  ┌───────────▼────────────┐    │
                         │  │  /patients REST API     │◄───┼──── Next.js Dashboard
                         │  │  (CRUD, filters)         │    │      (fetches via HTTPS)
                         │  └───────────┬────────────┘    │
                         └──────────────┼─────────────────┘
                                          │ SQLAlchemy ORM
                                          ▼
                         ┌─────────────────────────────┐
                         │   PostgreSQL (Supabase/       │
                         │   Railway managed Postgres)   │
                         │   - patients table              │
                         │   - call_logs table (optional)  │
                         └─────────────────────────────┘
```

**Key architectural principle:** the voice platform never talks to the database directly. It only calls FastAPI tool-webhooks, and FastAPI is the single source of truth and validation gate — this satisfies "validate all inputs server-side (do not rely solely on the voice agent for validation)."

---

## 3. Tech Stack Decisions & Justification

| Layer | Choice | Why |
|---|---|---|
| Telephony + Voice AI | **Vapi** (fallback: Retell AI) | Abstracts STT/TTS/turn-taking, gives you a real phone number in minutes, has native "tool calling" that maps directly onto REST endpoints. Fastest path to a working system in 3 hours, as the brief itself recommends. |
| LLM | **GPT-4o-mini** via Vapi's built-in model config (fallback: Claude 3.5 Haiku) | Cheap, fast, good instruction-following for structured slot-filling conversations. Low latency matters for voice. |
| Backend | **FastAPI (Python)** | Async, automatic OpenAPI docs, Pydantic validation out of the box (directly satisfies "validate all inputs server-side"), fast to scaffold. |
| ORM / Migrations | **SQLAlchemy 2.0 + Alembic** | Type-safe schema, migration history, works identically against SQLite (dev) and Postgres (prod). |
| Database | **PostgreSQL** (Section 4 has full reasoning) | |
| Frontend | **Next.js (App Router) + TypeScript + Tailwind** | You already chose this; it's the natural fit for the bonus "Dashboard" requirement and for a clean API-consumer demo. |
| Hosting (backend) | **Railway** (fallback: Render) | One-command deploy from GitHub, free Postgres add-on, environment variable UI, persistent (not serverless — important for SQLite/DB connections and background consistency). |
| Hosting (frontend) | **Vercel** | Native Next.js support, free tier, instant preview URLs. |
| Local dev tunnel (if needed) | **ngrok** | Only needed if testing Vapi webhooks against localhost before deploying. |

---

## 4. Database Recommendation

### Comparison

| Option | Persistence Across Restarts | Free Hosting | Concurrent Write Safety | Setup Speed | Verdict |
|---|---|---|---|---|---|
| SQLite (file-based) | ⚠️ Only if hosting disk is persistent (many free hosts wipe on redeploy) | Yes (built-in) | Weak (file locks) | Fastest | Good for **local dev only** |
| **PostgreSQL (managed)** | ✅ Yes, durable | ✅ Yes (Supabase free tier, Railway free Postgres) | ✅ Strong | Fast (5 min via Supabase/Railway) | **Recommended** |
| MongoDB Atlas | ✅ Yes | ✅ Yes (free tier) | ✅ Good | Fast | Viable, but the data is inherently relational (fixed schema, foreign-key-like relations, enums, constraints) — Postgres is a better semantic fit |

### Recommendation: **PostgreSQL**, hosted on **Supabase (free tier)** or **Railway's free Postgres plug-in**

**Why Postgres over SQLite for this specific challenge:**
- The brief explicitly tests "data must survive server restarts" and "second call without data loss" — free serverless/container hosts (Railway, Render free tier, Fly.io) often use **ephemeral filesystems**, so a SQLite file can silently vanish on redeploy or container restart. Postgres as a managed service is durable independent of your app container's lifecycle.
- The schema has real constraints (enums for `sex`, 2-letter state codes, UUID primary keys, timestamps) — Postgres enforces these natively at the DB level, not just in application code, which strengthens your "Technical Architecture" score.
- Free tier is genuinely free and takes ~5 minutes to provision (Supabase gives you a connection string immediately).

**When SQLite would be acceptable:** only if you are demoing entirely from your **local machine via ngrok** and won't need long-term persistence beyond the review call — a valid, documented trade-off per the brief's own guidance ("SQLite over Postgres" is explicitly listed as an acceptable shortcut). But since deployment is required for review, use Postgres.

---

## 5. Data Model & Schema

### SQL DDL (Postgres)

```sql
CREATE TYPE sex_enum AS ENUM ('Male', 'Female', 'Other', 'Decline to Answer');

CREATE TABLE patients (
    patient_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    first_name              VARCHAR(50)  NOT NULL,
    last_name               VARCHAR(50)  NOT NULL,
    date_of_birth            DATE         NOT NULL CHECK (date_of_birth <= CURRENT_DATE),
    sex                      sex_enum     NOT NULL,
    phone_number             VARCHAR(10)  NOT NULL,   -- store digits only, format at API edge
    email                    VARCHAR(255),
    address_line_1           VARCHAR(255) NOT NULL,
    address_line_2           VARCHAR(255),
    city                     VARCHAR(100) NOT NULL,
    state                    CHAR(2)      NOT NULL,
    zip_code                 VARCHAR(10)  NOT NULL,   -- 5-digit or ZIP+4
    insurance_provider       VARCHAR(255),
    insurance_member_id      VARCHAR(100),
    preferred_language       VARCHAR(50)  DEFAULT 'English',
    emergency_contact_name   VARCHAR(100),
    emergency_contact_phone  VARCHAR(10),
    created_at               TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at               TIMESTAMPTZ  NOT NULL DEFAULT now(),
    deleted_at               TIMESTAMPTZ                     -- soft delete
);

CREATE INDEX idx_patients_phone ON patients (phone_number) WHERE deleted_at IS NULL;
CREATE INDEX idx_patients_last_name ON patients (last_name) WHERE deleted_at IS NULL;
CREATE INDEX idx_patients_dob ON patients (date_of_birth) WHERE deleted_at IS NULL;

-- optional bonus: call transcripts
CREATE TABLE call_logs (
    call_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id   UUID REFERENCES patients(patient_id),
    transcript   TEXT,
    summary      TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Design notes:**
- `patient_id` as UUID (not serial int) matches the spec and avoids leaking record counts.
- `deleted_at` implements the required **soft delete** — `DELETE /patients/:id` sets this rather than removing the row.
- `updated_at` should be bumped via a trigger or explicitly in the service layer on every `PUT`.
- Phone numbers stored as raw 10 digits; format (e.g., `(555) 123-4567`) only at the presentation layer (API response / voice readback) — keeps validation and duplicate-lookup simple.

---

## 6. Backend Design (FastAPI)

### Folder Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app init, CORS, router mounting
│   ├── config.py                # env var loading (pydantic-settings)
│   ├── database.py               # SQLAlchemy engine/session
│   ├── models/
│   │   └── patient.py            # SQLAlchemy ORM model
│   ├── schemas/
│   │   └── patient.py            # Pydantic request/response schemas
│   ├── routers/
│   │   ├── patients.py           # /patients CRUD endpoints
│   │   └── voice_webhook.py      # /voice/tool-call endpoint (Vapi tool handler)
│   ├── services/
│   │   └── patient_service.py    # business logic, validation, dup-detection
│   └── utils/
│       └── validators.py         # phone/zip/state/date validators
├── alembic/                      # migrations
├── tests/
│   └── test_patients_api.py
├── requirements.txt
├── .env.example
└── Dockerfile
```

### Layered responsibility (Separation of Concerns)

1. **Router layer** — HTTP concerns only (status codes, request parsing).
2. **Service layer** — business rules: field validation beyond Pydantic types, duplicate-phone detection, soft-delete logic.
3. **Model layer** — persistence only.
4. **Voice webhook router** — translates Vapi's tool-call JSON payload into calls against the *same service layer* used by the REST API (no duplicated logic — this is the key "clean architecture" point to call out in your README).

### Response Envelope (required by spec)

```json
{ "data": { ... }, "error": null }
```
On failure:
```json
{ "data": null, "error": { "code": "VALIDATION_ERROR", "message": "date_of_birth cannot be in the future", "field": "date_of_birth" } }
```
Implement this as a FastAPI middleware/exception handler so every endpoint (including validation errors, 404s, 500s) returns the same shape.

---

## 7. REST API Specification

| Method | Endpoint | Description | Status Codes |
|---|---|---|---|
| GET | `/patients` | List patients. Query params: `last_name`, `date_of_birth`, `phone_number` (all optional, combinable) | 200 |
| GET | `/patients/{id}` | Get one patient by UUID | 200, 404 |
| POST | `/patients` | Create patient | 201, 400, 422 |
| PUT | `/patients/{id}` | Partial update | 200, 400, 404, 422 |
| DELETE | `/patients/{id}` | Soft delete (`deleted_at = now()`) | 200, 404 |
| POST | `/voice/tool-call` | Internal webhook Vapi calls for `create_patient`, `find_patient_by_phone`, `update_patient` tools | 200, 400 |

All list/detail endpoints exclude soft-deleted rows by default (`WHERE deleted_at IS NULL`).

Validation happens via Pydantic models with custom validators (regex for state codes, ZIP, phone digit count, date not in future) — **independent of whatever the voice agent already checked**, per the explicit requirement.

---

## 8. Voice AI Agent Design

### Platform: Vapi (or Retell AI as fallback)

Configure:
1. A phone number (Vapi provisions a real US number instantly on paid — or trial — tier).
2. An **Assistant** with:
   - System prompt (below)
   - Model: GPT-4o-mini
   - Voice: any natural TTS voice (e.g., ElevenLabs "Rachel" or Vapi's default)
   - **Tools** (function definitions) that map 1:1 to your FastAPI endpoints

### Tool Definitions (given to the LLM)

```json
[
  {
    "name": "find_patient_by_phone",
    "description": "Look up an existing patient by phone number to check for duplicates before creating a new record.",
    "parameters": { "phone_number": "string" }
  },
  {
    "name": "create_patient",
    "description": "Create a new patient record after all required fields are collected and confirmed.",
    "parameters": { "...all required + optional fields..." }
  },
  {
    "name": "update_patient",
    "description": "Update an existing patient's record when the caller is a returning patient.",
    "parameters": { "patient_id": "string", "...fields to update..." }
  }
]
```

Each tool call resolves to a webhook POST to `/voice/tool-call`, which your FastAPI service layer executes and returns a result the LLM reads back to the caller.

### System Prompt (documented, commented — include verbatim in README)

```
You are Alex, a warm and efficient intake coordinator for [Clinic Name].
You are speaking on the phone, not typing — keep responses short, natural, and
conversational. Never sound like a form or IVR menu.

GOAL: Collect the caller's demographic info to register them as a new patient,
or update their record if they already exist.

FLOW:
1. Greet warmly: "Hi, thanks for calling [Clinic Name], this is Alex — I can help
   get you registered. Can I start with your first and last name?"
2. As soon as you have a phone number, silently call find_patient_by_phone.
   - If found: ask "It looks like we already have a record for {first} {last} —
     would you like to update your information instead of creating a new one?"
     If yes, switch to update flow.
3. Collect REQUIRED fields one at a time or in small natural groups (don't
   interrogate — ask 1-2 things per turn):
   first_name, last_name, date_of_birth, sex, phone_number, address_line_1,
   city, state, zip_code.
4. Validate as you go, conversationally:
   - Date of birth: must be a real past date. If invalid/future, say:
     "Hmm, that date doesn't look right — could you repeat your date of birth?"
   - Phone number: must be 10 digits. If not, re-ask just that field.
5. After required fields are collected, offer optional info ONCE:
   "I can also grab your insurance info, an emergency contact, and your
   preferred language if you'd like — totally optional. Want to add any of that?"
   Only collect what they opt into.
6. CONFIRMATION (required): Read back ALL collected fields clearly, e.g.
   "Let me read that back: [Full Name], born [DOB], phone number [number],
   living at [address]... Did I get everything right?"
   - If caller corrects anything ("actually my last name is spelled D-A-V-I-S"),
     update that field only and re-confirm just that field.
7. Once confirmed, call create_patient (or update_patient) with the final data.
8. Relay the outcome:
   - Success: "You're all set, [First Name]! Thanks for calling, have a great day."
   - Failure: "I'm sorry, I ran into an issue saving your information — let me
     try that again," then retry once; if it fails again, apologize and say a
     team member will follow up, then end the call gracefully.

RULES:
- Never read technical error messages aloud.
- If the caller wants to start over, discard collected fields and restart
  from question 1, acknowledging: "No problem, let's start fresh."
- If interrupted mid-sentence, stop talking and listen.
- Handle out-of-order info naturally (if they blurt out their whole address
  before you asked, accept it and skip ahead).
- Default preferred_language to "English" unless stated otherwise.
- Keep every turn under ~2 sentences unless reading back the full confirmation.
```

This prompt directly targets the "Conversational Quality" rubric: natural tone, correction handling, confirmation-before-save, graceful interruption/out-of-order handling.

---

## 9. Voice Agent ↔ Backend Integration Workflow

Sequence for a **new patient** call:

```
Caller ──dial──▶ Vapi Number ──▶ Assistant starts, greets
Assistant ──collects first/last/phone──▶ 
Assistant ──tool call: find_patient_by_phone──▶ FastAPI /voice/tool-call
FastAPI ──queries Postgres──▶ no match found ──▶ returns { found: false }
Assistant ──continues collecting remaining required fields──▶
Assistant ──offers optional fields, caller opts in/out──▶
Assistant ──reads back full summary, caller confirms/corrects──▶
Assistant ──tool call: create_patient(payload)──▶ FastAPI /voice/tool-call
FastAPI service layer ──validates──▶ writes to Postgres ──▶ returns patient_id
Assistant ──"You're all set, Jane!"──▶ call ends
```

Returning-caller path adds the branch: `find_patient_by_phone` returns `{found: true, patient}` → assistant asks to update → collects only changed fields → calls `update_patient`.

**Logging:** Every tool-call webhook logs the full payload + response to stdout (satisfies "log agent conversations... final collected data payload").

---

## 10. Frontend Design (Next.js Dashboard)

Purpose: satisfies the bonus "Dashboard" item and gives you a fast way to visually verify data during testing/review.

```
frontend/
├── app/
│   ├── page.tsx                # Patient list table (fetches GET /patients)
│   ├── patients/[id]/page.tsx  # Patient detail/edit view
│   └── layout.tsx
├── components/
│   ├── PatientTable.tsx
│   ├── PatientFilterBar.tsx    # filters by last_name/dob/phone
│   └── PatientForm.tsx         # for manual create/edit (nice-to-have)
├── lib/
│   └── api.ts                  # typed fetch wrapper for FastAPI base URL
└── .env.local                  # NEXT_PUBLIC_API_BASE_URL
```

Keep this minimal: a table view + search/filter bar + detail page is enough. Don't spend more than ~20-25 minutes of your 3-hour budget here (see timeline).

---

## 11. Error Handling & Edge Cases

| Scenario | Handling |
|---|---|
| Invalid date of birth (future date, malformed) | LLM re-prompts specifically for DOB; backend also rejects with 422 via Pydantic `@validator` as a second safety net. |
| 3-digit or malformed phone number | Same dual-layer approach: conversational re-ask + server-side regex validation (`^\d{10}$`). |
| Telephony connection drops mid-call | Nothing to persist if no `create_patient` call was made yet — no partial records. If you want resilience, have the assistant call a lightweight `save_partial_progress` tool after each confirmed field (stretch goal, not required). Document this as a known limitation if not implemented. |
| Database write fails (POST /patients errors) | Webhook returns `{success: false, error}`; assistant is instructed to say a friendly retry message, attempt once more, then apologize and end gracefully rather than going silent. |
| Caller wants to start over | Prompt explicitly instructs LLM to discard in-progress fields and restart — this is conversation-state, no backend call needed until final confirm. |
| Duplicate phone number on create | `find_patient_by_phone` check before collecting full details (bonus requirement) — prevents duplicate records. |
| Missing required field at confirmation | Backend Pydantic model marks required fields as non-optional — a POST with a missing required field returns 422 with a field-level error message that the assistant can react to (re-ask that field) rather than showing a broken/silent failure. |
| Malformed email | Optional field — validate format only if provided (`EmailStr` in Pydantic), don't block registration if invalid; ask once to confirm/correct. |

Document any of these you *don't* fully implement (e.g., mid-call resume) plainly under "Known Limitations" in the README — the brief explicitly rewards honest trade-off documentation over silent gaps.

---

## 12. Security

- No API keys or secrets in source code — all via environment variables (`.env`, loaded through `pydantic-settings`; `.env` in `.gitignore`).
- Vapi webhook endpoint (`/voice/tool-call`) should validate a shared-secret header or Vapi's signature (if available) so random internet traffic can't inject fake patient records.
- Basic input sanitization: Pydantic type coercion + regex validators handle this; also strip/trim string inputs.
- CORS: restrict FastAPI's allowed origins to your deployed Next.js domain (and localhost for dev) rather than `*`.
- Do not log full patient PII in production-style logs beyond what's needed for the "log final payload" requirement — acceptable here since this is explicitly a non-HIPAA technical assessment with no real patient data (per FAQ).

---

## 13. Deployment Plan

1. **Database:** Create a free Postgres instance on Supabase → copy connection string.
2. **Backend:** Push `backend/` to GitHub → connect repo to Railway → set env vars (`DATABASE_URL`, `VAPI_WEBHOOK_SECRET`) → Railway auto-builds via `Dockerfile` or Nixpacks → note the public URL (`https://your-app.up.railway.app`).
3. Run Alembic migrations against the deployed DB (`alembic upgrade head`) — either via Railway's one-off command runner or a startup hook in `main.py`.
4. **Voice agent:** In Vapi dashboard, create Assistant → paste system prompt → register the three tools, each pointing its webhook URL at `https://your-app.up.railway.app/voice/tool-call` → buy/assign a phone number → test call yourself.
5. **Frontend:** Push `frontend/` to GitHub → import into Vercel → set `NEXT_PUBLIC_API_BASE_URL` to the Railway backend URL → deploy.
6. Smoke-test: call the number end-to-end, then check the Next.js dashboard and `GET /patients` directly to confirm persistence.
7. Restart the Railway backend service manually and re-query `/patients` to prove persistence survives restarts (this is literally graded).

---

## 14. Testing Plan

Given the time limit, keep this pragmatic:

- **Manual end-to-end:** at minimum 2 real calls — one full new-patient registration, one returning-caller/duplicate-detection call.
- **API unit/integration tests** (bonus, use `pytest` + `httpx.AsyncClient` + a test SQLite DB or test Postgres schema):
  - `test_create_patient_success`
  - `test_create_patient_missing_required_field_422`
  - `test_get_patient_not_found_404`
  - `test_soft_delete_excludes_from_list`
  - `test_duplicate_phone_detection`
- **Edge-case manual test:** speak an invalid DOB ("February 30th") and an invalid phone number during a call to confirm re-prompting.

---

## 15. Cost Breakdown & Free Alternatives

| Component | Paid Option (typical cost) | Free / Free-Tier Alternative |
|---|---|---|
| Phone number + telephony | Vapi: ~$0.05–0.09/min all-in (STT+LLM+TTS+telephony) after free trial credit; Twilio number ~$1.15/mo + usage | **Vapi free trial credit** (~$10–20 on signup, plenty for a demo); Twilio also offers trial credit with a **free trial phone number** (outbound to verified numbers only until upgraded — fine for reviewer's number if you verify it) |
| STT/TTS | Included in Vapi pricing; standalone Deepgram/ElevenLabs have free tiers (Deepgram ~$200 free credit, ElevenLabs free tier ~10k chars/mo) | Use Vapi's bundled default voice (no extra cost) instead of premium ElevenLabs voices |
| LLM | GPT-4o-mini: ~$0.15/1M input tokens (a few cents for a whole call) | **Groq** (Llama 3.1/3.3 models) has a generous free tier and very low latency — good fallback if OpenAI credit runs out |
| Backend hosting | Railway free tier: $5 free credit/month, then usage-based | **Render free web service** (spins down when idle — adds cold-start latency, document as a limitation) or run locally + **ngrok free tier** (temporary URL, rate-limited) |
| Database | Supabase free tier: 500MB, plenty for this | Railway also bundles a free Postgres add-on; both are $0 for this scale |
| Frontend hosting | Vercel free (Hobby) tier | Same — no cost at this scale |
| Domain / TLS | N/A — not required | Railway/Vercel/Vapi all provide HTTPS subdomains automatically, no purchase needed |

**Total realistic cost to complete and demo this challenge: $0**, using Vapi's signup trial credit, Supabase free Postgres, Railway free backend hosting, and Vercel free frontend hosting. The only place real cost could creep in is heavy testing call volume beyond the trial credit — keep test calls to a handful of short, focused runs.

**If Vapi's trial credit is insufficient:** fallback to **Twilio (free trial, no card needed for basic testing) + Twilio's built-in `<Gather>`/Media Streams + a free-tier LLM (Groq)** — more integration work, so only take this path if Vapi/Retell signup is blocked, and document the trade-off in "Known Limitations" per the FAQ's explicit guidance that vendor issues won't be penalized if documented.

---

## 16. 3-Hour Execution Timeline

| Time | Task |
|---|---|
| 0:00–0:15 | Provision Supabase Postgres; scaffold FastAPI project skeleton; set up Alembic |
| 0:15–0:45 | Build models/schemas/service layer + `/patients` CRUD endpoints; run migration |
| 0:45–1:00 | Write and test API manually (curl/Postman) against live DB |
| 1:00–1:15 | Deploy backend to Railway; confirm public URL works |
| 1:15–1:45 | Set up Vapi assistant: system prompt, tool definitions, webhook endpoint (`/voice/tool-call`); wire tools to service layer |
| 1:45–2:15 | Provision phone number; test call end-to-end; iterate on prompt for natural flow + corrections handling |
| 2:15–2:40 | Scaffold + deploy Next.js dashboard (list + filter view) pointed at Railway API |
| 2:40–2:55 | Edge case pass: invalid DOB, invalid phone, restart backend to confirm persistence, duplicate-call test |
| 2:55–3:00 | Write README, push final commit, gather phone number + URLs for submission |

If running behind, cut scope in this order: dashboard polish → optional fields flow → bonus tests → Spanish/multi-language — never cut the confirmation step or server-side validation, since those are explicitly graded.

---

## 17. README.md Template

```markdown
# Voice AI Patient Registration System

## Live Demo
- Phone number: +1 (XXX) XXX-XXXX
- API base URL: https://your-app.up.railway.app
- Dashboard: https://your-app.vercel.app

## Architecture
[paste the diagram from Section 2]

## Tech Stack & Justification
[paste Section 3 table]

## Setup Instructions
1. Clone repo
2. `cd backend && cp .env.example .env` (fill in DATABASE_URL, VAPI_WEBHOOK_SECRET)
3. `pip install -r requirements.txt && alembic upgrade head && uvicorn app.main:app --reload`
4. `cd frontend && cp .env.example .env.local && npm install && npm run dev`
5. Configure Vapi assistant per `docs/vapi-setup.md` (system prompt + tool definitions included there)

## Environment Variables
| Variable | Description |
|---|---|
| DATABASE_URL | Postgres connection string |
| VAPI_WEBHOOK_SECRET | Shared secret to validate incoming tool-call webhooks |
| NEXT_PUBLIC_API_BASE_URL | Backend URL for the frontend |

## System Prompt
[paste the full documented prompt from Section 8]

## Known Limitations / Trade-offs
- No mid-call resume if the connection drops before confirmation (documented, not implemented due to time).
- Dashboard is read/filter-only; editing is done via API/Postman, not UI (time trade-off).
- Multi-language support not implemented (bonus, skipped for time).

## Next Steps
- [whatever you didn't get to]
```

---

## 18. Bonus Challenges (If Time Remains)

Priority order if extra time is available after core scope is solid:
1. **Duplicate detection** — already built into the core flow above (cheap to include, high signal).
2. **Automated tests** — quick to add with `pytest`, strong "Code Quality" signal.
3. **Call transcript storage** (`call_logs` table already scaffolded above) — Vapi provides transcripts in its webhook payloads, just persist them.
4. **Appointment scheduling** — mock a static list of available slots, add a 4th tool `schedule_appointment`.
5. **Multi-language** — add a language-detection instruction to the prompt + Vapi's multilingual voice option; highest effort/lowest priority given time budget.

---

## 19. Repository Structure

```
voice-ai-patient-registration/
├── backend/            # FastAPI service (Section 6)
├── frontend/            # Next.js dashboard (Section 10)
├── docs/
│   ├── vapi-setup.md     # step-by-step Vapi assistant configuration + prompt
│   └── architecture.png  # exported diagram (optional)
├── README.md
└── .gitignore
```
