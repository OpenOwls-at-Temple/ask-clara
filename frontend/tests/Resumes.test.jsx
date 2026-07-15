import { render, screen, fireEvent, waitFor } from "@testing-library/react";
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
  id: "res-1",
  target_rank: 1,
  target_title: "Software Engineer",
  sections: [{ heading: "Skills", content: "Python, FastAPI" }],
  notes_for_student: [],
  raw_text: "SKILLS\nPython, FastAPI",
  edited_text: null,
  created_at: "2026-07-15T12:00:00Z",
};

const baseHook = {
  resumes: [sampleResume],
  loading: false,
  error: null,
  load: jest.fn(),
  generate: jest.fn(),
  saveEdit: jest.fn(),
};

function renderResumes(overrides = {}) {
  useResumes.mockReturnValue({ ...baseHook, ...overrides });
  return render(
    <MemoryRouter>
      <Resumes />
    </MemoryRouter>,
  );
}

describe("Resumes page — PDF preview and downloads", () => {
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
    expect(fetchResumePdf).toHaveBeenCalledWith("res-1", "png");

    fireEvent.click(screen.getByText("Download resume"));
    await waitFor(() =>
      expect(saveBlob).toHaveBeenCalledWith(
        pdfBlob,
        "clara-resume-software-engineer.pdf",
      ),
    );
    expect(fetchResumePdf).toHaveBeenCalledWith("res-1", "pdf");

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
        "res-1",
        "clara-resume-software-engineer.docx",
        "docx",
      ),
    );
  });
});
