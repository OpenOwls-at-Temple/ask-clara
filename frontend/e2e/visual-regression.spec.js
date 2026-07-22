import { test, expect } from "@playwright/test";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const RESUME_FIXTURE = path.resolve(
  __dirname,
  "../../docs/fixtures/synthetic-resume.docx",
);
const SECRET = process.env.TEST_LOGIN_SECRET || "e2e-local-secret";

// Visual-regression baselines for the 5 core pages, each captured in a populated
// state against the deterministic mock LLM provider. A single serial flow seeds
// the state every later page needs: profile → assessment → resumes → plan. The
// screenshot assertions are soft so one visual diff does not hide the others —
// every page is checked and every diff reported in a single run.
test.describe.configure({ mode: "serial" });

// Unique per run so reruns never collide on server-side profile state. The email
// is never rendered into any snapshotted view, so it does not affect baselines.
const email = `e2e+visual+${Date.now()}@temple.edu`;

// Run-time labels (e.g. "Generated 7/17/2026, 3:04 PM") change every run and must
// never enter a baseline, so they are masked out of the screenshots.
const timeMasks = (page) => [
  page.locator(".assessment-meta"),
  page.locator(".resume-card-meta"),
];

async function snapshot(page, name) {
  // Let async web fonts settle so glyph metrics are stable before capture.
  await page.evaluate(() => document.fonts.ready);
  await expect
    .soft(page)
    .toHaveScreenshot(name, { fullPage: true, mask: timeMasks(page) });
}

test("core pages match their visual baselines", async ({ page }) => {
  // Mint a session first-party on the frontend origin (see critical-path.spec.js
  // for why the refresh cookie must land on localhost:5173).
  const login = await page.request.post("/api/auth/test-login", {
    data: { email, display_name: "E2E Student" },
    headers: { "X-Test-Login-Secret": SECRET },
  });
  expect(login.ok()).toBeTruthy();

  // 1) Intake — the empty questionnaire (the richest form in the app), captured
  // before any data is entered so the baseline is deterministic.
  await page.goto("/intake");
  await expect(
    page.getByRole("button", { name: "Save Profile" }),
  ).toBeVisible();
  await snapshot(page, "intake.png");

  // Fill the questionnaire and upload the sanctioned synthetic resume so the
  // downstream pages render in a complete state.
  await page.selectOption("#degree_level", "undergrad");
  await page.fill("#major_program", "Computer Science");
  await page.fill("#expected_graduation", "2027-05");
  await page.selectOption("#track", "industry");
  await page
    .getByPlaceholder("e.g. Software Engineer")
    .fill("Software Engineer");
  await page.getByPlaceholder("e.g. Data Scientist").fill("Data Analyst");
  await page.getByPlaceholder("e.g. Product Manager").fill("Product Manager");
  await page.getByRole("button", { name: "Save Profile" }).click();
  await expect(
    page.getByText(/Undergraduate · Computer Science/),
  ).toBeVisible();

  await page
    .locator('.upload-zone input[type="file"]')
    .first()
    .setInputFiles(RESUME_FIXTURE);
  await page.getByRole("button", { name: "Upload Resume" }).click();
  await expect(page.getByText(/synthetic-resume\.docx on file/)).toBeVisible();

  // 2) Dashboard — complete profile with unlocked AI cards.
  await page.goto("/dashboard");
  await expect(page.getByText("Complete", { exact: true })).toBeVisible();
  await expect(page.getByText("Ready").first()).toBeVisible();
  await snapshot(page, "dashboard.png");

  // 3) Assessment — run against the mock provider, then capture the result.
  await page.goto("/assessment");
  await page.getByRole("button", { name: /Run Assessment/ }).click();
  await expect(page.getByText(/Mock strength/).first()).toBeVisible();
  await expect(page.getByText(/Mock recommendation/).first()).toBeVisible();
  await snapshot(page, "assessment.png");

  // 4) Resumes — one tailored draft per target role.
  await page.goto("/resumes");
  await page.getByRole("button", { name: "Generate Resumes" }).click();
  await expect(page.getByText(/3 drafts/)).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("First Choice")).toBeVisible();
  await expect(
    page.getByText("Mock summary tailored to the role.").first(),
  ).toBeVisible();
  await snapshot(page, "resumes.png");

  // 5) Plan — a 6-month roadmap generated from the assessment.
  await page.goto("/plan");
  await page.getByRole("button", { name: "Generate Plan" }).click();
  await expect(page.getByText(/-month horizon/)).toBeVisible({
    timeout: 30_000,
  });
  await expect(page.getByText("Milestones")).toBeVisible();
  await snapshot(page, "plan.png");
});
