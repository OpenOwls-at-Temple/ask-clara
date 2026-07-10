# Architecture Planning

> **OpenOwls SDD** — Read by the system architect and software engineers.
> Defines the folder structure, key design decisions, and implementation details.
> Claude Code uses this file to understand how the codebase is organized.

---

## System Architecture Overview

Clara is a three-tier web application with a multi-agent LLM layer:

- A **React (Vite) frontend** that handles sign-in, profile intake, and the views for assessments, plans, resumes, and job leads.
- A **FastAPI backend** that exposes a REST API, enforces auth and ownership, runs business logic, and is the **only** place that calls the LLM.
- A **hybrid data layer**: **PostgreSQL** for structured/queryable records (users, profiles, ranked preferences, plans, job leads) and **MongoDB** for document-shaped data (parsed resumes, LinkedIn extracts, generated resumes and cover letters, assessment transcripts).
- An **LLM orchestration layer** inside the backend that coordinates specialized "agents" (assessment, planning, document generation, job matching). Each agent is a prompt + service function; the orchestrator decides which agent runs and assembles context. Agents are called server-side only.

Frontend → REST → backend services → (Postgres + MongoDB) and, where reasoning is needed, → LLM orchestrator → Anthropic API.

---

## Folder Structure

```
clara/
├── CLAUDE.md
├── progress.md
├── ai_specs/
├── frontend/
│   ├── src/
│   │   ├── components/     # Reusable UI (UploadCard, RankedJobInput, AssessmentPanel, ResumeViewer)
│   │   ├── pages/          # SignIn, Dashboard, Intake, Assessment, Resumes, JobLeads
│   │   ├── hooks/          # useAuth, useProfile, useAssessment
│   │   ├── services/       # API call functions (auth, profile, assessment, documents, leads)
│   │   └── utils/          # Formatters, validators, file helpers
│   ├── tests/
│   └── public/
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI app entrypoint
│   │   ├── routes/         # auth.py, profile.py, assessment.py, documents.py, leads.py
│   │   ├── models/         # SQLAlchemy models (Postgres)
│   │   ├── documents/      # MongoDB document access (resumes, generated docs, transcripts)
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic (profile_service, assessment_service, ...)
│   │   └── llm/            # LLM integration layer
│   │       ├── prompts.py      # ALL prompt definitions, one place
│   │       ├── agents.py       # Assessment, Planning, Document, JobMatch agents
│   │       ├── orchestrator.py # Picks agents, assembles context, enforces token budget
│   │       └── service.py      # Anthropic client wrapper + retry/fallback
│   └── tests/
└── docs/
```

---

## Key Design Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| API style | REST | Simple for students to learn, test, and debug |
| Auth method | Google SSO (`@temple.edu`) + JWT session | Avoids storing passwords; fits a university audience |
| LLM calls | Server-side only | Keeps the API key secure and centralizes prompt logic and the token budget |
| Data layer | Hybrid: Postgres + MongoDB | Postgres for relational profile/preference data; MongoDB for document-shaped resumes and generated artifacts (per faculty guidance) |
| Multi-agent design | Prompt-per-agent behind one orchestrator | Maps to the proposal's assessment/planning/document/matching agents while staying debuggable |
| Resume generation | LLM drafts, user edits, nothing fabricated | Materials must reflect the student's real record |
| Job scanning (Phase 2) | GitHub Actions cron → authenticated trigger endpoint → background task + stored leads | Keeps scraping off the user request path and respectful of source sites. **Do not use an in-process scheduler (APScheduler etc.):** Render's free tier stops the process after ~15 min idle, so an internal timer would silently never fire. Instead, a scheduled GitHub Actions workflow (free, versioned in-repo, manual-run capable via `workflow_dispatch`) POSTs to `/api/admin/scan-jobs` with a shared secret; the request wakes the service, the endpoint validates the secret, starts the scan as a background task, and returns 202. The workflow then polls the status endpoint until completion — the polling doubles as keep-alive traffic so Render doesn't spin the instance down mid-scan. Decided 2026-07-10. |
| Cross-DB write consistency | Write-order + compensating cleanup | A write spans MongoDB (the document) and Postgres (the row that references its `_id`), which can't share one transaction. Write the Mongo document **first**, then the Postgres row; if the Postgres write fails, the route **must** catch the error and delete the just-created Mongo document so no orphan is left. A periodic sweep that deletes unreferenced documents is an acceptable simpler alternative for the pilot. |

---

## Data Models

### Postgres — `users`
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `temple_email` | String (unique) | `@temple.edu` identity from SSO |
| `display_name` | String | Student name |
| `role` | Enum | `student`, `counselor`, `admin` |
| `llm_generation_count` | Integer (default 0) | Lifetime count of expensive LLM generations; backs the per-user hard quota (see `auth-security.md`) |
| `created_at` | DateTime | Record creation (UTC) |
| `last_login_at` | DateTime | Most recent sign-in |

