# Domain Knowledge

> **OpenOwls SDD** — Read primarily by the AI coding assistant.
> Captures domain-specific concepts, terminology, business rules, and constraints
> that are not obvious from the code itself. Faculty seeds this file; students expand it.

---

## Domain Overview

Clara operates in the **career development and early-career recruiting** domain, specifically for university STEM students. The work follows a structured development arc: self-assessment → skill/credential building → tailored application materials → job matching → application → interview. Clara's distinctive stance is that it is a *persistent mentor* that tracks a student over time, not a transactional one-shot resume tool, and that it *complements* the Temple Career Center rather than replacing it.

---

## Key Concepts & Terminology

| Term | Definition |
|------|------------|
| Profile | A student's persisted academic history, experiences, target roles, and uploaded documents |
| Target role ("dream job") | One of three career roles a student ranks 1–3 by preference; drives assessment and tailoring |
| Degree level | `undergrad`, `grad`, or `phd` — changes the advice (e.g., PhDs may target academia/research) |
| Track | The student's intended sector: industry, academia, or government |
| Assessment | Clara's review of a profile producing strengths, gaps, and recommendations |
| Development plan | A ~6-month roadmap of specific skills, experiences, and credentials to acquire |
| Job lead | A scanned posting matched to a student's preferences, stored with its original link and a fit reason |
| Agent | A specialized LLM role (assessment, planning, document generation, job matching) coordinated by the orchestrator |
| Handoff | Sharing a student's Clara summary with a Temple counselor, with the student's consent |
| First-generation student | A student whose parents did not complete a four-year degree; a prioritized-outreach group, self-reported and never required |
| CST | Temple's College of Science and Technology — the pilot population |

---

## Business Rules

- A student can only ever see and act on **their own** profile, documents, assessments, and leads.
- Generated resumes and cover letters must reflect the student's **real** record — Clara must never fabricate employers, degrees, dates, titles, skills, or metrics.
- The "dream job" question always captures **exactly three** target roles, each with a distinct rank (1, 2, 3).
- Advice must be **tailored to STEM career paths** and to the student's degree level and track — not generic.
- Clara **augments** the Career Center; outputs are framed as a starting point that a human counselor can review, never as final authority.
- Application submission (Phase 3) **always** requires an explicit human approval step — Clara never submits silently.
- Job scanning must respect source sites' terms of service and must not bypass paywalls or logins.
- First-generation / working / commuter status is optional and self-reported; it may guide outreach and tone but must never gate access or be required.

---

## Domain Constraints

- The LLM operates on a real grant-funded token budget (~$3,000 across ~500 students) — context sent per call must be trimmed to what each agent needs (see `llm-integration.md`).
- Resume and LinkedIn text can be long; cap and summarize before sending to the model rather than passing entire raw documents repeatedly.
- All dates stored in UTC; displayed in the user's local timezone.
- Degree level meaningfully changes advice: undergrads → internships and first roles; grad students → specialized roles; PhDs → academic, research, or senior industry tracks.
- The pilot targets ~500 accounts with ~200 active — design for hundreds, not millions.

---

## Common Pitfalls

- Don't confuse **rank** (student-assigned preference of a target role) with **fit_score** (LLM-inferred match of a job lead).
- Don't treat all students as undergrads — branch advice on `degree_level` and `track`.
- Don't let the model invent achievements to make a resume look stronger; tailoring means re-emphasizing real content, not inventing it.
- Don't send raw PII (full email, phone, address) into prompts — strip contact blocks before model calls.
- Don't hard-delete student records on request without considering the retention/handoff implications; prefer soft-delete plus an explicit purge path.
- Don't position Clara as a replacement for counselors in any user-facing copy.

---

## External Dependencies & Integrations

| Service | Purpose | Notes |
|---------|---------|-------|
| Anthropic API | All LLM agents (assessment, planning, documents, matching) | Watch rate limits and per-call token cost against the grant budget |
| Google Workspace SSO | `@temple.edu` identity | University audience; avoids password storage |
| Temple Career Center | Counselor review and student handoff | Partnership framework defined with Dr. Gallo |
| Job posting sources (Phase 2) | Job leads scanning | Respect ToS; store original links, never republish full postings |

---

## References

- [Anthropic API Docs](https://docs.anthropic.com)
- Ask Clara — CST Innovation Initiative Fund Proposal (Dr. Alex Pang), project source of record
- Temple University Career Center services (counselor best practices via Dr. Gallo)
