import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Assessment from "../src/pages/Assessment";

jest.mock("../src/hooks/useAssessment", () => ({
  useAssessment: jest.fn(),
}));
jest.mock("../src/components/NavBar", () => () => <nav />);

const { useAssessment } = require("../src/hooks/useAssessment");

function renderAssessment() {
  return render(
    <MemoryRouter>
      <Assessment />
    </MemoryRouter>
  );
}

const baseHook = { assessments: [], loading: false, error: null, load: jest.fn(), run: jest.fn() };

describe("Assessment page — gap warning icon", () => {
  test("renders yellow SVG warning icon for each gap item", () => {
    useAssessment.mockReturnValue({
      ...baseHook,
      assessments: [
        {
          created_at: "2026-06-24T19:11:00Z",
          strengths: [],
          gaps: [
            { area: "Data pipeline and ETL tooling", target_rank: 2, why: "No Spark experience" },
            { area: "System design artifacts", target_rank: 1, why: "No mock interviews" },
          ],
          recommendations: [],
        },
      ],
    });

    const { container } = renderAssessment();

    // Each gap row should contain an SVG (the warning icon)
    const gapItems = container.querySelectorAll(".item-gap");
    expect(gapItems).toHaveLength(2);
    gapItems.forEach((item) => {
      expect(item.querySelector("svg")).not.toBeNull();
    });
  });

  test("SVG warning icon is NOT present on strength items", () => {
    useAssessment.mockReturnValue({
      ...baseHook,
      assessments: [
        {
          created_at: "2026-06-24T19:11:00Z",
          strengths: ["Strong Java background"],
          gaps: [],
          recommendations: [],
        },
      ],
    });

    const { container } = renderAssessment();
    const strengthItems = container.querySelectorAll(".item-strength");
    expect(strengthItems).toHaveLength(1);
    strengthItems.forEach((item) => {
      expect(item.querySelector("svg")).toBeNull();
    });
  });

  test("renders empty state when no assessment exists", () => {
    useAssessment.mockReturnValue({ ...baseHook, assessments: [] });
    renderAssessment();
    expect(screen.getByText("No assessment yet")).toBeInTheDocument();
  });

  test("renders loading spinner while running", () => {
    useAssessment.mockReturnValue({ ...baseHook, loading: true, assessments: [] });
    const { container } = renderAssessment();
    expect(container.querySelector(".spinner")).not.toBeNull();
  });
});
