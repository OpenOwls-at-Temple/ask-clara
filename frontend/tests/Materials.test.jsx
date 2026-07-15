import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Materials from "../src/pages/Materials";

jest.mock("../src/hooks/useMaterials", () => ({
  useMaterials: jest.fn(),
}));
jest.mock("../src/services/materials", () => ({
  fetchPosting: jest.fn(),
}));
jest.mock("../src/services/documents", () => ({
  fetchMaterialsResumePdf: jest.fn(),
  saveBlob: jest.fn(),
}));
jest.mock("../src/components/NavBar", () => () => <nav />);

const { useMaterials } = require("../src/hooks/useMaterials");
const { fetchPosting } = require("../src/services/materials");
const {
  fetchMaterialsResumePdf,
  saveBlob,
} = require("../src/services/documents");

beforeAll(() => {
  global.URL.createObjectURL = jest.fn(() => "blob:mock");
  global.URL.revokeObjectURL = jest.fn();
});

function renderMaterials(routerProps = {}) {
  return render(
    <MemoryRouter {...routerProps}>
      <Materials />
    </MemoryRouter>,
  );
}

const baseHook = {
  materials: null,
  loading: false,
  generating: false,
  error: null,
  load: jest.fn(),
  generate: jest.fn(),
};

const sampleDoc = {
  id: "mat-1",
  lead_id: null,
  posting: {
    title: "Software Engineer Intern",
    employer: "Acme",
    location: "Philadelphia",
    url: "https://acme.example/jobs/1",
    description: "Build APIs.",
  },
  fit_summary: "Your Python projects line up well with this posting.",
  resume_sections: [{ heading: "Skills", content: "Python, FastAPI" }],
  cover_letter: "Dear Hiring Team, I am excited to apply.",
  employer_brief: "Acme builds developer tools.",
  notes_for_student: ["Consider adding a SQL certification."],
  created_at: "2026-07-13T12:00:00Z",
};

