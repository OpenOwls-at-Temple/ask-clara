# Features

> **OpenOwls SDD** — Read by end users and the product owner.
> Defines what the application does, written in plain language.
> Organized into three phases. Phase 1 is the MVP — it must be achievable in the first sprint.

---

## How to Read This File

- **Phase 1** — Must-have features. The app is not usable without these.
- **Phase 2** — Should-have features. Adds meaningful value once Phase 1 is stable.
- **Phase 3** — Nice-to-have features. Advanced capabilities, AI enhancements, or stretch goals.

Each feature includes a short description and a set of acceptance criteria written from the user's perspective.

**Current phase:** Phase 1 (see `progress.md`).

---

## Phase 1 — Core MVP
<!-- Faculty-defined. Smallest useful version: sign in, build a profile, get an assessment, get tailored resumes. -->

### Feature 1: Account & Temple Sign-In
**As a** Temple student,
**I want to** sign in with my Temple account,
**So that** my profile and documents are saved securely and tied to me.

**Acceptance Criteria:**
- [x] Given I have a valid `@temple.edu` Google account, when I sign in, then an account is created or resumed and I land on my dashboard.
- [x] Given I am not signed in, when I try to open any profile or assessment page, then I am redirected to sign in.
- [x] Given I sign out, when I return, then I can sign back in and my saved data is still there.

---

### Feature 2: Profile Intake (Resume + LinkedIn + Questionnaire)
**As a** student,
**I want to** upload my resume and LinkedIn profile and answer a short questionnaire,
**So that** Clara understands my background and goals.

**Acceptance Criteria:**
- [x] Given I am on the intake page, when I upload a PDF or DOCX resume, then its text is parsed and stored and I see a confirmation.
- [x] Given I provide a LinkedIn profile (URL, exported PDF, or a CSV from LinkedIn's data export), when I submit it, then the relevant content is captured and stored with my profile. *(CSV accepted 2026-07-14 — LinkedIn's "Get a copy of your data" download is a ZIP of CSVs, not a PDF.)*
- [x] Given the questionnaire, when I answer it, then I can record my major/program, degree level (undergrad / grad / PhD), intended track (industry / academia / government / undecided), and graduation timeline.
- [x] Given the "dream job" question, when I respond, then I can enter **three** target roles **ranked** by preference (1–3).
- [x] Given I leave and return, when I reopen intake, then my previous answers are pre-filled and editable.

---

### Feature 3: Persistent Student Profile
**As a** student,
**I want** my profile and preferences saved across sessions,
**So that** Clara acts as a persistent coach rather than a one-off tool.

**Acceptance Criteria:**
- [x] Given I completed intake, when I log in later, then my profile, ranked preferences, and uploaded documents are loaded.
- [x] Given I edit my profile, when I save, then the change persists and is reflected in future assessments.
- [x] Given I view my profile, when it loads, then I only ever see my own data — never another student's.

---

### Feature 4: AI Profile Assessment & Recommendations
**As a** student,
**I want** Clara to review my profile and resume and give me feedback,
**So that** I learn my strengths, gaps, and next steps.

**Acceptance Criteria:**
- [x] Given a complete profile, when I request an assessment, then Clara returns identified strengths, gaps relative to my ranked target roles, and concrete recommendations.
- [x] Given the assessment, when it displays, then feedback is specific to STEM career paths (technical skills, projects, internship pipeline) rather than generic.
- [x] Given an assessment is generated, when it completes, then it is saved and viewable later without re-running the model.
- [x] Given the LLM call fails, when I request an assessment, then I see a friendly fallback message and can retry.

---

### Feature 5: Generate Three Tailored Base Resumes
**As a** student,
**I want** Clara to produce three customized resume drafts,
**So that** I have strong starting points aimed at my top target roles.

**Acceptance Criteria:**
- [x] Given my profile and three ranked target roles, when I request resumes, then Clara generates three distinct resume drafts, each oriented toward one ranked role.
- [x] Given each draft, when I review it, then it reflects my real experience (no fabricated employers, degrees, or dates).
- [x] Given a draft, when I want it, then I can download it (PDF/DOCX) and/or copy the text.
- [x] Given I edit a draft, when I save, then my edited version is stored alongside the original.

