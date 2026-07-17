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
jest.mock("../src/services/assessment", () => ({
  listAssessments: jest.fn(),
}));
jest.mock("../src/services/documents", () => ({
  listResumes: jest.fn(),
}));
jest.mock("../src/services/plan", () => ({
  getPlan: jest.fn(),
}));
jest.mock("../src/services/materials", () => ({
  listMaterials: jest.fn(),
}));
jest.mock("../src/components/NavBar", () => () => <nav />);
jest.mock("../src/utils/tutorial", () => ({
  hasSeenTutorial: jest.fn(),
  markTutorialSeen: jest.fn(),
}));

const { useAuth } = require("../src/hooks/useAuth");
const { useProfile } = require("../src/hooks/useProfile");
const { listLeads } = require("../src/services/leads");
const { listAssessments } = require("../src/services/assessment");
const { listResumes } = require("../src/services/documents");
const { getPlan } = require("../src/services/plan");
const { listMaterials } = require("../src/services/materials");
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
    listAssessments.mockResolvedValue([]);
    listResumes.mockResolvedValue([]);
    getPlan.mockResolvedValue(null);
    listMaterials.mockResolvedValue([]);
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

  test.each([
    ["assessment", () => listAssessments.mockResolvedValue([{ id: "a1" }])],
    ["resumes", () => listResumes.mockResolvedValue([{ id: "r1" }])],
    ["plan", () => getPlan.mockResolvedValue({ id: "p1" })],
    ["materials", () => listMaterials.mockResolvedValue([{ id: "m1" }])],
  ])(
    "the %s card turns green once the feature has been run",
    async (_, arm) => {
      useProfile.mockReturnValue({ profile: completeProfile, loading: false });
      arm();
      await renderDashboard();

      // Profile card + the one run feature card
      await waitFor(() =>
        expect(screen.getAllByText("Complete")).toHaveLength(2),
      );
      expect(screen.getAllByText("Ready")).toHaveLength(3);
    },
  );

  test("the leads card goes green when any leads exist, even none new", async () => {
    useProfile.mockReturnValue({ profile: completeProfile, loading: false });
    listLeads.mockResolvedValue([{ status: "seen" }, { status: "applied" }]);
    const { container } = await renderDashboard();

    // Profile card + leads card carry the complete styling
    await waitFor(() =>
      expect(container.querySelectorAll(".card-complete")).toHaveLength(2),
    );
    expect(screen.getByText("Up to date")).toBeInTheDocument();
  });

  test("feature cards show Loading — never red — while run checks are in flight", async () => {
    useProfile.mockReturnValue({ profile: completeProfile, loading: false });
    listLeads.mockReturnValue(new Promise(() => {}));
    listAssessments.mockReturnValue(new Promise(() => {}));
    listResumes.mockReturnValue(new Promise(() => {}));
    getPlan.mockReturnValue(new Promise(() => {}));
    listMaterials.mockReturnValue(new Promise(() => {}));
    const { container } = await renderDashboard();

    expect(screen.getAllByText("Loading…")).toHaveLength(5);
    expect(screen.queryByText("Ready")).toBeNull();
    expect(container.querySelector(".icon-cherry")).toBeNull();
  });

  test("artifact fetch failures leave the cards in their Ready state", async () => {
    useProfile.mockReturnValue({ profile: completeProfile, loading: false });
    listAssessments.mockRejectedValue(new Error("500"));
    listResumes.mockRejectedValue(new Error("500"));
    getPlan.mockRejectedValue(new Error("500"));
    listMaterials.mockRejectedValue(new Error("500"));
    await renderDashboard();

    expect(screen.getAllByText("Ready")).toHaveLength(4);
  });

  test("artifact endpoints are not called while the profile is incomplete", async () => {
    useProfile.mockReturnValue({ profile: null, loading: false });
    await renderDashboard();

    expect(listAssessments).not.toHaveBeenCalled();
    expect(getPlan).not.toHaveBeenCalled();
  });

  test("shows the first-gen resources panel only for first-gen students", async () => {
    useProfile.mockReturnValue({
      profile: { ...completeProfile, is_first_gen: true },
      loading: false,
    });
    const { unmount } = await renderDashboard();
    expect(screen.getByText("First-Generation Resources")).toBeInTheDocument();
    unmount();

    useProfile.mockReturnValue({ profile: completeProfile, loading: false });
    await renderDashboard();
    expect(screen.queryByText("First-Generation Resources")).toBeNull();
  });
});
