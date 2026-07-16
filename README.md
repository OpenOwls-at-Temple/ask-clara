# ask-clara
# Ask Clara (AI Career Coach)

Clara ("Ask Clara") is an AI career coach built for Temple University undergraduate, graduate, and PhD students. It helps students move from self-assessment to targeted job applications by providing persistent, personalized, and always-available career guidance.

Clara complements the Temple Career Center by acting as a low-pressure, always-on starting point that prepares students for meaningful engagements with human advisors.

---

## Tech Stack & Architecture

Clara is a three-tier web application built with:

- **Frontend**: React 18 + Vite (SPA)
- **Backend**: FastAPI (Python 3.11+)
- **Relational Database**: PostgreSQL (Users, profiles, target roles, development plans, job leads)
- **Document Database**: MongoDB (Uploaded/parsed resumes, LinkedIn data, assessments, generated resumes)
- **AI / LLM Layer**: Anthropic Claude (`claude-sonnet-4-6` or compatible) via a server-side multi-agent orchestrator

### Data Consistency Rule
This project uses a hybrid database setup (Postgres + MongoDB). In services writing to both:
- Write to MongoDB **first**.
- Write to PostgreSQL **second**.
- If Postgres fails, delete the orphaned MongoDB document to ensure cross-database consistency.

---

## Local Development Setup

### Prerequisites

Ensure you have the following installed on your machine:
- **Node.js**: 20+
- **Python**: 3.11+
- **Docker & Docker Compose**: For launching PostgreSQL and MongoDB locally.
- **Anthropic API Key**: From console.anthropic.com.
- **Google Client ID & Secret**: For Google SSO.

---

### Step-by-Step Setup

#### 1. Spin Up Local Databases
From the project root, start PostgreSQL and MongoDB using Docker Compose:
```bash
docker compose up -d
```
This starts:
- PostgreSQL on `localhost:5432` (Username: `user`, Password: `password`, Database: `clara`)
- MongoDB on `localhost:27017`

#### 2. Backend Setup
Navigate to the `backend` directory and set up your Python virtual environment:
```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows (cmd):
# .venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

##### Configure Backend Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill out the variables inside `.env`:
- `ANTHROPIC_API_KEY`: Your Anthropic developer console API key.
- `DATABASE_URL`: `postgresql+asyncpg://user:password@localhost:5432/clara` (pre-filled)
- `MONGODB_URI`: `mongodb://localhost:27017/clara` (pre-filled)
- `GOOGLE_CLIENT_ID`: Your Google OAuth 2.0 Web Client ID.
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth 2.0 Client Secret.
- `JWT_SECRET`: A long random string to sign JWTs (e.g., generate via `openssl rand -hex 32`).
- `ALLOWED_EMAIL_DOMAIN`: `temple.edu`
- `ENVIRONMENT`: `local`
- `TEST_LOGIN_SECRET`: Enables the local test-login flow and the Playwright E2E suite (see "Test Login" below). The pre-filled default matches the frontend's; **never set this in staging/production.**

##### Run Database Migrations (Postgres)
Initialize and migrate the database schema using Alembic:
```bash
python -m alembic upgrade head
```

##### Start the FastAPI Server
```bash
python -m uvicorn app.main:app --reload
```
The API documentation will be available at `http://localhost:8000/docs`.

---

#### 3. Frontend Setup
In a new terminal window, navigate to the `frontend` directory:
```bash
cd frontend

# Install Node modules
npm install
```

##### Configure Frontend Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Update `.env`:
- `VITE_API_BASE_URL`: `/api` (This works because Vite's dev server proxies `/api` to the backend)
- `VITE_GOOGLE_CLIENT_ID`: Your Google OAuth Web Client ID.
- `VITE_TEST_LOGIN_SECRET`: Must match the backend's
- `TEST_LOGIN_SECRET` (see "Test Login" below). The `.env.example` defaults on both sides already match.

##### Start the Frontend Server
```bash
npm run dev
```
The React application will be running locally at `http://localhost:5173`.

---

#### 4. Test Login (Local Development Only)

You can sign in without a Google account or a `@temple.edu` email while developing locally. When the frontend runs in dev mode (`npm run dev`), the sign-in page shows a **"Local Development Only"** form: enter any `@temple.edu` email (default `test1@temple.edu`) and click **Test Login**. The backend creates (or reuses) a synthetic user with that email and issues a normal session.

For this to work, the backend `.env` must have:
- `ENVIRONMENT=local`
- `TEST_LOGIN_SECRET` set (the `.env.example` default is `e2e-local-secret`)

and the frontend's `VITE_TEST_LOGIN_SECRET` must match `TEST_LOGIN_SECRET`. If you keep the `.env.example` defaults on both sides, no extra configuration is needed.

This is safe by design:
- The form is only rendered in Vite dev builds — it is stripped from production bundles.
- The backend endpoint (`POST /auth/test-login`) responds `404` unless `ENVIRONMENT=local` **and** the secret matches, so it is indistinguishable from a nonexistent route in staging/production. Never set `TEST_LOGIN_SECRET` outside local development.
- Emails are still restricted to the `ALLOWED_EMAIL_DOMAIN` (`temple.edu`).

The same endpoint powers the Playwright E2E suite (`frontend/e2e/`), which authenticates test users through it instead of Google SSO.

---

## Development Commands

### Running Tests

#### Backend Tests (Pytest)
Ensure your virtual environment is active in the `backend` directory, then run:
```bash
# Run all tests (requires Docker services to be up for database-dependent integration tests)
pytest

# Run a specific test file
pytest tests/test_assessment.py

# Run tests by name pattern
pytest -k "test_student_cannot"
```

#### Frontend Tests (Jest)
From the `frontend` directory, run:
```bash
npm test
```

### Code Formatting & Linting

#### Backend
We use `black` for auto-formatting Python code:
```bash
black app/
```

#### Frontend
We use `eslint` and `prettier`:
```bash
# Run ESLint check
npm run lint

# Run Prettier format
npx prettier --write src/
```

### Generating Database Migrations (Alembic)
Whenever you modify SQLAlchemy models in `backend/app/models/`, auto-generate a new migration:
```bash
cd backend
python -m alembic revision --autogenerate -m "describe changes here"
python -m alembic upgrade head
```

---

## Coding Guardrails & Best Practices

- **Never call the LLM from the frontend**: All agents and LLM services must be invoked server-side in `backend/app/llm/`.
- **Define prompts centrally**: Prompts are stored only in [backend/app/llm/prompts.py](backend/app/llm/prompts.py) — never inline them in routes or services.
- **Protect PII**: Strip sensitive student identifiers (Temple email, phone, street address) and self-reported demographic statuses (first-gen, commuter, working) before passing context to LLM agents.
- **Respect Token Budgets**: Pre-truncate experience context (e.g., keep the ~3 most recent roles) and enforce a ~1500-token input cap.
- **Atomic Quota Gate**: Every LLM generation must check and increment the database-backed per-user lifetime limit (`users.llm_generation_count`). If the generation fails, the credit must be refunded.
- **Mock LLM Calls in Tests**: Never hit live AI provider endpoints during unit tests; ensure appropriate mocking is configured.
