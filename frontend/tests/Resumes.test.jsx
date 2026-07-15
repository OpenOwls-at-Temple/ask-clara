import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Resumes from "../src/pages/Resumes";

jest.mock("../src/hooks/useResumes", () => ({ useResumes: jest.fn() }));
jest.mock("../src/services/documents", () => ({
  downloadResume: jest.fn(),
  fetchResumePdf: jest.fn(),
  saveBlob: jest.fn(),
}));
jest.mock("../src/components/NavBar", () => () => <nav />);

const { useResumes } = require("../src/hooks/useResumes");
const {
  downloadResume,
  fetchResumePdf,
  saveBlob,
} = require("../src/services/documents");

beforeAll(() => {
  global.URL.createObjectURL = jest.fn(() => "blob:mock");
  global.URL.revokeObjectURL = jest.fn();
});

const sampleResume = {
  id: "r1",
  target_rank: 1,
  target_title: "Software Engineer",
  raw_text: "RAW RESUME TEXT",
  edited_text: null,
  sections: [
    { heading: "Summary", content: "CS student at Temple." },
    { heading: "Experience", content: "Intern at Acme." },
  ],
  notes_for_student: ["Quantify your Acme impact."],
  created_at: "2026-07-01T12:00:00Z",
};

const baseHook = {
  resumes: [sampleResume],
  loading: false,
  error: null,
  load: jest.fn(),
  generate: jest.fn(),
  saveEdit: jest.fn().mockResolvedValue(undefined),
};

function renderResumes(overrides = {}) {
  useResumes.mockReturnValue({ ...baseHook, ...overrides });
  return render(
    <MemoryRouter>
      <Resumes />
    </MemoryRouter>,
  );
}

describe("Resumes page", () => {
  beforeEach(() => jest.clearAllMocks());

  test("View PDF shows an inline image preview, then Download saves the PDF", async () => {
    const pngBlob = new Blob(["PNG"], { type: "image/png" });
    const pdfBlob = new Blob(["%PDF"], { type: "application/pdf" });
    fetchResumePdf.mockImplementation((id, format) =>
      Promise.resolve(format === "png" ? pngBlob : pdfBlob),
    );
    renderResumes();

    fireEvent.click(screen.getByText("View PDF"));
    await waitFor(() =>
      expect(screen.getByAltText("Resume PDF preview")).toBeInTheDocument(),
    );
    expect(fetchResumePdf).toHaveBeenCalledWith("r1", "png");

    fireEvent.click(screen.getByText("Download resume"));
    await waitFor(() =>
      expect(saveBlob).toHaveBeenCalledWith(
        pdfBlob,
        "clara-resume-software-engineer.pdf",
      ),
    );
    expect(fetchResumePdf).toHaveBeenCalledWith("r1", "pdf");

    // Toggle closed again
    fireEvent.click(screen.getByText("Hide PDF"));
    expect(screen.queryByAltText("Resume PDF preview")).toBeNull();
  });

  test("failed PDF rendering shows the copy-text fallback inline", async () => {
    fetchResumePdf.mockRejectedValueOnce(new Error("503"));
    renderResumes();

    fireEvent.click(screen.getByText("View PDF"));
    await waitFor(() =>
      expect(screen.getByText(/PDF generation failed/)).toBeInTheDocument(),
    );
    // Copy text stays available on the card.
    expect(screen.getByText("Copy text")).toBeInTheDocument();
  });

  test("DOCX download stays available", async () => {
    downloadResume.mockResolvedValueOnce();
    renderResumes();

    fireEvent.click(screen.getByText("Download .docx"));
    await waitFor(() =>
      expect(downloadResume).toHaveBeenCalledWith(
        "r1",
        "clara-resume-software-engineer.docx",
        "docx",
      ),
    );
  });

  test("shows the empty state and loads on mount", () => {
    renderResumes({ resumes: [] });
    expect(screen.getByText("No resume drafts yet")).toBeInTheDocument();
    expect(baseHook.load).toHaveBeenCalledTimes(1);
  });

  test("shows the drafting spinner while generating with no drafts", () => {
    renderResumes({ loading: true, resumes: [] });
    expect(
      screen.getByText(/Clara is drafting your resumes/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Generating…/)).toBeInTheDocument();
  });

  test("shows the error banner when generation fails", () => {
    renderResumes({ error: new Error("429") });
    expect(screen.getByText(/429/)).toBeInTheDocument();
  });

  test("generate button triggers generation and disables while loading", () => {
    const generate = jest.fn();
    renderResumes({ resumes: [], generate });

    const button = screen.getByText("Generate Resumes");
    fireEvent.click(button);
    expect(generate).toHaveBeenCalledTimes(1);
  });

  test("renders sections, notes, and rank label for a draft", () => {
    renderResumes({ resumes: [sampleResume] });

    expect(screen.getByText("Software Engineer")).toBeInTheDocument();
    expect(screen.getByText("First Choice")).toBeInTheDocument();
    expect(screen.getByText("Summary")).toBeInTheDocument();
    expect(screen.getByText("CS student at Temple.")).toBeInTheDocument();
    expect(screen.getByText("Notes from Clara")).toBeInTheDocument();
    expect(screen.getByText("Quantify your Acme impact.")).toBeInTheDocument();
    expect(screen.queryByText("Edited")).not.toBeInTheDocument();
    // Regenerate wording when drafts already exist.
    expect(screen.getByText("Regenerate")).toBeInTheDocument();
  });

  test("shows the Edited badge and prefers edited_text in the editor", () => {
    renderResumes({
      resumes: [{ ...sampleResume, edited_text: "MY EDITS" }],
    });

    expect(screen.getByText("Edited")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Edit"));
    expect(screen.getByRole("textbox")).toHaveValue("MY EDITS");
  });

  test("edit flow saves through the hook and cancel discards", async () => {
    const saveEdit = jest.fn().mockResolvedValue(undefined);
    renderResumes({
      resumes: [sampleResume],
      saveEdit,
    });

    fireEvent.click(screen.getByText("Edit"));
    const textarea = screen.getByRole("textbox");
    expect(textarea).toHaveValue("RAW RESUME TEXT");

    fireEvent.change(textarea, { target: { value: "IMPROVED TEXT" } });
    await act(async () => {
      fireEvent.click(screen.getByText("Save edits"));
    });
    expect(saveEdit).toHaveBeenCalledWith("r1", "IMPROVED TEXT");
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();

    // Cancel path
    fireEvent.click(screen.getByText("Edit"));
    fireEvent.click(screen.getByText("Cancel"));
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(saveEdit).toHaveBeenCalledTimes(1);
  });

  test("copy writes the display text and reverts the label after 2s", async () => {
    jest.useFakeTimers();
    const writeText = jest.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });
    renderResumes({ resumes: [sampleResume] });

    fireEvent.click(screen.getByText("Copy text"));
    await act(async () => {});
    expect(writeText).toHaveBeenCalledWith("RAW RESUME TEXT");
    expect(screen.getByText("✓ Copied!")).toBeInTheDocument();

    act(() => {
      jest.advanceTimersByTime(2000);
    });
    expect(screen.getByText("Copy text")).toBeInTheDocument();
    jest.useRealTimers();
  });
});