describe("Materials page", () => {
  beforeEach(() => jest.clearAllMocks());

  test("renders empty state when there are no materials", () => {
    useMaterials.mockReturnValue({ ...baseHook, materials: [] });
    renderMaterials();
    expect(screen.getByText("No tailored materials yet")).toBeInTheDocument();
  });

  test("fetching a posting link prefills the form", async () => {
    useMaterials.mockReturnValue({ ...baseHook, materials: [] });
    fetchPosting.mockResolvedValue({
      title: "Data Analyst",
      employer: "OtherCo",
      location: "Remote",
      description: "Analyze data with SQL.",
      url: "https://otherco.example/jobs/2",
    });
    renderMaterials();

    fireEvent.change(screen.getByLabelText("Job posting link"), {
      target: { value: "https://otherco.example/jobs/2" },
    });
    fireEvent.click(screen.getByText("Fetch details"));

    await waitFor(() =>
      expect(screen.getByLabelText("Job title")).toHaveValue("Data Analyst"),
    );
    expect(screen.getByLabelText("Company")).toHaveValue("OtherCo");
    expect(screen.getByLabelText(/Job description/)).toHaveValue(
      "Analyze data with SQL.",
    );
    expect(fetchPosting).toHaveBeenCalledWith("https://otherco.example/jobs/2");
  });

  test("failed fetch tells the student to enter details manually", async () => {
    useMaterials.mockReturnValue({ ...baseHook, materials: [] });
    fetchPosting.mockRejectedValue(new Error("422"));
    renderMaterials();

    fireEvent.change(screen.getByLabelText("Job posting link"), {
      target: { value: "https://broken.example/x" },
    });
    fireEvent.click(screen.getByText("Fetch details"));

    await waitFor(() =>
      expect(
        screen.getByText(/paste the job details manually/i),
      ).toBeInTheDocument(),
    );
  });

  test("generate stays disabled until the manual posting is complete", () => {
    const generate = jest.fn().mockResolvedValue(sampleDoc);
    useMaterials.mockReturnValue({ ...baseHook, materials: [], generate });
    renderMaterials();

    const button = screen.getByText("Generate materials");
    expect(button).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Job title"), {
      target: { value: "SWE Intern" },
    });
    fireEvent.change(screen.getByLabelText("Company"), {
      target: { value: "Acme" },
    });
    fireEvent.change(screen.getByLabelText(/Job description/), {
      target: { value: "Build APIs in Python." },
    });
    expect(button).not.toBeDisabled();

    fireEvent.click(button);
    expect(generate).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "SWE Intern",
        employer: "Acme",
        description: "Build APIs in Python.",
      }),
      undefined,
    );
  });

  test("saved materials expand to show fit, brief, letter, resume actions, and notes", () => {
    fetchMaterialsResumePdf.mockResolvedValue(new Blob(["%PDF"]));
    useMaterials.mockReturnValue({ ...baseHook, materials: [sampleDoc] });
    renderMaterials();

    expect(screen.getByText("Software Engineer Intern")).toBeInTheDocument();
    fireEvent.click(screen.getByText("View"));

    expect(
      screen.getByText("Your Python projects line up well with this posting."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Acme builds developer tools."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Dear Hiring Team, I am excited to apply."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Consider adding a SQL certification."),
    ).toBeInTheDocument();

    // The resume text is not dumped on the page — it lives in the inline
    // PDF preview and the copy popup.
    expect(screen.queryByText("Python, FastAPI")).toBeNull();
    expect(screen.getByText("Copy resume")).toBeInTheDocument();
  });

  test("arriving from a job lead prefills and locks the posting identity", () => {
    const generate = jest.fn().mockResolvedValue(sampleDoc);
    useMaterials.mockReturnValue({ ...baseHook, materials: [], generate });
    renderMaterials({
      initialEntries: [
        {
          pathname: "/materials",
          state: {
            lead: {
              id: "lead-1",
              title: "Software Engineer Intern",
              employer: "Acme",
              url: "https://acme.example/jobs/1",
            },
          },
        },
      ],
    });

    expect(screen.getByLabelText("Job title")).toHaveValue(
      "Software Engineer Intern",
    );
    expect(screen.getByLabelText("Job title")).toBeDisabled();
    expect(screen.getByLabelText("Company")).toBeDisabled();

    // Description optional for a lead — Clara can read the posting page.
    const button = screen.getByText("Generate materials");
    expect(button).not.toBeDisabled();
    fireEvent.click(button);
    expect(generate).toHaveBeenCalledWith(expect.any(Object), "lead-1");
  });

  test("expanding a card shows the resume image inline with a download button", async () => {
    const pngBlob = new Blob(["PNG"], { type: "image/png" });
    const pdfBlob = new Blob(["%PDF"], { type: "application/pdf" });
    fetchMaterialsResumePdf.mockImplementation((id, format) =>
      Promise.resolve(format === "png" ? pngBlob : pdfBlob),
    );
    useMaterials.mockReturnValue({ ...baseHook, materials: [sampleDoc] });
    renderMaterials();

    fireEvent.click(screen.getByText("View"));
    await waitFor(() =>
      expect(screen.getByAltText("Resume PDF preview")).toBeInTheDocument(),
    );
    expect(fetchMaterialsResumePdf).toHaveBeenCalledWith("mat-1", "png");

    // Download fetches the real PDF, not the preview image.
    fireEvent.click(screen.getByText("Download resume"));
    await waitFor(() =>
      expect(saveBlob).toHaveBeenCalledWith(
        pdfBlob,
        "clara-resume-software-engineer-intern.pdf",
      ),
    );
    expect(fetchMaterialsResumePdf).toHaveBeenCalledWith("mat-1", "pdf");
  });

  test("failed PDF rendering shows the copy-text fallback inline", async () => {
    fetchMaterialsResumePdf.mockRejectedValueOnce(new Error("503"));
    useMaterials.mockReturnValue({ ...baseHook, materials: [sampleDoc] });
    renderMaterials();

    fireEvent.click(screen.getByText("View"));
    await waitFor(() =>
      expect(screen.getByText(/PDF generation failed/)).toBeInTheDocument(),
    );
  });

  test("Copy resume opens a popup with the resume text", async () => {
    const writeText = jest.fn().mockResolvedValue();
    Object.assign(navigator, { clipboard: { writeText } });
    fetchMaterialsResumePdf.mockResolvedValue(new Blob(["%PDF"]));
    useMaterials.mockReturnValue({ ...baseHook, materials: [sampleDoc] });
    renderMaterials();
    fireEvent.click(screen.getByText("View"));

    fireEvent.click(screen.getByText("Copy resume"));
    expect(screen.getByText(/Python, FastAPI/)).toBeInTheDocument();

    fireEvent.click(screen.getByText("Copy text"));
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(
        expect.stringContaining("Python, FastAPI"),
      ),
    );

    fireEvent.click(screen.getByText("Close"));
    expect(screen.queryByText(/Python, FastAPI/)).toBeNull();
  });

  test("shows the quota message on a 429 error", () => {
    useMaterials.mockReturnValue({
      ...baseHook,
      materials: [],
      error: new Error("429"),
    });
    renderMaterials();
    expect(
      screen.getByText(/generation limit for this pilot/i),
    ).toBeInTheDocument();
  });
});
