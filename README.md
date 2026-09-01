# Voice AI Patient Registration — Backend Starter

FastAPI + SQLAlchemy 2.0 (async) + Alembic + PostgreSQL backend. Exposes a
REST API for patient records and a `/voice/tool-call` webhook that a
voice platform (Vapi, Retell, Bland.ai, Twilio, etc.) calls during a live
phone conversation. Both entry points share the same service layer
(`app/services/patient_service.py`) — no duplicated validation logic.

```
.
├── docker-compose.yml        # Postgres + backend, one command up
├── .env.example               # root env for docker-compose (Postgres creds)
└── backend/
    ├── Dockerfile
    ├── entrypoint.sh          # runs alembic upgrade head, then uvicorn
    ├── requirements.txt
    ├── .env.example
    ├── alembic.ini
    ├── alembic/
    │   ├── env.py
    │   └── versions/0001_create_patients_table.py
    └── app/
        ├── main.py            # FastAPI app, envelope error handlers
        ├── config.py          # pydantic-settings
        ├── database.py        # async engine/session
        ├── models/patient.py
        ├── schemas/patient.py # validation matching the spec
        ├── services/patient_service.py
        └── routers/
            ├── patients.py    # REST CRUD
            └── voice.py       # voice-platform tool-call webhook
```

## Option A — Docker (recommended, DB included)

Requires Docker + Docker Compose.

```bash
git clone <your-repo-url>
cd voice-ai-patient-registration

cp .env.example .env
cp backend/.env.example backend/.env

docker compose up --build
```

This starts:
- **db** — Postgres 16 in a container with a named volume (`pgdata`), so data
  survives `docker compose down` / restarts.
- **backend** — builds the FastAPI image, waits for Postgres to be healthy,
  runs `alembic upgrade head` (creates the schema + 2 seed patients), then
  starts `uvicorn` on port 8000 with hot reload.

API is now live at `http://localhost:8000`. Check `http://localhost:8000/health`
and `http://localhost:8000/docs` (Swagger UI).

To stop: `docker compose down` (add `-v` to also wipe the database volume).

## Option B — Local Python virtual environment (no Docker for the app; still needs a Postgres)

If you'd rather run the app directly and only use Docker for Postgres:

```bash
# 1. Start just Postgres in Docker
docker compose up -d db

# 2. Create and activate a venv
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install deps
pip install -r requirements.txt

# 4. Configure env — point DATABASE_URL at localhost, not the "db" hostname
cp .env.example .env
# then edit .env:
#   DATABASE_URL=postgresql+asyncpg://voiceai:voiceai@localhost:5432/voiceai

# 5. Run migrations
alembic upgrade head

# 6. Start the API
uvicorn app.main:app --reload
```

Fully local, no Docker at all also works if you install Postgres yourself —
just point `DATABASE_URL` at wherever it's running.

## API quick reference

All responses use the envelope `{ "data": ..., "error": null }`.

| Method | Endpoint          | Description                                   |
|--------|-------------------|------------------------------------------------|
| GET    | /patients         | List, filter by `?last_name=&date_of_birth=&phone_number=` |
| GET    | /patients/{id}    | Fetch one patient                              |
| POST   | /patients         | Create                                         |
| PUT    | /patients/{id}    | Partial update                                 |
| DELETE | /patients/{id}    | Soft-delete (sets `deleted_at`)                |
| POST   | /voice/tool-call  | Voice-platform function/tool webhook           |

Example:

```bash
curl -X POST http://localhost:8000/patients \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "date_of_birth": "1992-03-10",
    "sex": "Female",
    "phone_number": "555-234-5566",
    "address_line_1": "1 Elm St",
    "city": "Denver",
    "state": "CO",
    "zip_code": "80202"
  }'
```

## Wiring up the voice agent

1. Pick a platform (Vapi/Retell are fastest — see FAQ in the challenge doc).
2. Point its custom function/tool at `POST {API_BASE_URL}/voice/tool-call`
   with header `X-Webhook-Secret: <VOICE_WEBHOOK_SECRET>`.
3. Define tools `register_patient`, `find_patient_by_phone`, `update_patient`
   with arguments matching the fields in `app/schemas/patient.py`.
4. Adjust `_extract_call()` in `app/routers/voice.py` to match your chosen
   platform's actual webhook payload shape (Vapi and Retell differ — a
   couple of examples are stubbed in comments).
5. Write the system prompt so the agent: collects required fields → offers
   optional fields → reads everything back for confirmation → calls
   `register_patient` → relays success/failure to the caller.

## Tech stack justification

- **FastAPI + async SQLAlchemy** — natural fit for a webhook that needs to
  stay responsive during a live phone call, and gives free OpenAPI docs.
- **PostgreSQL** — real constraints/types, survives restarts, works
  identically in Docker and hosted (Railway/Render/Fly.io).
- **Alembic** — versioned schema, `alembic upgrade head` on boot means the
  DB is always in the right state without manual steps.
- **Pydantic v2** — validation rules (name characters, phone digit count,
  state abbreviation, ZIP format, DOB not in the future) live in one place
  and apply to both the REST API and the voice webhook.

## Known limitations / next steps

- `voice/tool-call`'s `_extract_call` currently supports two example payload
  shapes and needs adapting to whichever platform is actually provisioned.
- No automated tests yet (bonus item in the assessment).
- No call transcript storage / duplicate-detection UX beyond
  `find_patient_by_phone` returning a match.
- CORS is wide open (`*`) — tighten to the dashboard's real origin before
  any real deployment.
