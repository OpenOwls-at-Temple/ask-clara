# Progress

> **OpenOwls SDD** — Living status document. Update this file at the end of every work session.
> Claude Code reads this first at the start of every new session to catch up on project state.
>
> **Entry format:** this file records *state* — current phase, what's done, what's blocked,
> what's next. Keep each Completed entry to 2–3 lines with a PR link; implementation detail
> belongs in the PR description and commit history, not here. When a phase completes, move its
> entries to `docs/progress-archive.md` (full-length pre-2026-07-11 entries are already there).

## Current Phase

**Active Phase:** Phase 2 — Enhanced Features

## Status Summary

Features 1–5 (Phase 1 MVP) are implemented and deployed to staging
(https://ask-clara-zeta.vercel.app). Phase 2 is underway: Features 6 (development plan),
7 (job leads scanning & alerts), and 8 (posting-tailored materials) are shipped and live.
Feature 9 (interview prep guidance) is next.

---

## Completed

### Phase 1 — MVP (2026-06-23 → 2026-06-30, live on staging since 06-26)

Full narrative in `docs/progress-archive.md`.

- [x] 2026-06-23 — `ai_specs/` set authored; repo scaffolded per `architecture-planning.md`; local Docker databases + Alembic set up (PR #1)
- [x] 2026-06-23 — Feature 1: Google SSO auth — JWT + httpOnly refresh cookie, `get_current_user`, frontend `AuthProvider`/`ProtectedRoute`
- [x] 2026-06-23 — Feature 2: profile intake — questionnaire, resume upload + parsing (MongoDB-first write), LinkedIn, Dashboard status
- [x] 2026-06-24 — Feature 4: AI assessment — quota-gated, cached, PII-stripped; three LLM output bugs fixed in browser testing (PR #2)
- [x] 2026-06-24 — Frontend UI redesign with Temple design system (PR #3)
- [x] 2026-06-24 — Feature 5: three tailored resumes, one per ranked role — generate/edit/download, ownership-gated (PR #4)
- [x] 2026-06-24 — Phase 1 AC gaps closed (DOCX download, LinkedIn export upload) + production-readiness fixes (quota refunds, concurrency, indexes) (PR #5)
- [x] 2026-06-25/26 — Staging deployed and smoke-tested end-to-end: Vercel + Render + Supabase + MongoDB Atlas; CI workflow added (PRs #6, #7)
- [x] 2026-06-26 — Resume prompt quality rules (active verbs, fabrication guards, section ordering); spec synced (`improve/resume-prompt-quality`)
- [x] 2026-06-30 — Profile UI polish + Jest frontend test suite (22 tests) (PR #8)

### Phase 2 — Enhanced Features (2026-07-10 → )

- [x] 2026-07-10 — Feature 6: 6-month development plan — `development_plans` table, planning agent, quota-gated routes, `Plan.jsx` with persisted checkboxes; browser-verified (PR #9)
- [x] 2026-07-10 — Developer onboarding & staging workflow guide (`docs/onboarding.md`); Google SSO test-user gate documented (PRs #10, #11)
- [x] 2026-07-10 — Spec audit + drift fixes across `deployment.md`, `CLAUDE.md`, `llm-integration.md` (PR #12)
- [x] 2026-07-10 — LLM provider data policy: Anthropic-only in staging/prod; Gemini/DeepSeek local-dev-only with synthetic data (`docs/fixtures/`) (PR #13)
- [x] 2026-07-10 — Anthropic structured outputs enforce JSON schemas for all agents; SDK 0.26.0 → 0.116.0 (PR #14)
- [x] 2026-07-10 — Feature 7 scheduler decision: GitHub Actions cron → authenticated `/api/admin/scan-jobs` trigger (in-process scheduler ruled out — Render spin-down) (PR #15)
- [x] 2026-07-10 — Latency targets re-scoped: cached views <1 s p95, fresh generation <60 s p95 (PR #16)
- [x] 2026-07-10 — Refresh-token revocation via `users.token_version`; migration applied to staging + local; flagged staging `DATABASE_URL` found in `backend/.env` (PR #17)
- [x] 2026-07-10 — Spec-sync rule: spec deltas ship in the same PR as the code change; known drift never merges (PR #18)
- [x] 2026-07-11 — Progress/ops hygiene: `progress.md` condensed to 2–3-line entries (narrative moved to `docs/progress-archive.md`), testing convention re-scoped to behavior coverage, Ops & Monitoring section added to `llm-integration.md` (`docs/progress-and-ops-hygiene`)
- [x] 2026-07-11 — Feature 7: job leads scanning & alerts — curated Greenhouse/Lever board scan (GitHub Actions cron → secret-gated trigger), keyword pre-filter + batched job-match agent, fit-ranked `JobLeads.jsx` with in-app new-lead badges; migration `473b757cc096` on staging + local; browser-verified (PR #20)
- [x] 2026-07-13 — Feature 8: per-posting resume + cover letter + employer brief — posting-materials agent (fit summary + tailored docs, structured outputs), SSRF-guarded posting fetch from a pasted link (JSON-LD extraction) with manual-entry fallback, `posting_materials` Mongo collection, quota-gated `/api/materials*` + `/api/leads/:id/materials` routes, `Materials.jsx` + "Tailor materials" on leads; SSRF/PII-leak review fixes + SNI fetch fix; browser-verified (PR #25)
- [x] 2026-07-14 — Intake fixes from user testing: LinkedIn upload accepts the CSVs LinkedIn's export actually produces (instructions now point at profile → More → Save to PDF), step-1 completion banner with "Continue to AI Assessment" and missing-items hints (LinkedIn optional); Feature 2 AC wording synced in `features.md`; browser-verified (PR #25)
- [x] 2026-07-15 — Architecture-review fixes: PDF/DOCX parsing moved to `document_parser_service`, cross-DB write consistency centralized in `profile_service.upsert_{resume,linkedin}_with_consistency`, PII address regex hardened for multi-word street names; new tests for orchestrator PII stripping, LLM retry/fallback, parser, and Mongo compensation (PR #21)
- [x] 2026-07-15 — Frontend data-layer test coverage: Jest `import.meta.env` transform (babel-plugin-transform-vite-meta-env, test-env only), 86 new tests across all 6 API services, all 6 hooks, and SignIn/Dashboard/Resumes pages (`test/frontend-unit-tests`)
- [x] 2026-07-15 — Playwright E2E critical path: sign-in → intake → resume upload → assessment → resume generation against `LLM_PROVIDER=mock` (no-network canned provider, local-only guard) + triple-gated `POST /auth/test-login`; new `e2e` CI job with trace artifacts; specs synced (auth-security, llm-integration, CLAUDE.md) (`feature/e2e-critical-path`)
- [x] 2026-07-15 — Typst resume PDFs (adapted from the PI's career-ops template): `resume_pdf.py` renders one-page PDFs (auto-shrinks 11pt → 9pt), PDF is now the default for `GET /api/resumes/:id/download` (`?format=docx` kept) plus `GET /api/materials/:id/resume/download`; inline Typst-rendered PNG previews (`?format=png`), no job title in the header (student name only); new dep: `typst`; browser-verified (PR #25)
- [x] 2026-07-16 — Local test-login UI: dev-build-only form on `SignIn.jsx` against the existing `POST /auth/test-login` seam, `testLogin` in `services/auth.js`, `VITE_TEST_LOGIN_SECRET` env var, README setup docs; browser-verified (`feature/local-test-login`)
- [x] 2026-07-16 — Intake required fields + collapsible sections: all questionnaire fields and all 3 ranked roles now required to save (client + `ProfileIn` schema); Resume and LinkedIn sections collapse to green-check summary cards via new `CollapsedSectionCard` (LinkedIn labeled optional); "(Beta Version)" added to the sign-in wordmark; Feature 2 ACs synced — awaiting browser verification
- [x] 2026-07-16 — Manual job-leads scan: student-triggered `POST /api/leads/scan` (single-profile `lead_service.scan_for_user`), once per rolling 24h via `users.last_lead_scan_at` (atomic consume/refund slot, migration `b8e14f6a2c97`), "Scan now" button + notices on `JobLeads.jsx`; specs synced (Feature 7 AC, API table, users table) — awaiting browser verification

---

## In Progress

_Nothing currently in progress._

---

## Blocked

| Item | Reason | Owner |
|------|--------|-------|
| Production hosting URLs | Pilot deploy targets not finalized | Project team |
| Career Center handoff details (Phase 3) | Partnership framework being defined with Dr. Gallo | PI |

---

## Up Next

- [ ] Feature 9: interview prep guidance (last Phase 2 feature)
- [ ] Before the first scheduled scan: set `SCAN_TRIGGER_SECRET` in Render and `BACKEND_URL` + `SCAN_TRIGGER_SECRET` in GitHub repository secrets (owner-managed)
- [ ] Before pilot launch: publish the Google OAuth consent screen to production (Testing mode caps sign-ins at 100 allowlisted test users — see `docs/onboarding.md` §1.2)
- [ ] Before pilot launch: stand up the daily ops check (spend/quota/error review — see `ai_specs/llm-integration.md` → Ops & Monitoring)