---

## Phase 2 — Enhanced Features
<!-- Defined after Phase 1 is stable. Development plans, job scanning, and per-posting tailoring. -->

### Feature 6: Personalized 6-Month Development Plan
**As a** student,
**I want** a roadmap of skills, experiences, and credentials to acquire,
**So that** I know exactly what to work on to reach my target roles.

**Acceptance Criteria:**
- [ ] Given my assessment, when I request a plan, then Clara generates a 6-month roadmap with milestones tailored to industry, academia, or government tracks.
- [ ] Given the plan, when it displays, then each item names a specific skill, experience, or credential and why it matters for my target role.
- [ ] Given time passes, when I revisit the plan, then I can mark items complete and Clara updates my progress.

---

### Feature 7: Job Leads Scanning & Alerts
**As a** student,
**I want** Clara to find relevant job and internship postings and alert me,
**So that** I spend my time on opportunities that fit my goals.

**Acceptance Criteria:**
- [x] Given my profile and preferences, when the scanner runs, then it collects postings that match my target roles and surfaces them with the original job link.
- [x] Given matched leads, when I view them, then they are prioritized by fit to my ranked preferences.
- [x] Given new matches, when they appear, then I receive a notification (in-app and/or email) with the job link. *(In-app: new-lead badge on the NavBar and Dashboard; email deferred by decision 2026-07-10.)*
- [x] Given a lead, when I open it, then I see why Clara thinks it fits me.

---

### Feature 8: Per-Posting Resume + Cover Letter + Employer Brief
**As a** student,
**I want** a resume and cover letter tailored to a specific posting plus context on the employer,
**So that** my application is targeted and I walk in informed.

**Acceptance Criteria:**
- [ ] Given a specific job posting, when I request materials, then Clara produces a tailored resume variant and a matching cover letter for that posting.
- [ ] Given the materials, when they display, then technical-skills sections, relevant projects, and quantifiable outcomes are emphasized for that role.
- [ ] Given a posting, when materials are generated, then Clara also produces a short brief on the potential employer.
- [ ] Given generated documents, when I review them, then nothing about my background is fabricated.

---

### Feature 9: Interview Prep Guidance
**As a** student,
**I want** guidance on preparing for technical and behavioral interviews,
**So that** I can navigate the STEM hiring pipeline with confidence.

**Acceptance Criteria:**
- [ ] Given a target role or posting, when I request prep, then Clara outlines likely interview formats and focus areas.
- [ ] Given the prep, when it displays, then it includes practice prompts relevant to my target role.

---

## Phase 3 — Advanced / AI Features
<!-- Stretch goals: counselor integration, progress dashboards, and supervised auto-application. -->

### Feature 10: Career Center Counselor Integration
**As a** student,
**I want** to share my Clara progress with a Temple counselor,
**So that** a human professional can review the AI's advice and help me further.

**Acceptance Criteria:**
- [ ] Given my consent, when I request a handoff, then a counselor can view a summary of my profile, assessment, and materials.
- [ ] Given a counselor reviews advice, when they respond, then their feedback is recorded alongside Clara's.

---

### Feature 11: Progress Tracking Dashboard
**As a** student,
**I want** a single view of my development arc,
**So that** I can see how far I've come and what's left.

**Acceptance Criteria:**
- [ ] Given my activity, when I open the dashboard, then I see assessment history, plan progress, applications, and leads in one place.

---

### Feature 12: Supervised Application Submission
**As a** student,
**I want** Clara to help submit applications on my behalf with my approval,
**So that** I can apply to fitting roles efficiently.

**Acceptance Criteria:**
- [ ] Given a matched lead and finalized materials, when I explicitly approve, then Clara assists with submission and records it.
- [ ] Given any submission, when it occurs, then it required an explicit human approval step — Clara never submits silently.

---

## Out of Scope

- Native iOS/Android apps (responsive web only for the pilot).
- Multi-language support (English only initially).
- Guaranteeing interviews, offers, or salary outcomes.
- Scraping behind paywalls or violating job-site terms of service.
- Storing or processing data for non-Temple users.
- Replacing the Temple Career Center or its counselors.
