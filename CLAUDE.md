# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> This project follows the **OpenOwls SDD (Spec-Driven Development) Process**.
> Read the files below in order before doing any work.
>
> **Project:** Clara ("Ask Clara") — an AI career coach for Temple University
> undergraduate, graduate, and PhD students.

## Session Startup — Read These First

1. **`progress.md`** (project root) — catch up on what has been done, what is in progress, and what is blocked
2. **`ai_specs/overview.md`** — understand the project goals, stakeholders, and tech stack
3. **`ai_specs/features.md`** — understand the full feature scope and which phase we are currently in
4. **`ai_specs/architecture-planning.md`** — understand folder structure, design decisions, and implementation details
5. **`ai_specs/domain-knowledge.md`** — understand domain-specific concepts and constraints
6. **`ai_specs/llm-integration.md`** — understand the LLM's role, model choice, prompt design, context strategy, and guardrails
7. **`ai_specs/conventions.md`** — follow all coding conventions, naming rules, and workflow standards without exception
8. **`ai_specs/auth-security.md`** — understand the user model, identity strategy, authentication, authorization, data protection, and threats
9. **`ai_specs/deployment.md`** — understand hosting platforms, environment variables, and deployment process

## Dev Commands

### Backend (FastAPI / Python 3.11+)
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload    # dev server on :8000

pytest                                      # all tests
pytest tests/test_assessment.py            # single test file
pytest -k "test_student_cannot"            # single test by name

black app/                                  # format
```

### Frontend (React 18 / Vite / Node 20+)
```bash
cd frontend
npm install
npm run dev                                 # dev server on :5173

npm test                                    # all tests (Jest)
npm test -- --testPathPattern=Profile      # single test file

npx eslint src/
npx prettier --write src/
```

### Database migrations (Postgres via Alembic)
```bash
cd backend
python -m alembic upgrade head             # apply pending migrations
python -m alembic revision --autogenerate -m "describe change"
```

## Architecture

Clara is a three-tier app with a multi-agent LLM layer:

```
React SPA (Vite)
  → REST API (FastAPI, Python)
    → Business logic services
      → LLM orchestrator (backend/app/llm/orchestrator.py)
        → LLM service wrapper (backend/app/llm/service.py)
          → LLM provider API — Anthropic claude-sonnet-4-6 by default;
            Gemini / DeepSeek switchable via LLM_PROVIDER env var
      → PostgreSQL (structured data: users, profiles, ranked roles, plans, leads)
      → MongoDB (documents: parsed resumes, LinkedIn extracts, generated resumes, assessments)
```

**Key layout:**
- `backend/app/routes/` — one file per resource (`assessment.py`, `profile.py`, etc.)
- `backend/app/services/` — business logic; routes call services, not DB directly
- `backend/app/llm/` — the entire LLM layer: `prompts.py` (all prompts), `agents.py` (assessment, planning, document, job-match agents), `orchestrator.py` (context assembly + token budget), `service.py` (provider-switchable client — Anthropic default, Gemini/DeepSeek via `LLM_PROVIDER` — with retry/fallback)
- `backend/app/models/` — SQLAlchemy models; `backend/app/documents/` — MongoDB access
- `frontend/src/pages/` — full-page views; `frontend/src/components/` — reusable UI; `frontend/src/services/` — API call functions (no LLM calls here, ever)

**Data layer split:** Postgres holds queryable relational records (users, profiles, `target_roles`, `development_plans`, `job_leads`). MongoDB holds document-shaped blobs (`resumes`, `linkedin`, `assessments`, `cover_letters`). Postgres rows reference MongoDB documents by `_id` string.

**Cross-DB write consistency:** Write the MongoDB document **first**, then the Postgres row. If the Postgres write fails, delete the orphaned Mongo document. There is no shared transaction; the write order is a hard rule.

**Auth flow:** Google SSO (`@temple.edu`) → backend issues short-lived JWT (access ~15 min) + httpOnly refresh cookie (~7 days). The frontend keeps the access token in memory only (never `localStorage`). On Vercel, a `/api/*` rewrite proxies to the Render backend so the cookie stays first-party.

**LLM token budget:** The project runs on a fixed grant (~$3,000 / ~500 students). Pre-truncate parsed experience to ~3 most recent roles and enforce a ~1,500-token input cap before building any prompt. Cache assessments and resumes — never re-call the model to display existing results. Enforce a database-backed per-user lifetime quota via `users.llm_generation_count`, incremented atomically.

## General Instructions

- Always work within the current phase defined in `ai_specs/features.md`. Do not implement features from a future phase unless explicitly instructed.
- After completing any meaningful unit of work, update `progress.md` to reflect what was done.
- If you encounter a conflict between these spec files, flag it to the user before proceeding.
- If a spec file is missing a detail you need, ask the user rather than assuming.
- Never delete or overwrite any file in `ai_specs/` without explicit instruction.
- Never use a library not already in `requirements.txt` or `package.json` without asking first.
- After completing the backend and frontend implementation for any new feature, STOP and prompt the user to perform a manual browser test. Ask the user if they want you to spin up the dev servers so they can visually verify the UI and end-to-end data flow before moving on to the next feature or updating progress.md.

## Clara-Specific Guardrails

- Never call the LLM from the frontend — all agents run server-side in `backend/app/llm/`.
- Never send PII (Temple email, phone, address) or self-reported first-gen/working/commuter status to the LLM. Strip contact blocks from resume text before any model call.
- Staging and production run `LLM_PROVIDER=anthropic` only. Non-Anthropic providers (Gemini/DeepSeek) are for local dev and may only ever receive synthetic/test data (`docs/fixtures/`) — never a real resume (see `ai_specs/llm-integration.md` → Privacy & Safety).
- Never fabricate a student's experience in generated resumes or cover letters. Ungrounded content goes in `notes_for_student`, not in document sections.
- Clara complements the Temple Career Center — never frame it as a replacement in user-facing copy.
- All prompts are defined only in `backend/app/llm/prompts.py` — never inline them in routes or agents.
- LLM calls in tests must be mocked — never hit a real model API (Anthropic, Gemini, or DeepSeek) in CI.
