# Clara — Developer Onboarding & Staging Workflow

> Audience: new developers joining the Clara project (students, RAs, collaborators).
> Owner: project team (PI + RA). Keep this document updated when the process changes.
>
> This document covers **how to get access, set up locally, test, and ship to staging**.
> It complements — does not replace — the spec files in `ai_specs/`, which define *what*
> to build and *how* to write code.

---

## 0. Read These First

Before writing any code, read in this order:

1. `CLAUDE.md` — project rules and dev commands (also the entry point for AI-assisted sessions)
2. `progress.md` — current phase, what's done, what's in progress, what's blocked
3. `ai_specs/` — all nine spec files, especially `conventions.md` (coding standards),
   `architecture-planning.md` (folder structure), and `llm-integration.md` (LLM rules)

The project follows the **OpenOwls SDD process**: specs drive implementation, `progress.md`
is updated after every meaningful unit of work, and nobody implements features from a
future phase without agreement.

---

## 1. Getting Access

Most day-to-day development needs **only GitHub access plus local credentials** — deploys
are git-driven, so you do not need hosting-dashboard logins to contribute.

| What | Who needs it | How to get it |
|------|-------------|---------------|
| GitHub repo (`OpenOwls-at-Temple/ask-clara`) | Everyone | Org/repo invite from the project owner. Write access; all changes go through PRs |
| Google OAuth **client ID** (public value) | Everyone (local `.env`) | Ask the project owner. `http://localhost:5173` is an authorized origin on the shared test client |
| Google OAuth **client secret** | Everyone (backend local `.env`) | Shared privately by the project owner — never committed, never posted in chat |
| An LLM API key for local dev | Everyone | **Use your own personal key.** Anthropic (`LLM_PROVIDER=anthropic`) or a free-tier Gemini key (`LLM_PROVIDER=gemini`) — the backend supports both. Never use the shared grant-funded key locally |
| A `@temple.edu` Google account | Everyone | Sign-in is domain-restricted (`ALLOWED_EMAIL_DOMAIN=temple.edu`); you sign into the app with your own Temple account |
| Supabase staging connection string (session mode, port 5432) | Only whoever runs staging migrations | Shared privately by the project owner, per-task |
| Supabase / MongoDB Atlas / Vercel / Render dashboards | Owner + at most 1–2 maintainers | Dashboard invites where the plan allows (see §1.1) |

### 1.1 Hosting dashboards — who actually needs them

The four hosting accounts (Supabase, Atlas, Vercel, Render) are currently personal accounts
held by the project owner. Because **merging to `main` is what deploys** (Vercel and Render
auto-deploy from GitHub), regular contributors never need those dashboards. Dashboards are
only needed to:

- change environment variables (Render/Vercel)
- read production/staging logs (Render)
- browse data (Supabase table editor, Atlas collections)
- manage database users / connection strings

Recommended setup, in order of preference:

1. **Invite maintainers as members** where the current plan supports it (Supabase
   organizations and Atlas projects support member invites; check the current plan limits
   for Vercel and Render — free personal plans may not support additional members).
2. Where member invites aren't available on the current plan, keep the dashboard
   **owner-only** and route requests (env var changes, log pulls) through the owner.
3. **Never share account passwords.** If a service must be co-managed and can't do invites,
   that's a signal to upgrade the plan or migrate to a team/org account.

Store all shared secrets (client secret, staging connection strings, JWT secret) in a
password manager vault shared with maintainers only — never in the repo, never in Slack/Discord
history, never in screenshots.

---

## 2. Local Environment Setup

Prerequisites: **Python 3.11+**, **Node 20+**, **Docker Desktop**, and a Google account.

```bash
# 1. Clone
git clone https://github.com/OpenOwls-at-Temple/ask-clara.git
cd ask-clara

# 2. Start local databases (Postgres 15 + MongoDB 6 in Docker)
docker compose up -d

# 3. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in real values — see below
python -m alembic upgrade head   # create/upgrade the local schema
python -m uvicorn app.main:app --reload    # http://localhost:8000 (docs at /docs)

# 4. Frontend (new terminal)
cd frontend
npm install
cp .env.example .env          # then fill in real values — see below
npm run dev                   # http://localhost:5173
```

