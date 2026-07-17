import { defineConfig } from "@playwright/test";

// Shared secret for the local-only /auth/test-login endpoint. CI sets its own.
const TEST_LOGIN_SECRET = process.env.TEST_LOGIN_SECRET || "e2e-local-secret";

// CI installs backend deps globally; local dev uses the backend virtualenv.
const backendPython = process.env.CI ? "python" : ".venv/bin/python";

export default defineConfig({
  testDir: "e2e",
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["html", { open: "never" }]] : "list",
  // CI runners cold-compile the Vite module graph on first request; give
  // assertions more headroom than the 5s default.
  expect: {
    timeout: 15_000,
    // Visual-regression defaults: disable animations and hide the text caret so
    // snapshots are deterministic, and allow a tiny per-pixel tolerance for
    // sub-pixel font antialiasing between runs on the same platform.
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.01,
      animations: "disabled",
      caret: "hide",
    },
  },
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
    // Pin the viewport so screenshot baselines are stable across machines/CI.
    viewport: { width: 1280, height: 800 },
  },
  // Both servers are started fresh so the backend is guaranteed to run with
  // the mock LLM provider and the test-login secret — never reuse a dev
  // server that may point at a real provider.
  webServer: [
    {
      command: `${backendPython} -m uvicorn app.main:app --port 8000`,
      cwd: "../backend",
      url: "http://localhost:8000/docs",
      reuseExistingServer: false,
      timeout: 60_000,
      env: {
        ENVIRONMENT: "local",
        LLM_PROVIDER: "mock",
        TEST_LOGIN_SECRET,
      },
    },
    {
      command: "npm run dev",
      url: "http://localhost:5173",
      reuseExistingServer: false,
      timeout: 60_000,
      // CI has no frontend/.env (gitignored) — provide the Vite vars here so
      // the app's fetch wrapper gets a real API base in every environment.
      env: {
        VITE_API_BASE_URL: "/api",
        VITE_GOOGLE_CLIENT_ID: "test-client-id",
      },
    },
  ],
});
