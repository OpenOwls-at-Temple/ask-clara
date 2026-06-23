# Progress

> **OpenOwls SDD** — Living status document. Update this file at the end of every work session.
> Claude Code reads this first at the start of every new session to catch up on project state.

## Current Phase

**Active Phase:** Phase 1 — Core MVP

## Status Summary

Feature 1 (Google SSO + session) is implemented. Feature 2 (profile intake) is next.

---

## Completed

- [x] 2026-06-23 — Initial `ai_specs/` set written (overview, features, architecture-planning, domain-knowledge, llm-integration, conventions, auth-security, deployment)
- [x] 2026-06-23 — Repo scaffolded per `architecture-planning.md`: full `backend/` and `frontend/` directory structure, SQLAlchemy models, Pydantic schemas, route stubs, LLM layer, Alembic setup, React pages, hooks, service modules
- [x] 2026-06-23 — Feature 1 implemented: `backend/app/auth.py` (JWT helpers, `get_current_user` dep), `routes/auth.py` (login via Google tokeninfo, /refresh, /logout), `services/auth_service.py` (upsert_user); all protected routes wired to `get_current_user`; frontend `AuthProvider` + `useAuth` hook + `ProtectedRoute`; `SignIn.jsx` renders Google Identity Services button; access token kept in memory only, refresh in httpOnly cookie

---

## In Progress

- [ ] _(nothing in progress yet)_

---

## Blocked

| Item | Reason | Owner |
|------|--------|-------|
| Production hosting URLs | Pilot deploy targets not finalized | Project team |
| Career Center handoff details (Phase 3) | Partnership framework being defined with Dr. Gallo | PI |

---

## Up Next

- [ ] Run initial Alembic migration: `alembic revision --autogenerate -m "initial"` (requires `DATABASE_URL` in `.env`)
- [ ] Feature 2: profile intake — implement `profile_service.upsert_profile`, `GET/PUT /api/profile`, resume upload (pypdf/python-docx → MongoDB `resumes`, then Postgres `resume_doc_id`), LinkedIn submit
- [ ] Register a Google OAuth client at console.cloud.google.com; add `GOOGLE_CLIENT_ID` + `VITE_GOOGLE_CLIENT_ID` to `.env` files

---

## Session Log

| Date | What Was Done |
|------|---------------|
| 2026-06-23 | Authored the complete filled-in `ai_specs/` set for Clara, plus `CLAUDE.md` and `progress.md` |
| 2026-06-23 | Scaffolded full repo: backend FastAPI app (models, schemas, routes, services, LLM layer, Alembic), frontend Vite+React app (pages, hooks, services), `.gitignore`, `.env.example` files |
| 2026-06-23 | Implemented Feature 1: Google SSO auth backend (JWT, `get_current_user`, login/refresh/logout routes), frontend `AuthProvider`, `SignIn` page with GIS button, `ProtectedRoute` |
