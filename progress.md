# Progress

> **OpenOwls SDD** — Living status document. Update this file at the end of every work session.
> Claude Code reads this first at the start of every new session to catch up on project state.

## Current Phase

**Active Phase:** Phase 1 — Core MVP

## Status Summary

Features 1 and 2 are implemented. Feature 3 (persistent profile, already covered by F2's DB layer) is done. Feature 4 (AI assessment) is next.

---

## Completed

- [x] 2026-06-23 — Initial `ai_specs/` set written (overview, features, architecture-planning, domain-knowledge, llm-integration, conventions, auth-security, deployment)
- [x] 2026-06-23 — Repo scaffolded per `architecture-planning.md`: full `backend/` and `frontend/` directory structure, SQLAlchemy models, Pydantic schemas, route stubs, LLM layer, Alembic setup, React pages, hooks, service modules
- [x] 2026-06-23 — Feature 1 implemented: `backend/app/auth.py` (JWT helpers, `get_current_user` dep), `routes/auth.py` (login via Google tokeninfo, /refresh, /logout), `services/auth_service.py` (upsert_user); all protected routes wired to `get_current_user`; frontend `AuthProvider` + `useAuth` hook + `ProtectedRoute`; `SignIn.jsx` renders Google Identity Services button; access token kept in memory only, refresh in httpOnly cookie
- [x] 2026-06-23 — Feature 2 implemented: `profile_service.py` (get/upsert profile, set_resume/linkedin_doc_id), `GET /api/profile` + `PUT /api/profile`, `POST /api/profile/resume` (pypdf/python-docx parsing, MongoDB-first write with Postgres compensating cleanup), `POST /api/profile/linkedin` (URL storage); `documents/linkedin.py`; Pydantic validators enforce unique ranks 1–3; frontend `Intake.jsx` (questionnaire, resume upload, LinkedIn URL, pre-filled on return), `useProfile` hook, `Dashboard.jsx` with completion status
- [x] 2026-06-24 — Feature 4 implemented and verified end-to-end in browser: `assessment_service.run_assessment` (load profile + resume/LinkedIn text from Postgres/MongoDB, strip PII via orchestrator, call assessment agent, persist to MongoDB `assessments`); `POST /api/assessment` (atomic quota increment via `UPDATE ... WHERE count < cap RETURNING`, ValueError refunds the slot, RuntimeError on LLM failure returns 503); `GET /api/assessment` (returns cached results, never re-calls model); frontend `Assessment.jsx` (load-on-mount, run button, displays strengths/gaps/recommendations with counselor note); 7 new tests covering agent retry, service validation, and LLM failure paths. LLM bugs fixed: embedded exact JSON schema in `ASSESSMENT_SYSTEM` prompt to prevent model from inventing its own schema; replaced `_strip_code_fences` with `_extract_json` (regex + brace-walk handles prose-prefixed and mid-fence responses); raised `ASSESSMENT_MAX_OUTPUT` to 2000 to prevent truncation.

---

## In Progress

- [ ] Feature 5: generate three tailored resumes (next up)

---

---

## Blocked

| Item | Reason | Owner |
|------|--------|-------|
| Production hosting URLs | Pilot deploy targets not finalized | Project team |
| Career Center handoff details (Phase 3) | Partnership framework being defined with Dr. Gallo | PI |

---

## Up Next

- [x] Run initial Alembic migration: `alembic revision --autogenerate -m "initial"` (completed 2026-06-23)
- [x] Feature 4: AI assessment — complete (see 2026-06-24 entry above)
- [x] Frontend UI redesign — complete (see 2026-06-24 entry below)
- [ ] Feature 5: generate three tailored resumes — implement `assessment_service.generate_resumes` (call resume agent once per ranked role, persist to MongoDB `resumes` with `kind='generated'`), wire `POST /api/resumes/generate` and `GET /api/resumes`; frontend `Resumes.jsx`

---

## Session Log

| Date | What Was Done |
|------|---------------|
| 2026-06-23 | Authored the complete filled-in `ai_specs/` set for Clara, plus `CLAUDE.md` and `progress.md` |
| 2026-06-23 | Scaffolded full repo: backend FastAPI app (models, schemas, routes, services, LLM layer, Alembic), frontend Vite+React app (pages, hooks, services), `.gitignore`, `.env.example` files |
| 2026-06-23 | Implemented Feature 1: Google SSO auth backend (JWT, `get_current_user`, login/refresh/logout routes), frontend `AuthProvider`, `SignIn` page with GIS button, `ProtectedRoute` |
| 2026-06-23 | Implemented Feature 2: profile service, GET/PUT /api/profile, resume upload (pypdf/docx + MongoDB-first write), LinkedIn URL submit; Intake page with pre-fill, Dashboard with completion status |
| 2026-06-23 | Set up Docker Compose local databases (PostgreSQL/MongoDB), configured `.env` templates, fixed `pymongo`/`motor` driver version conflicts, created Alembic templates, ran database migrations, repaired and verified unit tests, and added Vite proxy configurations |
| 2026-06-24 | Implemented Feature 4: assessment service, POST/GET /api/assessment routes with atomic quota gate, Assessment.jsx frontend page, 7 new passing tests |
| 2026-06-24 | E2E browser tested Feature 4 with real Anthropic API. Fixed three LLM bugs: JSON schema not specified in prompt (model invented own schema), `_strip_code_fences` not robust to prose-prefixed responses, `ASSESSMENT_MAX_OUTPUT=600` truncating the response mid-JSON |
| 2026-06-24 | Complete frontend UI redesign: built `src/index.css` design system with Temple cherry red tokens, custom typography scale, button/form/card/badge components; redesigned SignIn (dark hero split layout with radial glow + dot grid, white auth panel), Dashboard (progress card grid with left-border status accents), Intake (form cards with 2-column grid, cherry-numbered ranked roles, upload zone), Assessment (color-coded result items — green strengths, amber gaps, cherry recommendations); added shared `NavBar.jsx` component with sticky dark bar, cherry stripe, and active nav state; no CSS framework used |

