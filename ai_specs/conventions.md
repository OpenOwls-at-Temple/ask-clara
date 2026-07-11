# Conventions

> **OpenOwls SDD** — Read by engineers and the AI coding assistant.
> Defines how code is written on this project. These rules apply to every file, every session.
> Claude Code must follow these conventions without being reminded each time.

---

## Language & Framework Versions

| Technology | Version |
|------------|---------|
| Python | 3.11+ |
| Node.js | 20+ |
| React | 18+ |
| FastAPI | 0.110+ |
| SQLAlchemy | 2.0+ |
| PostgreSQL | 15+ |
| MongoDB | 6+ |
| Anthropic SDK (Python) | latest stable |

---

## Naming Conventions

| Context | Convention | Example |
|---------|------------|---------|
| Python variables & functions | `snake_case` | `generate_tailored_resumes()` |
| Python classes | `PascalCase` | `AssessmentService` |
| React components | `PascalCase` | `ResumeViewer.jsx` |
| React hooks | `camelCase` prefixed with `use` | `useProfile` |
| CSS classes | `kebab-case` | `assessment-panel` |
| Postgres tables | `snake_case`, plural | `target_roles` |
| MongoDB collections | `snake_case`, plural | `assessments` |
| Environment variables | `UPPER_SNAKE_CASE` | `ANTHROPIC_API_KEY` |
| Git branches | `type/short-description` | `feature/resume-generation` |

---

## File & Folder Conventions

- One component per file in React; file name matches the component name exactly.
- Tests live in a dedicated `tests/` folder mirroring the source layout.
- API route files are named after the resource they handle (`assessment.py`, `documents.py`, `leads.py`).
- **All prompts live only in `backend/app/llm/prompts.py`** — agents and routes import them, never redefine them.

---

## Code Style

- **Python:** Follow PEP 8. Use `black` for formatting.
- **JavaScript:** Follow ESLint recommended rules. Use `prettier` for formatting.
- Maximum line length: 100 characters.
- No commented-out code in commits — delete it or leave a `TODO:` with an explanation.
- No `console.log` or stray `print()` in production code.

---

## Git Conventions

- Commit messages: `type: short description` (types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`). Example: `feat: add ranked target roles to profile`.
- Every feature on its own branch; no direct commits to `main`.
- Pull requests require at least one review before merging.

---

## Testing Conventions

- Every route and service **behavior** has a test; ownership/authorization paths (a student must never see or modify another student's data) are **always** tested. Trivial helpers don't need dedicated tests — cover behaviors, not function counts.
- Tests must pass before any PR merges.
- Test naming: `test_[module].py` (Python) / `[module].test.js` (JS).
- Use descriptive names: `test_student_cannot_see_other_students_assessment`.
- LLM calls are **mocked** in unit tests — never hit the real Anthropic API in CI.

---

## LLM / AI Conventions

- All prompts are defined in `backend/app/llm/prompts.py` — never inline in routes or agents.
- Every LLM call goes through the service wrapper and has error handling plus a fallback response.
- Never send PII (Temple email, phone, address) or self-reported first-gen/working/commuter status to the model.
- Validate and parse model output before using it; on malformed output, retry once then fall back.
- Cache generated assessments/resumes; do not re-call the model to re-display existing results.
- Resume/cover-letter output must be grounded in the student's real record — code should route ungrounded content to "notes for student," not into documents.

---

## What Claude Code Should Never Do

- Never merge known spec/code drift: when a code change makes a statement in `ai_specs/` inaccurate, sync the spec in the same PR and call out the spec delta in the PR description. Deleting or wholesale-rewriting a spec file still requires explicit instruction.
- Never skip writing tests to save time.
- Never use a library not already in `requirements.txt` or `package.json` without asking first.
- Never expose environment variables or the Anthropic key in frontend code.
- Never call the LLM directly from the frontend.
- Never fabricate student experience in generated materials.
