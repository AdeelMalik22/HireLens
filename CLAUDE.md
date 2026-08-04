# HireLens Development Guide

## Project Overview

HireLens is a FastAPI backend for recruiter-assisted resume screening. Recruiters create jobs, connect Gmail, import resume attachments, and will later review AI-processed candidate rankings in a dashboard.

## Technology

- Python and FastAPI
- PostgreSQL, SQLAlchemy, and Alembic
- Redis and Celery
- Gmail API with OAuth 2.0
- OpenRouter free models
- PDF and DOCX resume parsing

## Important Architecture Rules

- Keep API route modules thin.
- Put business logic, database operations, integrations, and orchestration in `app/services/`.
- Use Pydantic schemas for API input and output validation.
- Keep SQLAlchemy models in `app/models/`.
- Use service-level exceptions and map them to HTTP errors in API routes.
- Roll back database sessions after database failures.
- Never log resume contents, OAuth tokens, API keys, or other sensitive data.
- Do not put secrets in source control. Use `.env`, which is Git-ignored.
- Candidate scoring must be deterministic backend logic; AI is used for extraction and summaries.

## Project Structure

```text
app/api/       API routes and HTTP adapters
app/core/      configuration and logging
app/db/        database session setup
app/models/    SQLAlchemy models
app/schemas/   Pydantic schemas
app/services/  business logic and integrations
alembic/       database migrations
main.py        application entry point
```

## Local Development

```bash
pip install -r requirements.txt
docker compose up -d
alembic upgrade head
uvicorn main:app --reload
```

API documentation is available at `http://localhost:8000/docs`.

## Validation

Before committing changes, run:

```bash
python -m compileall app alembic main.py
git diff --check
```

For schema changes, create an Alembic migration and verify it with:

```bash
alembic check
```

## Gmail Integration

The Gmail integration uses read-only OAuth access. The callback URL for local development is:

```text
http://localhost:8000/api/v1/integrations/gmail/callback
```

Google credentials belong in `.env` as `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`. Gmail tokens must not be exposed in API responses or logs.

## Git Workflow

- Use a separate commit for each feature, bug fix, refactor, or documentation change.
- Use clear conventional commit messages such as `feat:`, `fix:`, `refactor:`, and `docs:`.
- Do not commit `.env`, credentials, generated caches, or local uploads.
- Keep migrations included with the model changes they support.