### `.env` values to fill in

**backend/.env** — the defaults for `DATABASE_URL` and `MONGODB_URI` already match the
Docker containers; you only need to set:

- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — from the project owner
- `JWT_SECRET` — any long random string for local use
- `LLM_PROVIDER` + the matching key (`ANTHROPIC_API_KEY` or `GEMINI_API_KEY`) — your own key
- Leave `ENVIRONMENT=local` (this enables the effectively-unlimited local LLM quota and
  local CORS)

**frontend/.env**:

- `VITE_API_BASE_URL=/api` (the Vite dev server proxies `/api` to `localhost:8000`)
- `VITE_GOOGLE_CLIENT_ID` — same client ID as the backend

### Verify your setup

1. `http://localhost:8000/docs` loads the API docs.
2. `http://localhost:5173` loads the sign-in page; sign in with your `@temple.edu` account.
3. Complete intake, upload a resume, and run an assessment — this exercises Postgres,
   MongoDB, and your LLM key end-to-end.

---

## 3. Testing & Quality Gates

Run everything locally before opening a PR — CI runs the same commands and must be green.

```bash
# Backend (requires docker compose databases to be running —
# integration tests use the local Postgres in rolled-back transactions)
cd backend
pytest                        # full suite
pytest -k "test_name"         # one test
black app/ tests/             # format (CI runs black --check app/)

# Frontend
cd frontend
npm test                      # Jest suite
npx eslint src/ --max-warnings=0   # CI fails on any warning
npx prettier --write src/
```

Non-negotiable testing rules (from `ai_specs/conventions.md`):

