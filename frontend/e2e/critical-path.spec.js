import { test, expect } from "@playwright/test";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const RESUME_FIXTURE = path.resolve(
  __dirname,
  "../../docs/fixtures/synthetic-resume.docx",
);
const SECRET = process.env.TEST_LOGIN_SECRET || "e2e-local-secret";

// One student journey in order: sign in → intake → assessment → resumes.
test.describe.configure({ mode: "serial" });

// Unique per run so reruns never collide on profile state.
const email = `e2e+${Date.now()}@temple.edu`;

test("student signs in, completes intake, and generates an assessment", async ({
  page,
}) => {
  // Mint a session through the frontend origin: the refresh cookie is scoped
  // to path /api/auth, so it must land first-party on localhost:5173 for the
  // app's session restore to see it. page.request shares the page cookie jar.
  const login = await page.request.post("/api/auth/test-login", {
    data: { email, display_name: "E2E Student" },
    headers: { "X-Test-Login-Secret": SECRET },
  });
  expect(login.ok()).toBeTruthy();

  // Session restore from the refresh cookie lands on the dashboard.
  await page.goto("/");
  await expect(page.getByText("Hello, E2E")).toBeVisible();
  await expect(page.getByText("Incomplete")).toBeVisible();

  // Intake: questionnaire.
  await page.goto("/intake");
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
  // On success the questionnaire collapses into a summary card.
  await expect(
    page.getByText(/Undergraduate · Computer Science/),
  ).toBeVisible();

  // Intake: resume upload (sanctioned synthetic fixture only).
  await page
    .locator('.upload-zone input[type="file"]')
    .first()
    .setInputFiles(RESUME_FIXTURE);
  await page.getByRole("button", { name: "Upload Resume" }).click();
  await expect(page.getByText("Resume on file")).toBeVisible();

  // Dashboard now shows a complete profile with unlocked AI cards.
  await page.goto("/dashboard");
  await expect(page.getByText("Complete")).toBeVisible();
  await expect(page.getByText("Ready").first()).toBeVisible();

  // Assessment: run against the deterministic mock provider.
  await page.getByRole("button", { name: "View / Run" }).click();
  await page.getByRole("button", { name: /Run Assessment/ }).click();
  await expect(page.getByText(/Mock strength/).first()).toBeVisible();
  await expect(page.getByText(/Mock recommendation/).first()).toBeVisible();
});

test("generates one tailored resume draft per target role", async ({
  page,
}) => {
  // Same student as the previous test (serial mode) — restore the session.
  const login = await page.request.post("/api/auth/test-login", {
    data: { email, display_name: "E2E Student" },
    headers: { "X-Test-Login-Secret": SECRET },
  });
  expect(login.ok()).toBeTruthy();

  await page.goto("/resumes");
  await page.getByRole("button", { name: "Generate Resumes" }).click();
  await expect(page.getByText(/3 drafts/)).toBeVisible({ timeout: 30_000 });
  await expect(page.getByText("First Choice")).toBeVisible();
  await expect(
    page.getByText("Mock summary tailored to the role.").first(),
  ).toBeVisible();
});
