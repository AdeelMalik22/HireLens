# HireLens Implementation Plan

## 1. Product Objective

Build an MVP that allows recruiters to create a job, upload multiple resumes, process them asynchronously, and view an explainable ranked list of candidates.

The system will use AI for resume information extraction and candidate summaries. Candidate scoring and ranking will be handled by deterministic backend logic so results remain consistent and transparent.

## 2. MVP Technology Stack

- Backend: FastAPI, Python
- Database: PostgreSQL
- ORM and migrations: SQLAlchemy and Alembic
- Background processing: Celery with Redis as broker/result backend
- Resume parsing:
  - PyMuPDF for PDF files
  - python-docx for DOCX files
- AI provider: OpenRouter using free models
- Frontend: React
- Local development: Docker Compose for PostgreSQL and Redis

OpenRouter API access must be configured through environment variables. The selected free model should be configurable rather than hardcoded, because free model availability and limits may change.

## 3. High-Level Architecture

```text
React client
    |
    v
FastAPI API ---- PostgreSQL
    |
    v
Celery worker ---- Redis
    |
    v
Resume parser + OpenRouter
```

1. The recruiter creates a job through the API.
2. Resume files are uploaded and registered against that job.
3. FastAPI queues a processing task for each resume.
4. A Celery worker extracts text and structured candidate data.
5. The backend calculates the match score from normalized data.
6. OpenRouter generates a concise candidate summary where appropriate.
7. The API exposes processing status, rankings, and candidate details.

## 4. Core Data Model

### Job

- `id`
- `title`
- `description`
- `required_skills`
- `preferred_skills`
- `minimum_years_experience`
- `created_at`
- `updated_at`

### Candidate / Resume

- `id`
- `job_id`
- `original_filename`
- `file_path` or object-storage reference
- `file_hash` for duplicate detection
- `processing_status`
- `processing_error`
- `candidate_name`
- `email`
- `phone`
- `skills`
- `work_experience`
- `years_of_experience`
- `education`
- `certifications`
- `projects`
- `technologies`
- `ai_summary`
- `created_at`
- `updated_at`

### Match Result

- `id`
- `job_id`
- `candidate_id`
- `required_skill_score`
- `experience_score`
- `preferred_skill_score`
- `overall_score`
- `matched_required_skills`
- `missing_required_skills`
- `matched_preferred_skills`
- `created_at`
- `updated_at`

Use JSON/JSONB fields for extracted lists and structured sections during the MVP, while keeping the scoring fields normalized and queryable.

## 5. API Scope

### Jobs

- `POST /api/v1/jobs` — create a job
- `GET /api/v1/jobs` — list jobs
- `GET /api/v1/jobs/{job_id}` — retrieve job details
- `PATCH /api/v1/jobs/{job_id}` — update job requirements
- `DELETE /api/v1/jobs/{job_id}` — remove a job and its associated data, subject to retention rules

### Resumes and Candidates

- `POST /api/v1/jobs/{job_id}/resumes` — upload one or more PDF/DOCX resumes
- `GET /api/v1/jobs/{job_id}/resumes` — list resumes and processing states
- `GET /api/v1/jobs/{job_id}/candidates` — return ranked candidates
- `GET /api/v1/candidates/{candidate_id}` — return candidate details and score explanation
- `POST /api/v1/candidates/{candidate_id}/reprocess` — retry failed processing

### Processing

- `GET /api/v1/jobs/{job_id}/processing-status` — return upload and processing progress

Use Pydantic schemas for request validation and response contracts. Return clear errors for unsupported files, duplicate uploads, missing jobs, and processing failures.

## 6. Resume Processing Pipeline

1. Validate file extension, MIME type, and size.
2. Calculate a SHA-256 hash and detect duplicates for the same job.
3. Store the file securely outside public web directories.
4. Create a resume record with status `queued`.
5. Queue a Celery task.
6. Extract text using the appropriate parser.
7. Normalize whitespace, sections, skills, and experience values.
8. Send only the necessary resume text to OpenRouter.
9. Ask the model for structured JSON matching a strict schema.
10. Validate and sanitize the model response.
11. Calculate deterministic match scores.
12. Generate or store the AI summary.
13. Persist results and mark the resume `completed`.
14. On failure, store a safe error message and mark it `failed` for retry.

The worker should use timeouts, bounded retries, structured logging, and rate-limit handling for OpenRouter requests.

## 7. OpenRouter Integration

Create a small provider abstraction so the application can switch models without changing business logic.

