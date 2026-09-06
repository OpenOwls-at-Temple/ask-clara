import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import InterviewPrep from "../src/pages/InterviewPrep";

jest.mock("../src/hooks/useInterviewPrep", () => ({
  useInterviewPrep: jest.fn(),
}));
jest.mock("../src/hooks/useProfile", () => ({
  useProfile: jest.fn(),
}));
jest.mock("../src/components/NavBar", () => () => <nav />);

const { useInterviewPrep } = require("../src/hooks/useInterviewPrep");
const { useProfile } = require("../src/hooks/useProfile");

function renderPage(routerProps = {}) {
  return render(
    <MemoryRouter {...routerProps}>
      <InterviewPrep />
    </MemoryRouter>,
  );
}

const baseHook = {
  preps: null,
  loading: false,
  generating: false,
  error: null,
  load: jest.fn(),
  generateForRole: jest.fn(),
  generateForPosting: jest.fn(),
  generateForLead: jest.fn(),
};

const sampleDoc = {
  id: "prep-1",
  lead_id: null,
  target: { mode: "role", title: "Software Engineer", rank: 1, url: null },
  formats: [
    {
      name: "Technical screen",
      what_to_expect: "One coding problem live.",
      how_to_prepare: "Practice narrating your approach.",
    },
  ],
  focus_areas: [
    {
      area: "Data structures",
      why: "Every screen tests them.",
      how_to_prepare: "Drill arrays, hash maps, and trees.",
    },
  ],
  practice_questions: [
    {
      question: "Tell me about a project you shipped.",
      type: "behavioral",
      what_they_look_for: "Ownership and clear communication.",
    },
  ],
  questions_to_ask: ["How is success measured in the first six months?"],
  notes_for_student: ["Book a mock interview with the Career Center."],
  created_at: "2026-09-06T12:00:00Z",
};

const profileWithRoles = {
  profile: {
    target_roles: [
      { rank: 2, title: "Data Analyst" },
      { rank: 1, title: "Software Engineer" },
    ],
  },
};

describe("InterviewPrep page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useProfile.mockReturnValue(profileWithRoles);
  });

  test("renders the empty state when there is no saved prep", () => {
    useInterviewPrep.mockReturnValue({ ...baseHook, preps: [] });
    renderPage();
    expect(screen.getByText("No interview prep yet")).toBeInTheDocument();
  });

  test("lists the student's ranked roles and generates prep for the chosen one", () => {
    const generateForRole = jest.fn().mockResolvedValue(sampleDoc);
    useInterviewPrep.mockReturnValue({
      ...baseHook,
      preps: [],
      generateForRole,
    });
    renderPage();

    const select = screen.getByLabelText("Target role");
    // Ranked order, not the order the API returned them in.
    expect(Array.from(select.options).map((o) => o.textContent)).toEqual([
      "#1 — Software Engineer",
      "#2 — Data Analyst",
    ]);

    fireEvent.change(select, { target: { value: "2" } });
    fireEvent.click(screen.getByText("Get interview prep"));
    expect(generateForRole).toHaveBeenCalledWith(2);
  });

  test("role mode is blocked until the student has ranked roles", () => {
    useProfile.mockReturnValue({ profile: { target_roles: [] } });
    useInterviewPrep.mockReturnValue({ ...baseHook, preps: [] });
    renderPage();

    expect(
      screen.getByText(/Add your ranked target roles in your profile first/),
    ).toBeInTheDocument();
    expect(screen.getByText("Get interview prep")).toBeDisabled();
  });

  test("posting mode needs a title and sends the posting fields", () => {
    const generateForPosting = jest.fn().mockResolvedValue(sampleDoc);
    useInterviewPrep.mockReturnValue({
      ...baseHook,
      preps: [],
      generateForPosting,
    });
    renderPage();

    fireEvent.change(screen.getByLabelText("What are you preparing for?"), {
      target: { value: "posting" },
    });

    const button = screen.getByText("Get interview prep");
    expect(button).toBeDisabled();

    fireEvent.change(screen.getByLabelText("Job title"), {
      target: { value: "SWE Intern" },
    });
    fireEvent.change(screen.getByLabelText("Company"), {
      target: { value: "Acme" },
    });
    expect(button).not.toBeDisabled();

    fireEvent.click(button);
    expect(generateForPosting).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "SWE Intern",
        employer: "Acme",
        description: null,
      }),
    );
  });

  test("arriving from a job lead locks the posting identity and uses the lead endpoint", () => {
    const generateForLead = jest.fn().mockResolvedValue(sampleDoc);
    useInterviewPrep.mockReturnValue({
      ...baseHook,
      preps: [],
      generateForLead,
    });
    renderPage({
      initialEntries: [
        {
          pathname: "/interview-prep",
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

    fireEvent.click(screen.getByText("Get interview prep"));
    expect(generateForLead).toHaveBeenCalledWith("lead-1");
  });

  test("a saved guide expands to show formats, focus areas, and practice questions", () => {
    useInterviewPrep.mockReturnValue({ ...baseHook, preps: [sampleDoc] });
    renderPage();

    fireEvent.click(screen.getByText("View"));

    expect(screen.getByText("Technical screen")).toBeInTheDocument();
    expect(screen.getByText("One coding problem live.")).toBeInTheDocument();
    expect(screen.getByText("Data structures")).toBeInTheDocument();
    expect(
      screen.getByText(/Tell me about a project you shipped/),
    ).toBeInTheDocument();
    expect(screen.getByText("behavioral")).toBeInTheDocument();
    expect(
      screen.getByText("How is success measured in the first six months?"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Book a mock interview with the Career Center."),
    ).toBeInTheDocument();
  });

  test("shows the quota message on a 429 error", () => {
    useInterviewPrep.mockReturnValue({
      ...baseHook,
      preps: [],
      error: new Error("429"),
    });
    renderPage();
    expect(
      screen.getByText(/generation limit for this pilot/i),
    ).toBeInTheDocument();
  });
});
