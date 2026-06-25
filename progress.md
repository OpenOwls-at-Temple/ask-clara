# Progress

> **OpenOwls SDD** — Living status document. Update this file at the end of every work session.
> Claude Code reads this first at the start of every new session to catch up on project state.

## Current Phase

**Active Phase:** Phase 1 — Core MVP

## Status Summary

Features 1–5 are implemented. Phase 1 MVP is complete.

---

## Completed

- [x] 2026-06-23 — Initial `ai_specs/` set written (overview, features, architecture-planning, domain-knowledge, llm-integration, conventions, auth-security, deployment)
- [x] 2026-06-23 — Repo scaffolded per `architecture-planning.md`: full `backend/` and `frontend/` directory structure, SQLAlchemy models, Pydantic schemas, route stubs, LLM layer, Alembic setup, React pages, hooks, service modules
- [x] 2026-06-23 — Feature 1 implemented: `backend/app/auth.py` (JWT helpers, `get_current_user` dep), `routes/auth.py` (login via Google tokeninfo, /refresh, /logout), `services/auth_service.py` (upsert_user); all protected routes wired to `get_current_user`; frontend `AuthProvider` + `useAuth` hook + `ProtectedRoute`; `SignIn.jsx` renders Google Identity Services button; access token kept in memory only, refresh in httpOnly cookie
- [x] 2026-06-23 — Feature 2 implemented: `profile_service.py` (get/upsert profile, set_resume/linkedin_doc_id), `GET /api/profile` + `PUT /api/profile`, `POST /api/profile/resume` (pypdf/python-docx parsing, MongoDB-first write with Postgres compensating cleanup), `POST /api/profile/linkedin` (URL storage); `documents/linkedin.py`; Pydantic validators enforce unique ranks 1–3; frontend `Intake.jsx` (questionnaire, resume upload, LinkedIn URL, pre-filled on return), `useProfile` hook, `Dashboard.jsx` with completion status
- [x] 2026-06-24 — Feature 4 implemented and verified end-to-end in browser: `assessment_service.run_assessment` (load profile + resume/LinkedIn text from Postgres/MongoDB, strip PII via orchestrator, call assessment agent, persist to MongoDB `assessments`); `POST /api/assessment` (atomic quota increment via `UPDATE ... WHERE count < cap RETURNING`, ValueError refunds the slot, RuntimeError on LLM failure returns 503); `GET /api/assessment` (returns cached results, never re-calls model); frontend `Assessment.jsx` (load-on-mount, run button, displays strengths/gaps/recommendations with counselor note); 7 new tests covering agent retry, service validation, and LLM failure paths. LLM bugs fixed: embedded exact JSON schema in `ASSESSMENT_SYSTEM` prompt to prevent model from inventing its own schema; replaced `_strip_code_fences` with `_extract_json` (regex + brace-walk handles prose-prefixed and mid-fence responses); raised `ASSESSMENT_MAX_OUTPUT` to 2000 to prevent truncation.
- [x] 2026-06-24 — Feature 5 implemented: `assessment_service.generate_resumes` (load profile + resume/LinkedIn from Postgres/MongoDB, call `run_resume_agent` once per ranked target role, persist each to MongoDB `resumes` with `kind='generated'`); updated `RESUME_GENERATION_SYSTEM` prompt with explicit JSON schema to prevent model from inventing its own; `POST /api/resumes/generate` (atomic quota gate, ValueError refund, 503 on LLM failure); `GET /api/resumes` (returns cached generated resumes, never re-calls model); `PATCH /api/resumes/{id}` (saves user edits, ownership-gated); `documents/resumes.py` extended with `get_generated_resumes_for_user` and `update_resume_edited_text`; `schemas/resume.py` added (`ResumeOut`, `ResumeEditRequest`); frontend `useResumes.js` hook; `Resumes.jsx` page (generate button, three resume cards with sections, notes for student, copy-to-clipboard, .txt download, inline edit + save); resume page CSS added to `index.css`; 8 new tests (agent, service, ownership).
- [x] 2026-06-24 — Production readiness remediations implemented: added infinite quota bypasses for local environments, implemented full quota refunds on LLM/runtime exceptions, refactored resume tailoring to run concurrently with `asyncio.gather`, offloaded synchronous PDF/docx parsing to thread pools, set up automatic cleanups for overwritten MongoDB documents, generated and applied Alembic migrations for PostgreSQL foreign key indexes, registered collection startup index creators for MongoDB, implemented silent frontend JWT refreshing every 10 minutes, and set up a transactional pytest harness to verify and pass all 34 unit and integration tests.
- [x] 2026-06-24 — Fixed resume download gap (Feature 5 AC3): added `GET /api/resumes/{id}/download` endpoint that generates a DOCX file using `python-docx` (already in requirements.txt) and streams it back with the correct Content-Disposition header. Uses structured sections for clean formatting, falls back to line-by-line rendering when `edited_text` is present. Ownership is enforced (returns 404 for wrong user). Added `requestBlob` helper to `auth.js`, `downloadResume` service function, and updated the "Download .txt" button to "Download .docx" in `Resumes.jsx`. Added 2 new tests (DOCX content-type check, cross-user ownership block). All 39 tests pass.
- [x] 2026-06-24 — Fixed LinkedIn intake gap (Feature 2 AC2): added `POST /api/profile/linkedin/upload` endpoint that accepts a LinkedIn PDF/DOCX export, parses its text (reusing the resume parsing pipeline), and stores the content as `raw_text` so the LLM receives actual profile content. Fixed the URL-only path to store an empty `raw_text` (URL was previously stored as `raw_text`, polluting LLM context with a bare URL string). Added a LinkedIn export upload zone to `Intake.jsx` with instructions, alongside the existing URL reference field. Updated `useProfile` hook and `profile.js` service. Added 3 new tests (URL stores empty raw_text, export upload parses text, invalid file type rejected). All 37 tests pass.


---

## In Progress

- [ ] Staging deployment — infrastructure setup in progress (Supabase, Atlas, Render, Vercel, GitHub Actions)

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
- [x] Feature 5: generate three tailored resumes — complete (see 2026-06-24 entry above)

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
| 2026-06-25 | Staging deployment scaffolding: added `FRONTEND_ORIGIN` env var to config + dynamic CORS in `main.py`; created `frontend/vercel.json` (API rewrite to Render); created `render.yaml` (Render service IaC); created `.github/workflows/ci.yml` (GitHub Actions — backend pytest + black, frontend jest + eslint, with Postgres/Mongo service containers); created `frontend/eslint.config.js` (ESLint 9 flat config) |