### Postgres — `profiles`
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `user_id` | UUID (FK → users) | Owner |
| `degree_level` | Enum | `undergrad`, `grad`, `phd` |
| `major_program` | String | Major or program |
| `expected_graduation` | Date | Graduation timeline |
| `track` | Enum | `industry`, `academia`, `government`, `undecided` |
| `is_first_gen` | Boolean (optional, self-reported) | For prioritized outreach; never required |
| `resume_doc_id` | String | Reference to MongoDB resume document |
| `linkedin_doc_id` | String | Reference to MongoDB LinkedIn extract |
| `updated_at` | DateTime | Last update (UTC) |

### Postgres — `target_roles`
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `profile_id` | UUID (FK → profiles) | Owner profile |
| `rank` | Integer (1–3) | Preference ranking |
| `title` | String | Target role / "dream job" |
| `notes` | Text | Optional student notes |

### Postgres — `development_plans` (Phase 2)
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `profile_id` | UUID (FK) | Owner |
| `horizon_months` | Integer | Default 6 |
| `created_at` | DateTime | Generation time |
| `items` | JSONB | List of `{skill, why, target_rank, status}` where `status` is `pending` or `complete`; the backend injects `status` (the LLM does not produce it) |

### Postgres — `job_leads` (Phase 2)
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `profile_id` | UUID (FK) | Owner |
| `source` | String | Where the posting came from |
| `url` | String | Link to the original posting |
| `title` / `employer` | String | Role and employer |
| `fit_score` | Float | Match strength to ranked preferences |
| `fit_reason` | Text | Why Clara matched it |
| `status` | Enum | `new`, `seen`, `applied`, `dismissed` |
| `found_at` | DateTime | Discovery time (UTC) |

### MongoDB — document collections
| Collection | Shape |
|------------|-------|
| `resumes` | `{ user_id, kind: "uploaded"|"generated", target_rank, raw_text, structured_json, created_at }` |
| `linkedin` | `{ user_id, raw_text, structured_json, created_at }` |
| `assessments` | `{ user_id, strengths[], gaps[], recommendations[], model, created_at }` |
| `cover_letters` | `{ user_id, lead_id, body, created_at }` (Phase 2) |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/auth/me` | Current authenticated user |
| POST | `/api/auth/login` | Begin/complete Google SSO; issue session |
| POST | `/api/auth/logout` | End session |
| GET | `/api/profile` | Get the current user's profile + ranked roles |
| PUT | `/api/profile` | Create/update profile and ranked target roles |
| POST | `/api/profile/resume` | Upload & parse a resume (PDF/DOCX) |
| POST | `/api/profile/linkedin` | Submit LinkedIn URL or export |
| POST | `/api/assessment` | Run the assessment agent; return + persist results |
| GET | `/api/assessment` | List saved assessments |
| POST | `/api/resumes/generate` | Generate three tailored base resumes |
| GET | `/api/resumes` | List the user's resume drafts |
| POST | `/api/plan/generate` | (Phase 2) Generate 6-month development plan |
| GET | `/api/leads` | (Phase 2) List matched job leads |
| POST | `/api/leads/:id/materials` | (Phase 2) Tailored resume + cover letter + employer brief |
| POST | `/api/admin/scan-jobs` | (Phase 2) Trigger the job-leads scan; called by the scheduled GitHub Actions workflow, returns 202 and runs the scan as a background task |
| GET | `/api/admin/scan-jobs/status` | (Phase 2) Scan progress/completion; polled by the workflow (doubles as keep-alive) |

All non-auth routes require a valid session and enforce that the record belongs to the requesting user. Exception: the Phase 2 `/api/admin/scan-jobs*` endpoints are machine-to-machine — they authenticate via a `SCAN_TRIGGER_SECRET` shared-secret header (set in both Render and GitHub Actions secrets), not a user session.

---

## LLM Integration

- **Where the LLM layer lives:** backend service layer (`backend/app/llm/`), called server-side only. The orchestrator (`orchestrator.py`) selects an agent, assembles minimal context from Postgres/Mongo, and calls `service.py`, which wraps the Anthropic client with retry and fallback.
- **Full details:** see `ai_specs/llm-integration.md`.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key for LLM calls |
| `DATABASE_URL` | PostgreSQL connection string |
| `MONGODB_URI` | MongoDB connection string |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google SSO credentials |
| `JWT_SECRET` | Secret for signing session tokens |
| `ENVIRONMENT` | `local`, `staging`, or `production` |
| `SCAN_TRIGGER_SECRET` | (Phase 2) Shared secret authenticating the GitHub Actions job-scan trigger |

---

## Deployment

Deployment details are covered in `ai_specs/deployment.md`.
