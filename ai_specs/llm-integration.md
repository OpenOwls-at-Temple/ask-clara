# LLM Integration

> **OpenOwls SDD** — Read by engineers and the AI coding assistant.
> Every OpenOwls project has an LLM layer. This file defines what the LLM is responsible for,
> how it is integrated, how prompts are designed, and how the results are evaluated.
> Treat the LLM as a first-class component of the system — not an afterthought.

---

## What the LLM Does in This App

Clara uses a **multi-agent** design: specialized agents handle distinct steps of the career arc, coordinated by one server-side orchestrator.

| Responsibility | Description |
|----------------|-------------|
| Assessment (Phase 1) | Reviews a student's profile + resume against their three ranked target roles and returns strengths, gaps, and recommendations |
| Resume generation (Phase 1) | Drafts three tailored base resumes, one per ranked target role, using only the student's real experience |
| Development planning (Phase 2) | Turns an assessment into a ~6-month roadmap of specific skills, experiences, and credentials |
| Document tailoring (Phase 2) | Produces a posting-specific resume variant and matching cover letter, plus a short employer brief |
| Job matching (Phase 2) | Scores and explains why scanned postings fit a student's ranked preferences |

Each agent solves something a fixed algorithm cannot: it reasons over unstructured resume/LinkedIn text and open-ended career goals to produce individualized, natural-language guidance.

---

## Model

| Setting | Value |
|---------|-------|
| Active provider | Controlled by `LLM_PROVIDER` env var: `anthropic` (default) \| `gemini` \| `deepseek` |
| Default model | `claude-sonnet-4-6` (Anthropic), `gemini-2.5-flash` (Gemini), `deepseek-chat` (DeepSeek) |
| Why this design | Single env var swap in Render changes the provider for all agents — no code deploy needed |
| Called from | Backend service layer only (`backend/app/llm/service.py`) — never from the frontend |
| API key location | Set the key for whichever provider is active: `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, or `DEEPSEEK_API_KEY` |

**Provider notes:**
- **Anthropic `claude-sonnet-4-6`** — highest output quality; recommended for production pilot
- **Google `gemini-2.5-flash`** — free tier available; good for local dev and low-cost staging
- **DeepSeek `deepseek-chat`** — cheapest per token; OpenAI-compatible API; good cost/quality tradeoff for resume drafting

> To add a new provider: implement `_call_<provider>()` in `service.py`, add a branch in `call_llm()`, add the API key and model env vars to `config.py` and `.env.example`.

---

## Prompts

All prompts live in `backend/app/llm/prompts.py`. Never hardcode prompts in route handlers.

### Prompt 1: Profile Assessment

**Purpose:** Produce a student's strengths, gaps (relative to their ranked target roles), and concrete next-step recommendations.

**System Prompt:**
```
You are Clara, a supportive AI career coach for university STEM students.
You help undergraduate, graduate, and PhD students prepare for careers in
industry, academia, or government. You complement — never replace — human
career counselors, and you frame your advice as a starting point.

Given a student's profile and resume text, assess them against their three
ranked target roles. Identify genuine strengths, honest gaps, and specific,
actionable recommendations tailored to STEM hiring (technical skills,
projects, the internship-driven pipeline). Adjust advice to the student's
degree level and track. Be encouraging, specific, and concise. Never invent
experience the student does not have. Respond in JSON only.
```

**User Input:**
```
A JSON object with: degree_level, major_program, track, expected_graduation,
target_roles (ranked title list), and a trimmed resume_text (contact details
removed). LinkedIn summary included if available.
```

**Expected Output Format:**
```json
{
  "strengths": ["string"],
  "gaps": [{ "area": "string", "target_rank": 1, "why": "string" }],
  "recommendations": [{ "action": "string", "rationale": "string" }]
}
```

**Notes:**
- Strip contact blocks (email, phone, address) from `resume_text` before sending.
- If JSON is malformed, retry once, then return the fallback message.

---

### Prompt 2: Tailored Base Resume Generation

**Purpose:** Draft three resume versions, each oriented toward one of the student's ranked target roles.

**System Prompt:**
```
You are Clara, an AI career coach drafting resumes for a STEM student.
Produce a resume tailored to ONE target role using ONLY the experience,
education, skills, and outcomes present in the student's source material.
Re-emphasize and reorder real content to fit the role — do NOT invent
employers, titles, dates, degrees, skills, or metrics.

