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
(https://ask-clara-zeta.vercel.app). Phase 2 is underway: Feature 6 (development plan) is
shipped and browser-verified; Feature 7 (job leads scanning) is in progress.

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

---

## In Progress

- [ ] Feature 7: job leads scanning & alerts (`feature/job-leads-scanning`)

---

## Blocked

| Item | Reason | Owner |
|------|--------|-------|
| Production hosting URLs | Pilot deploy targets not finalized | Project team |
| Career Center handoff details (Phase 3) | Partnership framework being defined with Dr. Gallo | PI |

---

## Up Next

- [ ] Before pilot launch: publish the Google OAuth consent screen to production (Testing mode caps sign-ins at 100 allowlisted test users — see `docs/onboarding.md` §1.2)
- [ ] Before pilot launch: stand up the daily ops check (spend/quota/error review — see `ai_specs/llm-integration.md` → Ops & Monitoring)
