import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import JobLeads from "../src/pages/JobLeads";

jest.mock("../src/hooks/useLeads", () => ({
  useLeads: jest.fn(),
}));
jest.mock("../src/components/NavBar", () => () => <nav />);

const { useLeads } = require("../src/hooks/useLeads");

function renderLeads() {
  return render(
    <MemoryRouter>
      <JobLeads />
    </MemoryRouter>,
  );
}

const baseHook = {
  leads: null,
  loading: false,
  error: null,
  load: jest.fn(),
  setStatus: jest.fn(),
};

const sampleLeads = [
  {
    id: "lead-1",
    source: "greenhouse",
    url: "https://boards.greenhouse.io/acme/jobs/1",
    title: "Software Engineer Intern",
    employer: "Acme",
    fit_score: 0.92,
    fit_reason: "Matches your rank-1 role and internship stage.",
    status: "seen",
    wasNew: true,
    found_at: "2026-07-11T12:00:00Z",
  },
  {
    id: "lead-2",
    source: "lever",
    url: "https://jobs.lever.co/other/2",
    title: "Data Analyst",
    employer: "OtherCo",
    fit_score: 0.6,
    fit_reason: "Related to your rank-2 role.",
    status: "dismissed",
    wasNew: false,
    found_at: "2026-07-10T12:00:00Z",
  },
];

describe("JobLeads page", () => {
  test("renders empty state when there are no leads", () => {
    useLeads.mockReturnValue({ ...baseHook, leads: [] });
    renderLeads();
    expect(screen.getByText("No leads yet")).toBeInTheDocument();
  });

  test("renders lead with fit badge, reason, and original link", () => {
    useLeads.mockReturnValue({ ...baseHook, leads: sampleLeads });
    renderLeads();
    expect(screen.getByText("Software Engineer Intern")).toBeInTheDocument();
    expect(screen.getByText("92% fit")).toBeInTheDocument();
    expect(
      screen.getByText("Matches your rank-1 role and internship stage."),
    ).toBeInTheDocument();
    const link = screen.getByText("View posting ↗");
    expect(link.getAttribute("href")).toBe(
      "https://boards.greenhouse.io/acme/jobs/1",
    );
    expect(link.getAttribute("target")).toBe("_blank");
  });

  test("shows New chip for leads that were unseen at load time", () => {
    useLeads.mockReturnValue({ ...baseHook, leads: sampleLeads });
    renderLeads();
    expect(screen.getByText("New")).toBeInTheDocument();
  });

  test("dismissed leads are hidden behind the Dismissed toggle", () => {
    useLeads.mockReturnValue({ ...baseHook, leads: sampleLeads });
    renderLeads();
    expect(screen.queryByText("Data Analyst")).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("Show"));
    expect(screen.getByText("Data Analyst")).toBeInTheDocument();
  });

  test("action buttons call setStatus with the right transition", () => {
    const setStatus = jest.fn();
    useLeads.mockReturnValue({ ...baseHook, leads: sampleLeads, setStatus });
    renderLeads();
    fireEvent.click(screen.getByText("I applied"));
    expect(setStatus).toHaveBeenCalledWith("lead-1", "applied");
    fireEvent.click(screen.getByText("Dismiss"));
    expect(setStatus).toHaveBeenCalledWith("lead-1", "dismissed");
  });

  test("shows error banner when the hook reports an error", () => {
    useLeads.mockReturnValue({ ...baseHook, error: new Error("500") });
    renderLeads();
    expect(screen.getByText(/500/)).toBeInTheDocument();
  });
});