- Every backend function gets at least one unit test.
- **LLM calls are always mocked in tests** — never hit a real model API in tests or CI.
- Ownership/authorization paths get explicit tests (e.g. "student cannot see another
  student's data").

Manual testing: after implementing any feature that touches both backend and frontend,
do a full browser pass locally (sign in → exercise the feature → refresh to confirm
persistence) before opening the PR.

---

## 4. Development Workflow

1. **Branch** from `main`: `type/short-description` (`feature/job-leads`, `fix/quota-refund`,
   `docs/onboarding`). Never commit directly to `main`.
2. **Implement** within the current phase (`progress.md`) and per `ai_specs/conventions.md`.
3. **Test + lint** locally (§3).
4. **Update `progress.md`** — completed entry, session log row.
5. **Open a PR** to `main`. GitHub Actions runs backend (black + pytest against service
   containers, with migrations applied) and frontend (eslint + jest) jobs.
6. **One review minimum** before merge. CI must be green.
7. **Merging to `main` deploys to staging automatically** (Vercel + Render). If your PR
   includes a database migration, follow §5 *before* merging.

---

## 5. Database Changes & Migrations

Postgres schema changes go through **Alembic** — never edit a schema by hand, in any
environment. Alembic tracks each database's current revision in its `alembic_version` table.

### Local (while developing)

```bash
cd backend
# 1. Change/add SQLAlchemy models (backend/app/models/) and register any new
#    model module in alembic/env.py imports so autogenerate can see it
# 2. Generate the migration
python -m alembic revision --autogenerate -m "describe change"
# 3. Review the generated file in alembic/versions/ — autogenerate is a draft, not gospel
# 4. Apply and test locally
python -m alembic upgrade head
pytest
```

### Staging (Supabase) — run **before** merging the PR

Render does **not** run migrations on deploy. You apply them manually, and the order
matters:

1. **Prefer additive changes** (new tables, new nullable columns). Additive migrations are
   safe to apply while the *old* code is still deployed, which is what makes this
   migrate-then-merge order work. If a change is destructive (dropping/renaming a column
   that deployed code still uses), stop and coordinate with the project owner — it needs a
   multi-step expand/contract rollout.
2. Get the **staging Supabase connection string** from the project owner. Use the
   **direct / session-mode string (port 5432)** — not the transaction pooler (port 6543),
   which can fail on DDL with asyncpg.
3. Apply and verify:
   ```bash
   cd backend
   DATABASE_URL="<staging-session-connection-string>" python -m alembic upgrade head
   DATABASE_URL="<staging-session-connection-string>" python -m alembic current
   # should print your new revision id
   ```
   Optionally confirm the table/column in the Supabase dashboard.
4. **Now merge the PR.** The auto-deployed code finds the schema already in place — no
   window where new endpoints 500.
5. If something goes wrong, additive migrations roll back cleanly:
   ```bash
   DATABASE_URL="<staging-session-connection-string>" python -m alembic downgrade -1
   ```

MongoDB needs no migration step — collections are created on first write. If you add a
**new collection**, register a `user_id` index for it in the startup hook in
`backend/app/main.py` (see the existing `create_index` calls).

### Production

Same pattern, but production deploys are **manual and require PI approval**
(`ai_specs/deployment.md`). Migrations are always proven on staging first, then applied to
the production Supabase with the same commands and the production connection string.

---

## 6. Staging Deployment & Smoke Test

### What happens on merge to `main`

| Component | Platform | Trigger | Notes |
|-----------|----------|---------|-------|
| Frontend | Vercel | Auto on push to `main` | `frontend/vercel.json` rewrites `/api/*` to the Render backend so the auth cookie stays first-party |
| Backend | Render | Auto on push to `main` | `render.yaml` defines the service; secrets (`sync: false`) are set in the Render dashboard |
| Postgres | Supabase | **Manual** (§5) | Never auto-migrated |
| MongoDB | Atlas | Nothing to do | Collections/indexes created by app startup |

Staging URL: **https://ask-clara-zeta.vercel.app**

New environment variables are a **manual, owner-side step**: add them to `render.yaml`
(with `sync: false` for secrets) and set the value in the Render dashboard *before* merging
code that requires them. Same for Vercel env vars.

### Post-deploy smoke test (run after every staging deploy)

1. Sign in with a Temple Google account.
2. Dashboard loads with correct profile status.
3. Intake: profile loads pre-filled; save an edit; re-load.
4. Assessment: cached assessment displays **without** a new LLM call; run a fresh one if
   the deploy touched the LLM layer.
5. Resumes: cached drafts display; download a DOCX.
6. Plan: cached plan displays; toggle an item complete and refresh to confirm persistence.
7. Anything the deploy specifically changed.

Watch out for: Render free tier spins down when idle (first request after a while is slow —
retry, don't panic); long LLM generations can hit the Vercel proxy timeout (see
`ai_specs/deployment.md`).

### Rolling back staging

- **Code:** Vercel and Render both support one-click rollback to the previous deploy from
  their dashboards (owner task). Reverting the merge commit on `main` also redeploys.
- **Schema:** `alembic downgrade -1` against staging (only safe for additive migrations —
  coordinate first if data was written to the new structures).

---

## 7. Onboarding Checklists

### For the project owner (per new developer)

- [ ] Invite to the GitHub org/repo with write access
- [ ] Confirm branch protection on `main`: require PRs, ≥1 review, CI green (Settings → Branches)
- [ ] Share via password manager / private channel: Google client ID + secret
- [ ] Confirm they have (or help them create) a personal Anthropic or Gemini API key
- [ ] Add them to the shared secrets vault if they'll be a maintainer
- [ ] If they'll run staging migrations: share the Supabase session-mode connection string
- [ ] Point them at this document and the §0 reading list

### For the new developer (first day)

- [ ] Read §0 documents in order
- [ ] Complete §2 local setup; verify sign-in and an end-to-end assessment locally
- [ ] Run the full test suites (§3) and confirm everything passes untouched
- [ ] Make a trivial branch + PR (e.g. fix a typo) to walk the full workflow once
- [ ] Read the security rules in `ai_specs/auth-security.md` — especially: never commit
      secrets, never log PII, never send PII to the LLM
