import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import HowItWorks from "../src/pages/HowItWorks";

jest.mock("../src/hooks/useProfile", () => ({
  useProfile: jest.fn(),
}));
jest.mock("../src/utils/tutorial", () => ({
  markTutorialSeen: jest.fn(),
}));
jest.mock("../src/components/NavBar", () => () => <nav />);

const { useProfile } = require("../src/hooks/useProfile");
const { markTutorialSeen } = require("../src/utils/tutorial");

const completeProfile = {
  resume_doc_id: "doc-1",
  target_roles: [{ rank: 1 }, { rank: 2 }, { rank: 3 }],
};

function renderHowItWorks() {
  return render(
    <MemoryRouter initialEntries={["/how-it-works"]}>
      <Routes>
        <Route path="/how-it-works" element={<HowItWorks />} />
        <Route path="/dashboard" element={<div>DASHBOARD PROBE</div>} />
        <Route path="/intake" element={<div>INTAKE PROBE</div>} />
        <Route path="/leads" element={<div>LEADS PROBE</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("HowItWorks page", () => {
  afterEach(() => jest.clearAllMocks());

  test("renders the six steps in order", () => {
    useProfile.mockReturnValue({ profile: null, loading: false });
    renderHowItWorks();

    expect(screen.getByText("How Clara works")).toBeInTheDocument();
    const titles = screen
      .getAllByRole("listitem")
      .map((li) => li.querySelector(".card-title").textContent);
    expect(titles).toEqual([
      "Build your profile",
      "Run your AI assessment",
      "Generate tailored resumes",
      "Follow your 6-month plan",
      "Review matched job leads",
      "Create application materials",
    ]);
  });

  test("marks the tutorial as seen on mount", () => {
    useProfile.mockReturnValue({ profile: null, loading: false });
    renderHowItWorks();

    expect(markTutorialSeen).toHaveBeenCalledTimes(1);
  });

  test("incomplete profile gates steps 2-6 and shows the get-started CTA", () => {
    useProfile.mockReturnValue({ profile: null, loading: false });
    renderHowItWorks();

    expect(screen.getAllByText("Unlocks after step 1")).toHaveLength(5);

    fireEvent.click(screen.getByText("Get Started — Build Your Profile →"));
    expect(screen.getByText("INTAKE PROBE")).toBeInTheDocument();
  });

  test("step 1 deep link works even with an incomplete profile", () => {
    useProfile.mockReturnValue({ profile: null, loading: false });
    renderHowItWorks();

    fireEvent.click(screen.getByText("Go to Profile →"));
    expect(screen.getByText("INTAKE PROBE")).toBeInTheDocument();
  });

  test("complete profile unlocks all deep links and flips the CTA", () => {
    useProfile.mockReturnValue({ profile: completeProfile, loading: false });
    renderHowItWorks();

    expect(screen.queryByText("Unlocks after step 1")).not.toBeInTheDocument();

    fireEvent.click(screen.getByText("Go to Leads →"));
    expect(screen.getByText("LEADS PROBE")).toBeInTheDocument();
  });

  test("complete profile CTA returns to the dashboard", () => {
    useProfile.mockReturnValue({ profile: completeProfile, loading: false });
    renderHowItWorks();

    fireEvent.click(screen.getByText("Back to Dashboard →"));
    expect(screen.getByText("DASHBOARD PROBE")).toBeInTheDocument();
  });

  test("no CTA banner while the profile is loading", () => {
    useProfile.mockReturnValue({ profile: null, loading: true });
    const { container } = renderHowItWorks();

    expect(container.querySelector(".next-step-banner")).toBeNull();
  });

  test("includes the Career Center note", () => {
    useProfile.mockReturnValue({ profile: null, loading: false });
    renderHowItWorks();

    expect(
      screen.getByText(/complements the Temple Career Center/),
    ).toBeInTheDocument();
  });
});
