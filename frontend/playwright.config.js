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
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
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
    },
  ],
});
