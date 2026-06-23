# CLAUDE.md
> This project follows the **OpenOwls SDD (Spec-Driven Development) Process**.
> Read the files below in order before doing any work.
>
> **Project:** Clara ("Ask Clara") — an AI career coach for Temple University
> undergraduate, graduate, and PhD students.

## Session Startup — Read These First

1. **`progress.md`** (project root) — catch up on what has been done, what is in progress, and what is blocked
2. **`ai_specs/overview.md`** — understand the project goals, stakeholders, and tech stack
3. **`ai_specs/features.md`** — understand the full feature scope and which phase we are currently in
4. **`ai_specs/architecture-planning.md`** — understand folder structure, design decisions, and implementation details
5. **`ai_specs/domain-knowledge.md`** — understand domain-specific concepts and constraints
6. **`ai_specs/llm-integration.md`** — understand the LLM's role, model choice, prompt design, context strategy, and guardrails
7. **`ai_specs/conventions.md`** — follow all coding conventions, naming rules, and workflow standards without exception
8. **`ai_specs/auth-security.md`** — understand the user model, identity strategy, authentication, authorization, data protection, and threats
9. **`ai_specs/deployment.md`** — understand hosting platforms, environment variables, and deployment process

## General Instructions

- Always work within the current phase defined in `ai_specs/features.md`. Do not implement features from a future phase unless explicitly instructed.
- After completing any meaningful unit of work, update `progress.md` to reflect what was done.
- If you encounter a conflict between these spec files, flag it to the user before proceeding.
- If a spec file is missing a detail you need, ask the user rather than assuming.
- Never delete or overwrite any file in `ai_specs/` without explicit instruction.

## Clara-Specific Guardrails

- Never call the LLM from the frontend — all agents run server-side in `backend/app/llm/`.
- Never send PII (Temple email, phone, address) or self-reported first-gen/working/commuter status to the LLM.
- Never fabricate a student's experience in generated resumes or cover letters.
- Clara complements the Temple Career Center — never frame it as a replacement in user-facing copy.
