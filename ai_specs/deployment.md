# Deployment

> **OpenOwls SDD** — Read by engineers and DevOps-minded team members.
> Defines how the application is built, configured, and deployed across environments.
> Claude Code uses this file to understand deployment targets and avoid environment-specific mistakes.

---

## Environments

| Environment | Purpose | URL |
|-------------|---------|-----|
| Local | Development and testing on your own machine | `http://localhost:5173` |
| Staging | Pre-production testing, shared with the team | `https://ask-clara-zeta.vercel.app` (live since 2026-06-26) |
| Production | Live pilot for CST students | `https://clara.vercel.app` (TBD) |

---

## Hosting Platforms

| Component | Platform | Tier | Notes |
|-----------|----------|------|-------|
| Frontend | Vercel | Free | Auto-deploys from `main` |
| Backend | Render | Free / low-cost | Spins down after inactivity on free tier; consider paid for pilot reliability |
| Relational DB | Supabase (PostgreSQL) | Free | 500MB limit on free tier |
| Document DB | MongoDB Atlas | Free (M0) | For resumes and generated documents |
| File handling | Parsed server-side; raw files not persisted long-term | — | Keep storage minimal for the pilot |

---

## Environment Variables

### Backend
| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | Yes | Active LLM provider: `anthropic` (default), `gemini`, or `deepseek` (see `llm-integration.md`) |
| `ANTHROPIC_API_KEY` | When `LLM_PROVIDER=anthropic` | Anthropic API key for LLM agents |
| `ANTHROPIC_MODEL` | No | Anthropic model ID (default `claude-sonnet-4-6`) |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | When `LLM_PROVIDER=gemini` | Gemini API key and model (default `gemini-2.5-flash`) |
| `DEEPSEEK_API_KEY` / `DEEPSEEK_MODEL` | When `LLM_PROVIDER=deepseek` | DeepSeek API key and model (default `deepseek-chat`) |
| `FRONTEND_ORIGIN` | Yes | Frontend origin allowed by CORS (e.g. `http://localhost:5173` locally, the Vercel URL on staging) |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `MONGODB_URI` | Yes | MongoDB Atlas connection string |
| `GOOGLE_CLIENT_ID` | Yes | Google SSO client ID |
| `GOOGLE_CLIENT_SECRET` | Yes | Google SSO client secret |
| `JWT_SECRET` | Yes | Secret for signing session tokens |
| `ALLOWED_EMAIL_DOMAIN` | Yes | Restrict sign-in (e.g. `temple.edu`) |
| `ENVIRONMENT` | Yes | `local`, `staging`, or `production` |
| `SCAN_TRIGGER_SECRET` | Phase 2 | Shared secret for the GitHub Actions job-scan trigger — set the same value in Render and in GitHub Actions secrets (see `architecture-planning.md` → Key Design Decisions) |

### Frontend
| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | Yes | Base URL of the backend API |
| `VITE_GOOGLE_CLIENT_ID` | Yes | Google SSO client ID (public) |

> ⚠️ Never commit `.env` files. Add them to `.gitignore`. Keep a `.env.example` with dummy values checked in.

---

## Local Development Setup

**The authoritative local setup guide is `docs/onboarding.md` §2** — it covers the Docker Compose databases (Postgres 15 + MongoDB 6), `.env` values, Alembic migrations, and setup verification. This section is intentionally not duplicated here to avoid drift.

Quick reference only:

- Prerequisites: Python 3.11+, Node 20+, Docker Desktop, a `@temple.edu` Google account.
- LLM key: **use your own personal key** — Anthropic (`LLM_PROVIDER=anthropic`, paid) or a free-tier Gemini key (`LLM_PROVIDER=gemini`). Never use the shared grant-funded key locally. (Anthropic has no free API tier.)
- Google OAuth client ID + secret: shared privately by the project owner (see `docs/onboarding.md` §1).

---

## Deployment Process

### Frontend (Vercel)
1. Push to `main` — Vercel auto-deploys.
2. Set environment variables in the Vercel dashboard under *Settings → Environment Variables*.
3. Check deployment status at `https://vercel.com/dashboard`.
4. **API proxying (cookie origin fix):** The frontend (Vercel) and backend (Render) live on different origins, which makes the `httpOnly` refresh cookie a third-party cookie — increasingly blocked by browsers. To keep the cookie first-party, add a `vercel.json` in the frontend root that rewrites `/api/(.*)` to the Render backend:
   ```json
   {
     "rewrites": [
       { "source": "/api/:path*", "destination": "https://[your-render-backend-url]/api/:path*" }
     ]
   }
   ```
   The frontend then calls `/api/...` on its own domain and Vercel proxies to Render, so the backend's cookie stays first-party. Set the cookie host-only (no explicit `Domain`) and `SameSite=Lax`. With the proxy in place, `VITE_API_BASE_URL` should point at the frontend's own origin (`/api`), not the Render URL directly.

   > ⚠️ Vercel rewrites have a proxy response timeout. Long LLM generations (e.g. resume drafting) can exceed it. If they do, stream the response or move generation to a job + polling pattern rather than a single long request.

### Backend (Render)
1. Push to `main` — Render auto-deploys.
2. Set environment variables in the Render dashboard under *Environment*.
3. First deploy may take 3–5 minutes.
4. Check logs at `https://dashboard.render.com`.

### Databases
1. **Postgres (Supabase):** run migrations manually — `python -m alembic upgrade head`. Never edit the production schema directly; test migrations on staging first.
2. **MongoDB (Atlas):** collections are created on first write; index `user_id` on each collection.

---

## CI/CD Pipeline

GitHub Actions runs on every pull request:
- Linting (`black`, `eslint`)
- Unit tests (`pytest`, `jest`) — LLM calls are mocked
- Build check

Merging to `main` triggers automatic deployment to staging. Production deploys are manual and require faculty (PI) approval.

---

## Common Deployment Issues

| Issue | Likely Cause | Fix |
|-------|-------------|-----|
| Backend 500 on first request | Missing environment variable | Check Render logs; verify all env vars are set |
| Frontend can't reach backend | Wrong `VITE_API_BASE_URL` | Confirm the backend URL in Vercel env vars |
| Postgres connection fails | `DATABASE_URL` format incorrect | Use the connection string from the Supabase dashboard |
| Mongo writes fail | Bad `MONGODB_URI` or IP allowlist | Verify the Atlas URI and allow the backend's egress IP |
| SSO rejected | Domain restriction or wrong client ID | Confirm `ALLOWED_EMAIL_DOMAIN` and Google client config |
| Unexpected LLM cost spike | Oversized context per call | Check token logging; trim context per `llm-integration.md` |

---

## Secrets Management

- All secrets live in the hosting platform's environment variable settings, never in code.
- Rotate `JWT_SECRET`, `ANTHROPIC_API_KEY`, and the Google secret if ever committed accidentally.
- Each environment (local, staging, production) uses its own separate API keys and databases.
- Students use their own personal LLM keys (Anthropic or free-tier Gemini) for local development.
