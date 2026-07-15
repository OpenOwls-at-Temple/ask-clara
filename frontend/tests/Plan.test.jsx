import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Plan from "../src/pages/Plan";

jest.mock("../src/hooks/usePlan", () => ({
  usePlan: jest.fn(),
}));
jest.mock("../src/components/NavBar", () => () => <nav />);

const { usePlan } = require("../src/hooks/usePlan");

function renderPlan() {
  return render(
    <MemoryRouter>
      <Plan />
    </MemoryRouter>,
  );
}

const baseHook = {
  plan: null,
  loading: false,
  error: null,
  load: jest.fn(),
  generate: jest.fn(),
  toggleItem: jest.fn(),
};

const samplePlan = {
  id: "plan-1",
  horizon_months: 6,
  created_at: "2026-07-10T12:00:00Z",
  items: [
    {
      skill: "Build a REST API project",
      why: "Backend depth",
      target_rank: 1,
      status: "pending",
    },
    {
      skill: "AWS certification",
      why: "Cloud gap",
      target_rank: 2,
      status: "complete",
    },
  ],
};

describe("Plan page", () => {
  test("renders empty state when no plan exists", () => {
    usePlan.mockReturnValue({ ...baseHook });
    renderPlan();
    expect(screen.getByText("No plan yet")).toBeInTheDocument();
  });

  test("renders loading spinner while generating", () => {
    usePlan.mockReturnValue({ ...baseHook, loading: true });
    const { container } = renderPlan();
    expect(container.querySelector(".spinner")).not.toBeNull();
  });

  test("renders plan items with role tags and progress count", () => {
    usePlan.mockReturnValue({ ...baseHook, plan: samplePlan });
    renderPlan();
    expect(screen.getByText("Build a REST API project")).toBeInTheDocument();
    expect(screen.getByText("AWS certification")).toBeInTheDocument();
    expect(screen.getByText("Role #1")).toBeInTheDocument();
    expect(screen.getByText("1 of 2 complete")).toBeInTheDocument();
    expect(screen.getByText("50%")).toBeInTheDocument();
  });

  test("completed items get the done class and checked box", () => {
    usePlan.mockReturnValue({ ...baseHook, plan: samplePlan });
    const { container } = renderPlan();
    const done = container.querySelectorAll(".plan-item-done");
    expect(done).toHaveLength(1);
    expect(container.querySelectorAll(".plan-item-check.checked")).toHaveLength(
      1,
    );
  });

  test("clicking a checkbox calls toggleItem with the item index", () => {
    const toggleItem = jest.fn();
    usePlan.mockReturnValue({ ...baseHook, plan: samplePlan, toggleItem });
    const { container } = renderPlan();
    const checks = container.querySelectorAll(".plan-item-check");
    fireEvent.click(checks[0]);
    expect(toggleItem).toHaveBeenCalledWith(0);
  });

  test("shows error banner when the hook reports an error", () => {
    usePlan.mockReturnValue({ ...baseHook, error: new Error("503") });
    renderPlan();
    expect(screen.getByText(/503/)).toBeInTheDocument();
  });
});
