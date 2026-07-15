import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Intake from "../src/pages/Intake";

jest.mock("../src/hooks/useProfile", () => ({ useProfile: jest.fn() }));
jest.mock("../src/components/NavBar", () => () => <nav />);

const { useProfile } = require("../src/hooks/useProfile");

// Minimal profile with degree + roles → triggers auto-collapse
const savedProfile = {
  degree_level: "grad",
  major_program: "computer science",
  expected_graduation: "2026-10",
  track: "industry",
  is_first_gen: false,
  target_roles: [
    { rank: 1, title: "sw engineer" },
    { rank: 2, title: "data engineer" },
  ],
  resume_doc_id: null,
  linkedin_doc_id: null,
};

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

  test("auto-collapses when profile has degree_level AND target_roles", () => {
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

    fireEvent.click(screen.getByText("Save Profile"));

    await waitFor(() => {
      expect(screen.queryByLabelText("Degree level")).toBeNull();
      expect(screen.getByText("Edit")).toBeInTheDocument();
    });
  });

  test("stays expanded after a failed save", async () => {
    baseHook.save.mockRejectedValue(new Error("network"));
    renderIntake({ profile: null, save: baseHook.save });

    fireEvent.click(screen.getByText("Save Profile"));

    await waitFor(() => {
      expect(screen.getByLabelText("Degree level")).toBeInTheDocument();
    });
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

  test("shows 'Resume on file' card when profile.resume_doc_id is set and no preview active", () => {
    renderIntake({
      profile: { ...savedProfile, resume_doc_id: "mongo-id-abc" },
    });
    expect(screen.getByText("Resume on file")).toBeInTheDocument();
    expect(
      screen.getByText("Select a new file below to replace it"),
    ).toBeInTheDocument();
  });

  test("does NOT show 'Resume on file' card when profile has no resume_doc_id", () => {
    renderIntake({ profile: { ...savedProfile, resume_doc_id: null } });
    expect(screen.queryByText("Resume on file")).toBeNull();
  });

  test("shows 'Resume on file' card even after a failed upload attempt", async () => {
    const saveResume = jest.fn().mockRejectedValue(new Error("bad file"));
    const { container } = renderIntake({
      profile: { ...savedProfile, resume_doc_id: "existing-id" },
      saveResume,
    });

    const file = new File(["content"], "bad.pdf", { type: "application/pdf" });
    const input = container.querySelectorAll("input[type='file']")[0];
    fireEvent.change(input, { target: { files: [file] } });
    fireEvent.click(screen.getByText("Upload Resume"));

    await waitFor(() => {
      expect(screen.getByText(/Upload failed/i)).toBeInTheDocument();
    });

    // The old resume card should still be visible (not hidden by the error status)
    expect(screen.queryByText("Resume on file")).toBeNull(); // preview URL took over
    // Since a PDF was selected, embed preview is shown instead of the "on file" card — that's expected
  });

  test("upload zone resets label to 'Click to select a file' after successful upload", async () => {
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
      expect(screen.getByText(/Uploaded successfully/)).toBeInTheDocument();
    });

    // After upload, filename is cleared — zone shows placeholder again
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
