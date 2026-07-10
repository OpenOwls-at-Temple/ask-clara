# Progress

> **OpenOwls SDD** — Living status document. Update this file at the end of every work session.
> Claude Code reads this first at the start of every new session to catch up on project state.

## Current Phase

**Active Phase:** Phase 2 — Enhanced Features

## Status Summary

Features 1–5 (Phase 1 MVP) are implemented and deployed to staging. Phase 2 is underway: Feature 6 (development plan) is implemented and browser-verified.

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
- [x] 2026-06-26 — Expanded resume generation prompt quality (`improve/resume-prompt-quality`): added active-verb rules, accomplished/measured-by/by-doing bullet structure guidance, cliché and fabrication guards, date formatting rules, and degree/track-based section ordering. Added Research/Publications as a valid section heading for PhD and academia-track students. Synced `ai_specs/llm-integration.md` to match. Output schema and call pattern unchanged.
- [x] 2026-06-30 — Profile UI enhancements and frontend test suite (`improve/profile-ui-and-tests`): replaced triangle gap icon in `Assessment.jsx` with an inline SVG yellow warning sign; added auto-collapse of the Background & Goals section in `Intake.jsx` once degree and ranked roles are filled (with an Edit button to re-expand); added PDF file preview via blob URL when the user selects a resume (cleared after upload); added collapsed card CSS classes and a green check circle indicator to `index.css`; added favicon and apple-touch-icon. Wired up Jest + Babel + jsdom and added 22 tests across `Assessment.test.jsx` and `Intake.test.jsx` covering collapse logic, blob URL lifecycle, and SVG icon rendering. Fixed Babel preset version conflict (pinned `@babel/preset-env` and `@babel/preset-react` to `^7.22.0` to match `@babel/core@7.x`); fixed ESLint flat-config to add a CommonJS env override for `src/__mocks__/**` so `require`/`module` are recognized.
- [x] 2026-07-10 — Feature 6 implemented and browser-verified (`feature/development-plan`): `models/plan.py` (`DevelopmentPlan` — UUID id, `profile_id` FK, `horizon_months`, JSONB `items`) with Alembic migration `895488924f88`; `DEVELOPMENT_PLAN_SYSTEM` prompt updated with explicit JSON schema (same fix as Features 4/5 — spec sync to `ai_specs/llm-integration.md` Prompt 3 pending explicit instruction); `run_planning_agent` in `agents.py` plus a shared `_call_and_parse` helper that deduplicates the call/parse/retry-once logic across all three agents; `build_plan_context` in orchestrator (sends profile basics + ranked roles + saved assessment only — no PII, no raw resume text); `plan_service.py` (`generate_plan` requires profile + roles + latest saved MongoDB assessment, injects `status: "pending"` into every item server-side, persists to Postgres; `get_latest_plan`; ownership-scoped `update_item_status`); `routes/plan.py` (`POST /api/plan/generate` with atomic quota gate + refund on failure, `GET /api/plan` returns cached latest plan, `PATCH /api/plan/{id}/items/{index}` for mark complete/pending, 404 on wrong owner or bad index); frontend `Plan.jsx` page (generate/regenerate card, progress bar, checkbox milestones with persisted toggle, counselor note), `usePlan` hook, `services/plan.js`, `/plan` route + NavBar link + fourth Dashboard card; 15 new backend tests (agent, context PII, service, ownership integration) and 6 new Jest tests. All 54 backend + 28 frontend tests pass. Note: running `black` over `tests/` reformatted four pre-existing test files (style-only diff).
- [x] 2026-07-10 — Developer onboarding & staging workflow guide added (`docs/onboarding.md`, PR #10): access model (GitHub-driven; hosting dashboards stay owner-managed), local setup, test/lint commands matching CI, branch/PR workflow, Supabase migration runbook (migrate-staging-before-merge, session-mode port 5432 vs transaction pooler 6543, additive-first rule), staging smoke-test checklist, rollback paths, owner + new-developer onboarding checklists. Updated same day (`docs/sso-test-users`) with §1.2 on Google SSO's two gates: while the OAuth consent screen is in Testing mode, each tester's `@temple.edu` email must be added as a Test user in Google Cloud Console (100-user cap); the consent screen must be published to production before the student pilot; `ALLOWED_EMAIL_DOMAIN=temple.edu` remains the app-level gate either way. Owner onboarding checklist now includes the test-user step.


---

## In Progress

_(none)_

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
- [x] Feature 6: personalized 6-month development plan — complete (see 2026-07-10 entry above)
- [ ] Feature 7: job leads scanning & alerts (next Phase 2 feature)
- [ ] Before pilot launch: publish the Google OAuth consent screen to production (Testing mode caps sign-ins at 100 allowlisted test users — see `docs/onboarding.md` §1.2)

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
| 2026-06-26 | Staging deployment live and smoke tested end-to-end: sign-in (Google SSO), intake (resume upload, LinkedIn, questionnaire), AI assessment, and resume generation all working on real infrastructure (Vercel + Render + Supabase + MongoDB Atlas). URL: https://ask-clara-zeta.vercel.app |
| 2026-06-26 | Expanded resume generation prompt: active-verb + bullet-structure rules, cliché/fabrication guards, date formatting, degree/track-based section ordering, Research/Publications heading for PhD/academia; synced `ai_specs/llm-integration.md` |
| 2026-06-30 | Profile UI enhancements: SVG warning icon in Assessment, auto-collapse + Edit button + PDF preview in Intake, favicon/apple-touch-icon; wired Jest + Babel + jsdom; 22 frontend tests; fixed Babel 7/8 peer conflict and ESLint CommonJS mock override |
| 2026-07-10 | Entered Phase 2. Implemented Feature 6 (6-month development plan): `development_plans` table + migration, planning agent with schema-embedded prompt, plan service with server-injected item status, quota-gated generate route + mark-complete PATCH, Plan.jsx page with progress bar and persistent checkboxes; 15 backend + 6 frontend tests; browser-verified end-to-end with real LLM call |

