# HireLens

HireLens is an AI-assisted resume screening platform. Recruiters define job requirements, connect Gmail, import resume attachments, and will be able to review ranked candidates from a dashboard.

## Current Status

The current version provides the FastAPI backend foundation, job management, resume uploads, Gmail OAuth, and Gmail resume attachment syncing.

The dashboard is server-rendered with Jinja2 inside FastAPI. The AI resume processing and candidate ranking pipeline are not implemented yet.

## Stack

- FastAPI and Python
- PostgreSQL with SQLAlchemy and Alembic
- Redis and Celery foundation
- Gmail API with OAuth 2.0
- OpenRouter configuration for free AI models
- PDF and DOCX resume support

## Local Setup

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start PostgreSQL and Redis:

```bash
docker compose up -d
```

Create `.env` from `.env.example`, then run database migrations:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn main:app --reload
```

API documentation is available at:

```text
http://localhost:8000/docs
```

The recruiter dashboard is available at:

```text
http://localhost:8000/dashboard
```

The dashboard is protected by a development login. Configure `ADMIN_EMAIL` and `ADMIN_PASSWORD` in `.env`, then open `http://localhost:8000/` and sign in.

## Environment Variables

Required or useful local settings include:

```env
DATABASE_URL=postgresql+psycopg://hirelens:hirelens@localhost:5432/hirelens
REDIS_URL=redis://localhost:6379/0
UPLOAD_DIR=storage/uploads

OPENROUTER_API_KEY=
OPENROUTER_MODEL=openrouter/free

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/integrations/gmail/callback
APP_SECRET_KEY=change-me-before-production
```

Never commit `.env` or real credentials. `.env` is ignored by Git.

## Gmail Setup

1. Create or select a project in Google Cloud Console.
2. Enable the Gmail API.
3. Configure the OAuth consent screen.
4. Add the Gmail account as a test user.
5. Create a Web application OAuth client.
6. Add this exact redirect URI:

```text
http://localhost:8000/api/v1/integrations/gmail/callback
```

7. Put the client ID and secret in `.env`.
8. Restart the API.

Connect Gmail by opening this URL directly in a browser:

```text
http://localhost:8000/api/v1/integrations/gmail/connect
```

## Main API Endpoints

### System

- `GET /api/v1/health`

### Jobs

- `POST /api/v1/jobs`
- `GET /api/v1/jobs`
- `GET /api/v1/jobs/{job_id}`
- `PATCH /api/v1/jobs/{job_id}`
- `DELETE /api/v1/jobs/{job_id}`

### Manual Resume Uploads

- `POST /api/v1/jobs/{job_id}/resumes`
- `GET /api/v1/jobs/{job_id}/resumes`

Supported file types are PDF and DOCX. Duplicate files for the same job are skipped using SHA-256 hashes.

### Gmail

- `GET /api/v1/integrations/gmail/connect`
- `GET /api/v1/integrations/gmail/callback`
- `GET /api/v1/integrations/gmail/accounts`
- `POST /api/v1/integrations/gmail/accounts/{account_id}/sync/{job_id}`

### Dashboard

- `GET /dashboard` — workspace overview
- `GET /dashboard/jobs/new` — job creation form
- `GET /dashboard/jobs/{job_id}` — job workspace and resume queue
- `POST /dashboard/jobs/{job_id}/upload` — upload resumes through the dashboard
- `POST /dashboard/jobs/{job_id}/sync` — sync Gmail attachments for a job

The sync endpoint searches Gmail for PDF/DOCX attachments and imports them into the selected job. A custom Gmail search query can be supplied through the `query` parameter.

## Project Structure

```text
app/
├── api/          HTTP routes
├── core/         configuration and logging
├── db/           SQLAlchemy session setup
├── models/       database models
├── schemas/      Pydantic request/response schemas
└── services/     business logic and integrations
alembic/          database migrations
main.py           application entry point
```

Business logic belongs in `app/services`; API route modules should remain thin adapters around service calls.

## Validation

Run basic syntax and migration checks with:

```bash
python -m compileall app alembic main.py
alembic check
```