Writing rules for Experience and Projects bullets:
- Start every bullet with a strong active verb ("built", "led", "reduced", "improved", "designed").
- Where the source material supports it, prefer the structure: accomplished
  [outcome] as measured by [a number] by doing [the specific action]. Only
  include a number if it is genuinely present in or directly derivable from
  the source material — never estimate or invent one.
- Never write "we" — describe what the student personally did.
- Avoid clichés and filler ("team player", "fast learner", "hit the ground
  running"); replace with a specific real detail or omit the claim entirely.
- Name specific technologies, tools, or methods the student actually used,
  especially ones relevant to the target role.
- Use consistent, spelled-out date formatting ("June 2023 – August 2023", not "06/23-08/23").

Section ordering: tailor the order of "sections" to the student's degree
level and track (both given in the input). Undergraduate or master's
students with relevant experience should lead with Experience/Projects;
those with little experience should lead with Education. PhD students or
anyone on an academia track should foreground research and publications
ahead of other experience.

Emphasize technical skills, relevant projects, and quantifiable outcomes
only where they genuinely exist in the source material. Use clear, standard
resume structure. Respond in JSON only.
```

**User Input:**
```
A JSON object with the student's structured profile, parsed resume content,
optional LinkedIn content, and the single target role (title + rank) to
tailor toward. Called three times — once per ranked role.
```

**Expected Output Format:**
```json
{
  "target_rank": 1,
  "target_title": "string",
  "sections": [{ "heading": "string", "content": "string" }],
  "notes_for_student": ["string"]
}
```

**Notes:**
- Anything the model cannot ground in source material goes in `notes_for_student` as a suggestion, never into the resume body.
- Cap each section to keep output tokens bounded.
- Bullet-quality rules (active verbs, accomplished/measured-by/by-doing structure, no clichés, no "we", named technologies, consistent dates) and degree/track-based section ordering are enforced via the system prompt only — output schema and call pattern (one call per ranked role) are unchanged. Adapted from a general-purpose resume-writing prompt

---

### Prompt 3: Development Plan (Phase 2)

**Purpose:** Convert an assessment into a ~6-month roadmap.

**System Prompt:**
```
You are Clara, building a 6-month development plan for a STEM student.
Given their assessment and ranked target roles, list specific skills,
experiences, and credentials to acquire, tailored to their track (industry,
academia, or government) and degree level. Each item must name a concrete
action and why it matters for a specific target role. Respond in JSON only.
```

**User Input:**
```
The student's saved assessment plus profile and ranked target roles.
```

**Expected Output Format:**
```json
{
  "horizon_months": 6,
  "items": [{ "skill": "string", "why": "string", "target_rank": 1 }]
}
```

**Notes:**
- **Schema mapping:** the model output omits `status`. Before persisting `items` to the Postgres `development_plans.items` JSONB array, the orchestrator must inject `"status": "pending"` into each item (status vocabulary: `pending` → `complete`, per Feature 6). The model never sets or sees plan status.

---

### Prompt 4: Posting Materials — Resume Variant, Cover Letter, Employer Brief (Phase 2)

**Purpose:** Tailor materials to a specific job posting and brief the student on the employer.

**System Prompt:**
```
You are Clara, tailoring application materials for one specific job posting.
Using only the student's real record, produce: (1) a resume variant tuned to
the posting, (2) a matching cover letter, and (3) a short, factual brief on
the employer based on the posting text. Emphasize technical fit and
quantifiable outcomes that genuinely exist. Do not fabricate anything about
the student or the employer. Respond in JSON only.
```

**User Input:**
```
The student's profile and resume content plus the job posting text and link.
```

**Expected Output Format:**
```json
{
  "resume_variant": { "sections": [{ "heading": "string", "content": "string" }] },
  "cover_letter": "string",
  "employer_brief": "string"
}
```

---

## Architecture

- **Prompt definitions location:** `backend/app/llm/prompts.py`
- **LLM service location:** `backend/app/llm/service.py` (Anthropic client wrapper + retry/fallback)
- **Orchestration:** `backend/app/llm/orchestrator.py` selects the agent, assembles trimmed context, enforces the token budget
- **Called by:** route handlers in `backend/app/routes/` (e.g. `assessment.py`, `documents.py`) via the service layer
- **Frontend interaction:** frontend calls REST endpoints (e.g. `/api/assessment`) — it never calls the LLM directly

### Call Flow
```
User action (frontend)
  → API request to backend route
    → Business logic service
      → LLM orchestrator (picks agent, trims context)
        → LLM service (constructs prompt, calls Anthropic API)
          → Parse and validate JSON response
        → Persist result (Postgres/Mongo) and return structured data
    → JSON response to frontend
  → Display assessment / resume / plan to the student
```

---

## Context & Token Management

| Concern | Decision |
|---------|----------|
| Max input size | **Deterministic pre-truncation:** cap parsed experience to the ~3 most recent/relevant roles and enforce a hard input-string limit (start at ~1,500 tokens) *before* building the prompt. Do not pass raw multi-page documents and do not rely on the model to summarize them. Numbers are configurable, but truncation happens in code, not in the LLM. |
| Max output tokens | ~1,200 for resume drafts; ~600 for assessments — keep outputs bounded |
| Per-call budget awareness | Orchestrator estimates tokens before each call and logs cost; agents reuse stored assessments instead of re-running |
| What is excluded from context | Contact details (PII), unrelated past target roles, completed plan items |
| Caching | Save generated assessments/resumes so viewing them later does not re-call the model |

---

## Error Handling & Fallbacks

| Scenario | Handling |
|----------|----------|
| API timeout | Retry once after ~2s, then return a friendly fallback and let the user retry |
| Malformed JSON response | Log the raw response, retry once, then return a fallback message |
| Rate limit hit | Back off and retry after a short delay; surface a "try again shortly" message |
| Empty / unhelpful response | Return a default message (e.g. "I couldn't generate that right now — let's try again.") |
| Model attempts to fabricate | Validation step flags ungrounded employers/dates; route them to `notes_for_student`, not the document body |

---

## Privacy & Safety

- **Sent to LLM:** degree level, major/program, track, ranked target role titles, trimmed resume/LinkedIn *content* (skills, experience, projects), and job posting text.
- **Never sent to LLM:** Temple email, phone number, mailing address, session tokens, passwords, or any other direct PII; first-gen/working/commuter status.
- **Data retention:** Anthropic's API does not train on API inputs by default — verify the current policy before launch.
- **Provider data policy (student-data protection):** Staging and production always run `LLM_PROVIDER=anthropic`. Non-Anthropic providers (Gemini, DeepSeek) are permitted for **local development only** and may only ever receive **synthetic/test data** — use the fixture resume in `docs/fixtures/`, never a real student's (or your own) resume or LinkedIn content. Rationale: free-tier Gemini's terms may allow submitted data to be used for product improvement, and DeepSeek's data-handling posture has not been reviewed against this project's FERPA-aware requirements. To test locally with real personal data, use your own Anthropic key.
- **Content safety:** Uploaded text is user-generated; sanitize and bound it before sending, and never echo raw uploads into other students' contexts.

---

## Evaluation

| Metric | How to Measure | Target |
|--------|---------------|--------|
| Assessment usefulness | Manual review of 20 sampled assessments by testers/counselors | >80% rated useful |
| Resume groundedness | Manual check that drafts contain no fabricated facts | 100% (zero fabrications) |
| Response time | Logged per LLM call | <5 s p95 for assessments |
| JSON parse success rate | Logged in the service layer | >98% |
| Fallback rate | Logged when a fallback is returned | <2% |
| Cost per active student | API spend ÷ active users | Within grant budget (~$3,000 / ~500) |

---

## Prompt Iteration Log

| Date | Prompt | Change Made | Reason |
|------|--------|-------------|--------|
| 2026-06-23 | All | Initial versions | Baseline for Phase 1 build |
| YYYY-MM-DD | Prompt 2 | (planned) Add explicit "no fabrication" validator pass | Guard against invented experience in resumes |
