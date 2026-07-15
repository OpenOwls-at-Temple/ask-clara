# Overview

> **OpenOwls SDD** — Read by the business sponsor and the full team.
> Describes the project at a high level: what it is, why it exists, who it is for, and what technology it uses.

---

## Project Name

**Clara** ("Ask Clara") — an AI career coach for Temple University students.

## One-Line Description

A virtual AI career coach that helps Temple University undergraduate, graduate, and PhD students move from self-assessment to job application by giving persistent, personalized, always-available career guidance.

---

## Problem Statement

First-generation college students and those from underserved backgrounds face a well-documented disadvantage in career preparation. Their peers benefit from family professional networks, mentorship, and inherited knowledge about navigating recruitment, while first-generation, working, and commuter students often lack access to those resources — a gap that persists even when academic performance is equal, and that shows up later as lower employment rates and lower starting salaries. Private career coaching exists, but it is expensive.

Temple's Career Center offers excellent free services, yet many students under-utilize them because of limited awareness, scheduling conflicts, discomfort asking for help, or competing priorities. Clara does not replace those services — it lowers the barrier to using them. It gives students a low-pressure, low-cost, always-available starting point that builds confidence and prepares them to engage more effectively with human counselors.

---

## Goals

- Ship a functional Clara prototype that CST students can sign in to and use end-to-end (profile → assessment → tailored resumes).
- Create 500 student accounts during the pilot, with at least 200 active users completing an initial assessment.
- Produce assessment feedback and tailored application materials that testers rate as useful (>80% positive on sampled outputs).
- Establish a documented partnership framework with the Temple Career Center so AI-generated advice can be reviewed by professionals and students can be handed off to human counselors.
- Collect structured user feedback to guide future development and potential university-wide expansion.

## Non-Goals

- Clara does **not** replace human career counselors; it prepares students to use them.
- Clara does **not** autonomously submit job applications in Phase 1 or Phase 2 (deferred to Phase 3, and only with explicit user approval).
- Clara is **not** a job board or applicant tracking system — it complements existing tools rather than rebuilding them.
- No native mobile app in the pilot (responsive web only).
- No guaranteed outcomes (interviews, offers, salaries) are promised to students.

---

## Target Users

| User Type | Description |
|-----------|-------------|
| Primary User | A Temple University student — undergraduate, graduate, or PhD — preparing for internships, jobs, or post-graduate roles in industry, academia, or government. The pilot prioritizes CST (College of Science and Technology) seniors, with priority outreach to first-generation, working, and commuter students. |
| Secondary User | A Temple Career Center counselor who reviews AI-generated advice, receives student handoffs, and uses Clara to extend their reach. |
| Administrator | The project team (PI and student RA) who manage accounts, monitor usage and LLM quality, and curate domain content. |

---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | React 18 + Vite | Responsive SPA; component-based UI for upload, questionnaire, assessment, and document views |
| Backend | FastAPI (Python 3.11+) | REST API; orchestrates the multi-agent LLM layer server-side |
| Relational DB | PostgreSQL | Users, profiles, ranked preferences, development plans, job leads — structured/queryable data |
| Document DB | MongoDB | Parsed resumes, LinkedIn extracts, generated resumes & cover letters, assessment transcripts — document-shaped data |
| AI / LLM | Anthropic Claude (`claude-sonnet-4-6`) via the Anthropic API | Multi-agent design: assessment, planning, document generation, job matching |
| File parsing | `pypdf` / `python-docx` | Extract text from uploaded resume files |
| PDF rendering | `typst` (Python bindings) | Render generated resumes to one-page PDFs server-side |
| Hosting | Vercel (frontend), Render (backend), Supabase (Postgres), MongoDB Atlas (documents) | Free / low-cost tiers for the pilot |

---

## Stakeholders

| Name / Role | Responsibility |
|-------------|----------------|
| Dr. Alex Pang — Principal Investigator, Dept. of Computer & Information Sciences | Leads project design, development, and evaluation; defines scope and reviews milestones |
| Dr. Kristen Gallo, EdD — Executive Director, Temple University Career Center (Collaborator) | Provides career-counseling domain expertise and best practices; facilitates integration with Career Center services |
| CST Student Research Assistant | Development, testing, and documentation support |
| End Users (CST students) | Testing, feedback, and validation of usefulness |

---

## Key Constraints

- Funded by a CST Innovation Initiative grant ($3,000 for AI API access for ~500 students; $2,000 for a student assistant) — usage and prompt design must stay within a real token budget.
- Pilot must reach a deployable prototype within the grant timeline (architecture May–July, implementation Aug–Nov, pilot Dec–May).
- Must use free / low-cost cloud tiers wherever possible.
- Student data is sensitive (resumes, academic history, career goals) — privacy and FERPA-aware handling are required.
- AI-generated career advice must be reviewable by Career Center professionals, not delivered as unchecked authority.
- Built and maintained primarily by students learning the stack — favor simple, well-documented choices over clever ones.
