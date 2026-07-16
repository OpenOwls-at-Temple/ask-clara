import {
  render,
  screen,
  fireEvent,
  waitFor,
  within,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Intake from "../src/pages/Intake";

jest.mock("../src/hooks/useProfile", () => ({ useProfile: jest.fn() }));
jest.mock("../src/components/NavBar", () => () => <nav />);

const { useProfile } = require("../src/hooks/useProfile");

// Fully answered questionnaire (all fields + 3 roles) → triggers auto-collapse
const savedProfile = {
  degree_level: "grad",
  major_program: "computer science",
  expected_graduation: "2026-10",
  track: "industry",
  is_first_gen: false,
  target_roles: [
    { rank: 1, title: "sw engineer" },
    { rank: 2, title: "data engineer" },
    { rank: 3, title: "ml engineer" },
  ],
  resume_doc_id: null,
  linkedin_doc_id: null,
};

// Legacy partial profile (only 2 roles) — must stay expanded
const partialProfile = {
  ...savedProfile,
  target_roles: savedProfile.target_roles.slice(0, 2),
};

function fillQuestionnaire() {
  fireEvent.change(screen.getByLabelText("Degree level"), {
    target: { value: "grad" },
  });
  fireEvent.change(screen.getByLabelText("Major / Program"), {
    target: { value: "computer science" },
  });
  fireEvent.change(screen.getByLabelText("Expected graduation"), {
    target: { value: "2026-10" },
  });
  fireEvent.change(screen.getByLabelText("Career track"), {
    target: { value: "industry" },
  });
  fireEvent.change(screen.getByPlaceholderText("e.g. Software Engineer"), {
    target: { value: "sw engineer" },
  });
  fireEvent.change(screen.getByPlaceholderText("e.g. Data Scientist"), {
    target: { value: "data engineer" },
  });
  fireEvent.change(screen.getByPlaceholderText("e.g. Product Manager"), {
    target: { value: "ml engineer" },
  });
}

const baseHook = {
  profile: null,
  loading: false,
  save: jest.fn(),
  saveResume: jest.fn(),
  saveLinkedIn: jest.fn(),
  saveLinkedInExport: jest.fn(),
};

function renderIntake(hookOverrides = {}) {
  useProfile.mockReturnValue({ ...baseHook, ...hookOverrides });
  return render(
    <MemoryRouter>
      <Intake />
    </MemoryRouter>,
  );
}

// ─── Background & Goals collapse ────────────────────────────────────────────

describe("Intake — Background & Goals collapsible section", () => {
  test("shows expanded form when profile has no data", () => {
    renderIntake({ profile: null });
    expect(screen.getByLabelText("Degree level")).toBeInTheDocument();
    expect(screen.queryByText("Edit")).toBeNull();
  });

  test("auto-collapses when profile has all fields and 3 target_roles", () => {
    renderIntake({ profile: savedProfile });
    expect(screen.queryByLabelText("Degree level")).toBeNull();
    expect(screen.getByText("Edit")).toBeInTheDocument();
    expect(screen.getByText("Background & Goals")).toBeInTheDocument();
  });

  test("does NOT auto-collapse when only degree_level is set (no roles)", () => {
    renderIntake({
      profile: { ...savedProfile, target_roles: [] },
    });
    // Form should remain expanded
    expect(screen.getByLabelText("Degree level")).toBeInTheDocument();
    expect(screen.queryByText("Edit")).toBeNull();
  });

  test("does NOT auto-collapse when only target_roles are set (no degree)", () => {
    renderIntake({
      profile: { ...savedProfile, degree_level: null },
    });
    expect(screen.getByLabelText("Degree level")).toBeInTheDocument();
    expect(screen.queryByText("Edit")).toBeNull();
  });

  test("does NOT auto-collapse a legacy profile with fewer than 3 roles", () => {
    renderIntake({ profile: partialProfile });
    expect(screen.getByLabelText("Degree level")).toBeInTheDocument();
    expect(screen.queryByText("Edit")).toBeNull();
  });

  test("collapsed summary shows degree label and top 2 roles", () => {
    renderIntake({ profile: savedProfile });
    const summary = screen.getByText(/Graduate/);
    expect(summary.textContent).toContain("computer science");
    expect(summary.textContent).toContain("sw engineer");
    expect(summary.textContent).toContain("data engineer");
  });

  test("clicking Edit expands the form", () => {
    renderIntake({ profile: savedProfile });
    fireEvent.click(screen.getByText("Edit"));
    expect(screen.getByLabelText("Degree level")).toBeInTheDocument();
    expect(screen.queryByText("Edit")).toBeNull();
  });

  test("shows green check circle when collapsed", () => {
    const { container } = renderIntake({ profile: savedProfile });
    const check = container.querySelector(".form-card-check");
    expect(check).not.toBeNull();
    expect(check.textContent).toBe("✓");
  });

  test("collapses after a successful save", async () => {
    baseHook.save.mockResolvedValue({});
    renderIntake({ profile: null, save: baseHook.save });

    // Form is expanded
    expect(screen.getByLabelText("Degree level")).toBeInTheDocument();

    fillQuestionnaire();
    fireEvent.click(screen.getByText("Save Profile"));

    await waitFor(() => {
      expect(screen.queryByLabelText("Degree level")).toBeNull();
      expect(screen.getByText("Edit")).toBeInTheDocument();
    });
  });

  test("stays expanded after a failed save", async () => {
    baseHook.save.mockRejectedValue(new Error("network"));
    renderIntake({ profile: null, save: baseHook.save });

    fillQuestionnaire();
    fireEvent.click(screen.getByText("Save Profile"));

    await waitFor(() => {
      expect(screen.getByLabelText("Degree level")).toBeInTheDocument();
    });
  });

  test("blocks save and shows an error when fields are missing", () => {
    const save = jest.fn();
    renderIntake({ profile: null, save });

    // Fill everything except the third role
    fillQuestionnaire();
    fireEvent.change(screen.getByPlaceholderText("e.g. Product Manager"), {
      target: { value: "  " },
    });
    fireEvent.click(screen.getByText("Save Profile"));

    expect(save).not.toHaveBeenCalled();
    expect(
      screen.getByText(/Please complete all fields and enter all three/),
    ).toBeInTheDocument();
  });

  test("blocks save when a select field is empty", () => {
    const save = jest.fn();
    renderIntake({ profile: null, save });

    fillQuestionnaire();
    fireEvent.change(screen.getByLabelText("Career track"), {
      target: { value: "" },
    });
    fireEvent.click(screen.getByText("Save Profile"));

    expect(save).not.toHaveBeenCalled();
    expect(
      screen.getByText(/Please complete all fields and enter all three/),
    ).toBeInTheDocument();
  });
});

// ─── Step-1 completion banner ────────────────────────────────────────────────

describe("Intake — completion / continue banner", () => {
  const completeProfile = {
    ...savedProfile,
    resume_doc_id: "mongo-id-abc",
    target_roles: [
      { rank: 1, title: "sw engineer" },
      { rank: 2, title: "data engineer" },
      { rank: 3, title: "ml engineer" },
    ],
  };

  test("shows continue button when resume is on file and 3 roles saved", () => {
    renderIntake({ profile: completeProfile });
    expect(screen.getByText("Step 1 complete")).toBeInTheDocument();
    expect(screen.getByText("Continue to AI Assessment →")).toBeInTheDocument();
  });

  test("notes that LinkedIn is optional when it was skipped", () => {
    renderIntake({ profile: { ...completeProfile, linkedin_doc_id: null } });
    expect(screen.getByText(/LinkedIn is optional/)).toBeInTheDocument();
  });

  test("tells the student what is missing when profile is incomplete", () => {
    renderIntake({ profile: partialProfile }); // 2 roles, no resume
    expect(screen.getByText("To finish Step 1")).toBeInTheDocument();
    expect(
      screen.getByText(
        /Upload your resume and save all three ranked target roles/,
      ),
    ).toBeInTheDocument();
    expect(screen.queryByText("Continue to AI Assessment →")).toBeNull();
  });

  test("asks only for missing roles when resume is already uploaded", () => {
    renderIntake({
      profile: { ...partialProfile, resume_doc_id: "mongo-id-abc" }, // 2 roles saved
    });
    expect(screen.getByText(/Save 1 more target role/)).toBeInTheDocument();
  });
});

// ─── Resume section ──────────────────────────────────────────────────────────

describe("Intake — Resume section", () => {
  beforeEach(() => {
    // Reset URL API mocks
    global.URL.createObjectURL = jest.fn(() => "blob:fake-url");
    global.URL.revokeObjectURL = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test("shows 'Click to select a file' when no file selected and no resume on file", () => {
    renderIntake({ profile: savedProfile });
    expect(screen.getByText("Click to select a file")).toBeInTheDocument();
  });

  test("collapses with 'Resume on file' summary when profile.resume_doc_id is set", () => {
    renderIntake({
      profile: { ...savedProfile, resume_doc_id: "mongo-id-abc" },
    });
    expect(screen.getByText(/Resume on file/)).toBeInTheDocument();
    // Upload UI is hidden while collapsed
    expect(screen.queryByText("Click to select a file")).toBeNull();
  });

  test("clicking Edit on the collapsed Resume card reveals the upload UI", () => {
    renderIntake({
      profile: { ...savedProfile, resume_doc_id: "mongo-id-abc" },
    });
    const resumeCard = screen.getByText(/Resume on file/).closest(".form-card");
    fireEvent.click(within(resumeCard).getByText("Edit"));
    expect(screen.getByText("Click to select a file")).toBeInTheDocument();
    expect(
      screen.getByText("Select a new file below to replace it"),
    ).toBeInTheDocument();
  });

  test("does NOT collapse the Resume section when profile has no resume_doc_id", () => {
    renderIntake({ profile: { ...savedProfile, resume_doc_id: null } });
    expect(screen.queryByText(/Resume on file/)).toBeNull();
    expect(screen.getByText("Click to select a file")).toBeInTheDocument();
  });

  test("stays expanded and shows the error after a failed upload attempt", async () => {
    const saveResume = jest.fn().mockRejectedValue(new Error("bad file"));
    const { container } = renderIntake({
      profile: { ...savedProfile, resume_doc_id: "existing-id" },
      saveResume,
    });

    // Section starts collapsed — expand it first
    const resumeCard = screen.getByText(/Resume on file/).closest(".form-card");
    fireEvent.click(within(resumeCard).getByText("Edit"));

    const file = new File(["content"], "bad.pdf", { type: "application/pdf" });
    const input = container.querySelectorAll("input[type='file']")[0];
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByText("Upload Resume"));

    await waitFor(() => {
      expect(screen.getByText(/Upload failed/i)).toBeInTheDocument();
    });

    // The failed section must not re-collapse
    expect(screen.getByText("Upload Resume")).toBeInTheDocument();
  });

  test("collapses to 'Resume on file' after a successful upload", async () => {
    const saveResume = jest.fn().mockResolvedValue({ resume_doc_id: "new-id" });
    const { container } = renderIntake({ profile: savedProfile, saveResume });

    const file = new File(["content"], "resume.pdf", {
      type: "application/pdf",
    });
    // The resume file input is the first file input in the Resume card
    const inputs = container.querySelectorAll("input[type='file']");
    // Resume card input comes before LinkedIn inputs
    const resumeInput = inputs[0];
    fireEvent.change(resumeInput, { target: { files: [file] } });

    expect(screen.getByText("resume.pdf")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Upload Resume"));

    await waitFor(() => {
      expect(screen.getByText(/Resume on file/)).toBeInTheDocument();
    });

    // Expanding again shows a reset upload zone (filename cleared)
    const resumeCard = screen.getByText(/Resume on file/).closest(".form-card");
    fireEvent.click(within(resumeCard).getByText("Edit"));
    expect(screen.queryByText("resume.pdf")).toBeNull();
    expect(screen.getByText("Click to select a file")).toBeInTheDocument();
  });

  test("creates blob URL for PDF selection and shows embed", () => {
    const { container } = renderIntake({ profile: savedProfile });

    const file = new File(["content"], "resume.pdf", {
      type: "application/pdf",
    });
    const input = container.querySelectorAll("input[type='file']")[0];
    fireEvent.change(input, { target: { files: [file] } });

    expect(URL.createObjectURL).toHaveBeenCalledWith(file);
    const embed = container.querySelector("embed");
    expect(embed).not.toBeNull();
    expect(embed.getAttribute("src")).toBe("blob:fake-url");
  });

  test("does NOT create blob URL for DOCX selection", () => {
    const { container } = renderIntake({ profile: savedProfile });

    const file = new File(["content"], "resume.docx", {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const input = container.querySelectorAll("input[type='file']")[0];
    fireEvent.change(input, { target: { files: [file] } });

    expect(URL.createObjectURL).not.toHaveBeenCalled();
    expect(container.querySelector("embed")).toBeNull();
  });

  test("revokes blob URL when component unmounts", () => {
    const { container, unmount } = renderIntake({ profile: savedProfile });

    const file = new File(["content"], "resume.pdf", {
      type: "application/pdf",
    });
    const input = container.querySelectorAll("input[type='file']")[0];
    fireEvent.change(input, { target: { files: [file] } });

    unmount();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:fake-url");
  });

  test("upload zone accepts CSV for the LinkedIn export input", () => {
    const { container } = renderIntake({ profile: savedProfile });
    const inputs = container.querySelectorAll("input[type='file']");
    // inputs[0] = resume, inputs[1] = LinkedIn export
    expect(inputs[0].getAttribute("accept")).toBe(".pdf,.docx");
    expect(inputs[1].getAttribute("accept")).toBe(".pdf,.docx,.csv");
  });

  test("revokes old blob URL and creates a new one when a second PDF is selected", () => {
    const { container } = renderIntake({ profile: savedProfile });

    URL.createObjectURL
      .mockReturnValueOnce("blob:url-1")
      .mockReturnValueOnce("blob:url-2");

    const input = container.querySelectorAll("input[type='file']")[0];

    const file1 = new File(["a"], "first.pdf", { type: "application/pdf" });
    fireEvent.change(input, { target: { files: [file1] } });

    const file2 = new File(["b"], "second.pdf", { type: "application/pdf" });
    fireEvent.change(input, { target: { files: [file2] } });

    // Old URL revoked by useEffect cleanup when resumePreviewUrl changes
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:url-1");
    expect(URL.createObjectURL).toHaveBeenCalledTimes(2);
  });
});

// ─── LinkedIn section ────────────────────────────────────────────────────────

describe("Intake — LinkedIn collapsible section", () => {
  test("is labeled optional when expanded", () => {
    renderIntake({ profile: savedProfile });
    expect(screen.getByText("LinkedIn Profile")).toBeInTheDocument();
    expect(screen.getByText("(optional)")).toBeInTheDocument();
  });

  test("collapses with a summary when profile.linkedin_doc_id is set", () => {
    renderIntake({
      profile: { ...savedProfile, linkedin_doc_id: "mongo-li-id" },
    });
    expect(screen.getByText(/LinkedIn info saved/)).toBeInTheDocument();
    expect(screen.queryByText("Upload LinkedIn Export")).toBeNull();
  });

  test("clicking Edit on the collapsed LinkedIn card reveals the upload UI", () => {
    renderIntake({
      profile: { ...savedProfile, linkedin_doc_id: "mongo-li-id" },
    });
    const card = screen.getByText(/LinkedIn info saved/).closest(".form-card");
    fireEvent.click(within(card).getByText("Edit"));
    expect(screen.getByText("Upload LinkedIn Export")).toBeInTheDocument();
    expect(screen.getByText("Save URL")).toBeInTheDocument();
  });

  test("does NOT collapse when profile has no linkedin_doc_id", () => {
    renderIntake({ profile: savedProfile });
    expect(screen.queryByText(/LinkedIn info saved/)).toBeNull();
    expect(screen.getByText("Upload LinkedIn Export")).toBeInTheDocument();
  });

  test("collapses after a successful URL save", async () => {
    const saveLinkedIn = jest.fn().mockResolvedValue({});
    renderIntake({ profile: savedProfile, saveLinkedIn });

    fireEvent.change(
      screen.getByPlaceholderText("https://linkedin.com/in/your-profile"),
      { target: { value: "https://linkedin.com/in/test" } },
    );
    fireEvent.click(screen.getByText("Save URL"));

    await waitFor(() => {
      expect(screen.getByText(/LinkedIn info saved/)).toBeInTheDocument();
    });
  });
});
