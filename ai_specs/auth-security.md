# Authentication & Security

> **OpenOwls SDD** — Read by engineers and the AI coding assistant.
> Defines how users are authenticated and authorized, how sensitive data is protected,
> and what security rules apply across the project. Security is a design concern, not a
> last-minute checklist — document these decisions before writing auth code.

---

## User Model & Scale

| Question | Decision |
|----------|----------|
| Expected number of users | ~500 pilot accounts (CST), with ~200 active; design for hundreds, not millions |
| Growth expectation | Roughly flat per pilot; possible university-wide expansion later |
| User model | Multi-user, single-tenant — all users share one application instance |
| Do users belong to groups? | Loosely — students have a degree level and program; counselors form a small reviewer group |
| Anonymous / guest access? | No — every action requires a signed-in Temple account |

---

## Identity Strategy

| Setting | Decision |
|---------|----------|
| Approach | Third-party OAuth (Google SSO) |
| Why this approach | "Sign in with Google" avoids storing passwords and fits a university audience that already has Temple Google accounts |
| Identity provider(s) | Google Workspace SSO, restricted to `@temple.edu` accounts |
| Fallback / alternative | None for the pilot — Google SSO only |

---

## Authentication Method

| Setting | Value |
|---------|-------|
| Method | Google SSO establishes identity; the backend issues a short-lived signed session (JWT) |
| Why this method | Stateless, simple to reason about, works well with a React SPA and avoids password storage |
| Token storage (client) | In-memory access token + httpOnly refresh cookie — never `localStorage`. Frontend and backend are served from one origin via a Vercel `/api` proxy so the cookie stays first-party (see `deployment.md`). |
| Token lifetime | Access ~15 min; refresh ~7 days |
| Password hashing | N/A (no passwords stored — SSO only) |

---

## Authorization & Roles

| Role | Permissions |
|------|-------------|
| Student | Create/read/update/delete **only their own** profile, documents, assessments, plans, and leads |
| Counselor | View a student's shared summary **only after the student consents to a handoff**; add review notes |
| Admin (project team) | Manage accounts, view aggregate usage and LLM quality metrics; no casual browsing of student documents |

- **Enforcement point:** authorization is checked server-side on every protected route — ownership is re-verified per record, never trusted from the frontend.
- **Default posture:** deny by default — a route is private unless explicitly marked public.

---

## User Lifecycle & Management

| Stage | Decision |
|-------|----------|
| Account creation | Self-signup via Google SSO; restricted to `@temple.edu` |
| Onboarding | New users land on profile intake (resume + LinkedIn + questionnaire) |
| Password reset | N/A — SSO only |
| Account recovery | Handled by Google SSO; locked-out users recover through Temple Google |
| Profile updates | Students can edit profile and ranked roles anytime |
| Deactivation / deletion | Soft-delete by default (disable login, retain records); explicit purge path on request removes documents and PII |
| Who administers users | The project team (PI + RA) holds the admin role |

---

## Sensitive Data

| Data | Classification | Protection |
|------|---------------|------------|
| Temple email | PII | Access-controlled; never sent to the LLM; not returned in unrelated responses |
| Resume / LinkedIn content | Sensitive personal | Stored in MongoDB with access control; contact blocks stripped before any LLM call |
| Academic history & career goals | Sensitive personal | Owner-only access; never shared without consent |
| First-gen / working / commuter status | Sensitive, self-reported | Optional; never required, never sent to the LLM, never used to gate access |
| Session tokens | Secret | httpOnly cookie; never logged; never in client storage |
| `ANTHROPIC_API_KEY`, `JWT_SECRET` | Secret | Environment variables only; never in code or frontend |

---

## Secrets Management

- All secrets live in environment variables, never in committed code.
- `.env` files are git-ignored; a `.env.example` with dummy values is checked in.
- Each environment (local, staging, production) uses separate secrets and its own API key/database.
- Rotate any secret immediately if it is accidentally committed.

---

## Common Web Vulnerabilities

| Threat | Mitigation |
|--------|------------|
| SQL injection | Use the ORM / parameterized queries only — never string-concatenate SQL |
| NoSQL injection | Validate and type-check all inputs before building MongoDB queries; never pass raw user objects into queries |
| Cross-site scripting (XSS) | Escape all user-generated content; rely on React's default escaping; sanitize resume text before render |
| Cross-site request forgery (CSRF) | SameSite cookies + CSRF token on state-changing requests |
| Broken access control | Re-check record ownership on every access, not just on list views |
| Sensitive data exposure | Enforce HTTPS everywhere; never return secrets or other students' data |
| File upload abuse | Validate file type/size on upload; parse in a constrained way; never execute uploaded content |

---

## Input Validation

- Validate and sanitize every input on the server, even when the frontend already validates.
- Use Pydantic schemas to validate request bodies in FastAPI.
- Enforce length limits, file-size/type limits on uploads, and reject unexpected fields.
- Treat all uploaded resume/LinkedIn text as untrusted before parsing or sending to the LLM.

---

## Session & Account Safety

- Invalidate the refresh token on logout — implemented via token versioning: each refresh JWT carries the `users.token_version` it was minted with (`tv` claim); logout increments the column, so every outstanding refresh token for that user (including stolen copies) fails the version check on `/refresh` with a 401. Clearing the cookie alone is not revocation.
- Rate-limit expensive endpoints (uploads, LLM generation) per user.
- Re-verify identity through SSO for sensitive account changes.
- **Hard LLM quotas (budget protection):** time-based rate limits alone do not protect a fixed grant budget from a compromised account scripting requests. Enforce a **database-backed lifetime cap** per user via the `users.llm_generation_count` column (e.g. a configurable max such as 20 resume generations). Check and increment it **atomically** (an `UPDATE ... WHERE llm_generation_count < :cap RETURNING ...` or a row lock) so concurrent requests cannot both pass the check, and reject over-quota requests at the FastAPI layer before any model call. As defense in depth, also keep a **global/aggregate budget guard** (e.g. a daily spend ceiling) that pauses generation for everyone if total spend nears the grant limit.

---

## Security Checklist Before Deploy

- [ ] No secrets in the repository or in frontend code
- [ ] All protected routes enforce authentication and per-record ownership server-side
- [ ] HTTPS enforced in staging and production
- [ ] No passwords stored anywhere (SSO only)
- [ ] PII and self-reported status never sent to the LLM
- [ ] Dependencies checked for known vulnerabilities
- [ ] Error messages do not leak stack traces or internal details

---

## What Claude Code Should Never Do

- Never store secrets, tokens, or keys in client-side code or in the repository.
- Never disable authentication or authorization checks "temporarily" to make a feature work.
- Never log emails, tokens, PII, or raw resume content.
- Never trust input from the client without server-side validation.
- Never send PII or first-gen/working/commuter status to the LLM.