Required configuration:

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `OPENROUTER_BASE_URL`
- Request timeout and retry settings

The extraction prompt should require:

- Strict JSON output
- `null` or empty arrays when information is absent
- No inferred facts that are not present in the resume
- Consistent skill and experience formats

Because free models may have lower reliability or rate limits, the backend must validate responses, retry transient failures, and provide a fallback status when extraction cannot be completed.

## 8. Deterministic Scoring

Default weights:

- Required skills: 50 points
- Experience: 30 points
- Preferred skills: 20 points

Suggested calculation:

```text
required_skill_score = matched_required / total_required * 50
experience_score = min(candidate_years / minimum_years, 1) * 30
preferred_skill_score = matched_preferred / total_preferred * 20
overall_score = required_skill_score + experience_score + preferred_skill_score
```

Edge cases to define:

- No preferred skills: redistribute or omit the preferred-skill weight.
- No minimum experience: award the full experience component or remove it from the total.
- Skill aliases: normalize common equivalents such as `Postgres` and `PostgreSQL`.
- Missing required skills: clearly display them even when the overall score is high.

The scoring service should be pure, unit-testable, and independent of FastAPI, Celery, and the AI provider.

## 9. Security and Privacy

- Keep API keys in environment variables or a secrets manager.
- Validate uploads and reject unsupported or suspicious files.
- Store resumes with restricted access and avoid public URLs.
- Do not log resume contents, contact details, or API keys.
- Apply authorization checks to every job and candidate endpoint.
- Define a basic data deletion and retention policy before production use.
- Treat AI output as assistance, not an automatic hiring decision.

## 10. Delivery Milestones

### Milestone 1 — Project Foundation

- Create FastAPI project structure.
- Add configuration, logging, error handling, and health endpoint.
- Set up PostgreSQL, Redis, SQLAlchemy, and Alembic.
- Add Docker Compose for local development.

### Milestone 2 — Jobs and Uploads

- Implement job model and CRUD endpoints.
- Implement bulk PDF/DOCX uploads.
- Add file validation, secure storage, and duplicate detection.
- Add database migrations and API tests.

### Milestone 3 — Processing Pipeline

- Implement PDF and DOCX text extraction.
- Add Celery tasks and processing status tracking.
- Add retry and failure handling.
- Test batches of at least 50 resumes.

### Milestone 4 — AI Extraction

- Integrate OpenRouter through a provider service.
- Define extraction and summary prompts.
- Validate structured model responses.
- Add model timeout, retry, and rate-limit handling.

### Milestone 5 — Matching and Ranking

- Implement skill normalization.
- Implement deterministic scoring.
- Persist score components and match explanations.
- Add ranked candidate and candidate-detail endpoints.

### Milestone 6 — Frontend MVP

- Job creation form.
- Bulk upload screen with progress/status.
- Ranked candidate list.
- Candidate detail and score explanation view.

### Milestone 7 — Hardening and Release

- Add authentication and authorization.
- Run security and validation checks.
- Test duplicate, malformed, empty, and very large resumes.
- Add API documentation and deployment configuration.
- Verify end-to-end processing and success criteria.

## 11. Testing Strategy

- Unit tests for scoring, skill normalization, parsers, and schema validation.
- API tests for job, upload, candidate, and status endpoints.
- Worker tests for success, retry, timeout, and failure paths.
- Mock OpenRouter in automated tests.
- Integration tests with PostgreSQL and Redis.
- End-to-end test: create job → upload resumes → process → rank → inspect details.
- Performance test with at least 50 resumes in one upload.

## 12. MVP Acceptance Criteria

The MVP is ready when a recruiter can:

1. Create a job with required skills, preferred skills, and experience requirements.
2. Upload at least 50 PDF/DOCX resumes.
3. See processing progress and failed-file errors.
4. View extracted candidate information.
5. View candidates ranked by deterministic match score.
6. See matched and missing skills plus score components.
7. Read an AI-generated candidate summary.
8. Retry failed processing.
9. Avoid duplicate resume records for the same job.
10. Access resume data securely through authorized endpoints.

## 13. Decisions to Confirm Before Production

- Authentication method and user roles.
- Resume file size and total storage limits.
- Exact model selected from OpenRouter's free models.
- Whether preferred/experience weights are redistributed in edge cases.
- Resume retention and deletion period.
- Production file storage provider.
- Whether candidate data may be sent to the selected OpenRouter model under the organization's privacy policy.

