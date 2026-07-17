import {
  render,
  screen,
  fireEvent,
  act,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import Dashboard from "../src/pages/Dashboard";

jest.mock("../src/hooks/useAuth", () => ({
  useAuth: jest.fn(),
}));
jest.mock("../src/hooks/useProfile", () => ({
  useProfile: jest.fn(),
}));
jest.mock("../src/services/leads", () => ({
  listLeads: jest.fn(),
}));
jest.mock("../src/components/NavBar", () => () => <nav />);
jest.mock("../src/utils/tutorial", () => ({
  hasSeenTutorial: jest.fn(),
  markTutorialSeen: jest.fn(),
}));

const { useAuth } = require("../src/hooks/useAuth");
const { useProfile } = require("../src/hooks/useProfile");
const { listLeads } = require("../src/services/leads");
const { hasSeenTutorial, markTutorialSeen } = require("../src/utils/tutorial");

const completeProfile = {
  resume_doc_id: "doc-1",
  target_roles: [{ rank: 1 }, { rank: 2 }, { rank: 3 }],
};

async function renderDashboard() {
  const utils = render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/intake" element={<div>INTAKE PROBE</div>} />
        <Route path="/assessment" element={<div>ASSESSMENT PROBE</div>} />
        <Route path="/how-it-works" element={<div>TUTORIAL PROBE</div>} />
      </Routes>
    </MemoryRouter>,
  );
  // Flush the mount-time listLeads promise.
  await act(async () => {});
  return utils;
}

describe("Dashboard page", () => {
  beforeEach(() => {
    useAuth.mockReturnValue({ user: { display_name: "Jane Doe" } });
    listLeads.mockResolvedValue([]);
    hasSeenTutorial.mockReturnValue(true);
  });

  afterEach(() => jest.clearAllMocks());

  test("greets the user by first name, with a fallback when signed-out", async () => {
    useProfile.mockReturnValue({ profile: null, loading: false });
    const { unmount } = await renderDashboard();
    expect(screen.getByText("Hello, Jane")).toBeInTheDocument();
    unmount();

    useAuth.mockReturnValue({ user: null });
    await renderDashboard();
    expect(screen.getByText("Hello, there")).toBeInTheDocument();
  });

  test("locks the AI cards until the profile is complete", async () => {
    useProfile.mockReturnValue({ profile: null, loading: false });
    await renderDashboard();

    expect(screen.getAllByText("Profile required")).toHaveLength(5);
    expect(screen.getByText("Incomplete")).toBeInTheDocument();
    // Locked cards render disabled buttons.
    expect(screen.getByText("View / Run")).toBeDisabled();
    expect(screen.getByText("View Leads")).toBeDisabled();
  });

  test("missing resume shows the upload banner that navigates to intake", async () => {
    useProfile.mockReturnValue({ profile: null, loading: false });
    await renderDashboard();

    fireEvent.click(screen.getByText("Upload Resume →"));
    expect(screen.getByText("INTAKE PROBE")).toBeInTheDocument();
  });

  test("resume uploaded but roles missing shows the remaining-roles banner", async () => {
    useProfile.mockReturnValue({
      profile: {
        resume_doc_id: "doc-1",
        target_roles: [{ rank: 1 }, { rank: 2 }],
      },
      loading: false,
    });
    const { container, unmount } = await renderDashboard();
    expect(container.querySelector(".next-step-text").textContent).toBe(
      "Add 1 more target role to complete your profile.",
    );
    unmount();

    useProfile.mockReturnValue({
      profile: { resume_doc_id: "doc-1", target_roles: [{ rank: 1 }] },
      loading: false,
    });
    const { container: c2 } = await renderDashboard();
    expect(c2.querySelector(".next-step-text").textContent).toBe(
      "Add 2 more target roles to complete your profile.",
    );
  });

  test("a complete profile unlocks the cards and enables navigation", async () => {
    useProfile.mockReturnValue({ profile: completeProfile, loading: false });
    await renderDashboard();

    expect(screen.getByText("Complete")).toBeInTheDocument();
    expect(screen.getAllByText("Ready")).toHaveLength(4);
    expect(screen.queryByText("Profile required")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("View / Run"));
    expect(screen.getByText("ASSESSMENT PROBE")).toBeInTheDocument();
  });

  test("shows the new-leads badge from the leads service", async () => {
    useProfile.mockReturnValue({ profile: completeProfile, loading: false });
    listLeads.mockResolvedValue([
      { status: "new" },
      { status: "new" },
      { status: "seen" },
    ]);
    await renderDashboard();

    await waitFor(() => expect(screen.getByText("2 new")).toBeInTheDocument());
  });

  test("a leads fetch failure never breaks the dashboard", async () => {
    useProfile.mockReturnValue({ profile: completeProfile, loading: false });
    listLeads.mockRejectedValue(new Error("500"));
    await renderDashboard();

    expect(screen.getByText("Hello, Jane")).toBeInTheDocument();
    expect(screen.getByText("Up to date")).toBeInTheDocument();
  });

  test("welcome header links to the tutorial page", async () => {
    useProfile.mockReturnValue({ profile: completeProfile, loading: false });
    await renderDashboard();

    fireEvent.click(screen.getByText("✨ How Clara works →"));
    expect(screen.getByText("TUTORIAL PROBE")).toBeInTheDocument();
  });

  test("first visit with an incomplete profile redirects to the tutorial once", async () => {
    hasSeenTutorial.mockReturnValue(false);
    useProfile.mockReturnValue({ profile: null, loading: false });
    await renderDashboard();

    expect(screen.getByText("TUTORIAL PROBE")).toBeInTheDocument();
    expect(markTutorialSeen).toHaveBeenCalledTimes(1);
  });

  test("no tutorial redirect when already seen", async () => {
    useProfile.mockReturnValue({ profile: null, loading: false });
    await renderDashboard();

    expect(screen.queryByText("TUTORIAL PROBE")).not.toBeInTheDocument();
    expect(markTutorialSeen).not.toHaveBeenCalled();
  });

  test("no tutorial redirect when the profile is complete", async () => {
    hasSeenTutorial.mockReturnValue(false);
    useProfile.mockReturnValue({ profile: completeProfile, loading: false });
    await renderDashboard();

    expect(screen.queryByText("TUTORIAL PROBE")).not.toBeInTheDocument();
    expect(markTutorialSeen).not.toHaveBeenCalled();
  });

  test("no tutorial redirect while the profile is still loading", async () => {
    hasSeenTutorial.mockReturnValue(false);
    useProfile.mockReturnValue({ profile: null, loading: true });
    await renderDashboard();

    expect(screen.queryByText("TUTORIAL PROBE")).not.toBeInTheDocument();
    expect(markTutorialSeen).not.toHaveBeenCalled();
  });
});
