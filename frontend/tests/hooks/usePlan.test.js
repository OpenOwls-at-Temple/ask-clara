import { renderHook, act } from "@testing-library/react";

jest.mock("../../src/services/plan", () => ({
  generatePlan: jest.fn(),
  getPlan: jest.fn(),
  updatePlanItem: jest.fn(),
}));

const svc = require("../../src/services/plan");
const { usePlan } = require("../../src/hooks/usePlan");

const samplePlan = {
  id: "plan-1",
  items: [{ status: "pending" }, { status: "complete" }],
};

describe("usePlan", () => {
  afterEach(() => jest.clearAllMocks());

  test("load fetches the plan", async () => {
    svc.getPlan.mockResolvedValue(samplePlan);
    const { result } = renderHook(() => usePlan());

    await act(async () => {
      await result.current.load();
    });

    expect(result.current.plan).toEqual(samplePlan);
  });

  test("generate stores the new plan and clears errors", async () => {
    svc.getPlan.mockRejectedValue(new Error("500"));
    svc.generatePlan.mockResolvedValue(samplePlan);
    const { result } = renderHook(() => usePlan());

    await act(async () => {
      await result.current.load();
    });
    expect(result.current.error).not.toBeNull();

    await act(async () => {
      await result.current.generate();
    });

    expect(result.current.error).toBeNull();
    expect(result.current.plan).toEqual(samplePlan);
  });

  test("toggleItem flips pending to complete and stores the server response", async () => {
    svc.getPlan.mockResolvedValue(samplePlan);
    const updated = {
      ...samplePlan,
      items: [{ status: "complete" }, { status: "complete" }],
    };
    svc.updatePlanItem.mockResolvedValue(updated);
    const { result } = renderHook(() => usePlan());

    await act(async () => {
      await result.current.load();
    });
    await act(async () => {
      await result.current.toggleItem(0);
    });

    expect(svc.updatePlanItem).toHaveBeenCalledWith("plan-1", 0, "complete");
    expect(result.current.plan).toEqual(updated);
  });

  test("toggleItem flips complete back to pending", async () => {
    svc.getPlan.mockResolvedValue(samplePlan);
    svc.updatePlanItem.mockResolvedValue(samplePlan);
    const { result } = renderHook(() => usePlan());

    await act(async () => {
      await result.current.load();
    });
    await act(async () => {
      await result.current.toggleItem(1);
    });

    expect(svc.updatePlanItem).toHaveBeenCalledWith("plan-1", 1, "pending");
  });

  test("toggleItem is a no-op when no plan is loaded", async () => {
    const { result } = renderHook(() => usePlan());

    await act(async () => {
      await result.current.toggleItem(0);
    });

    expect(svc.updatePlanItem).not.toHaveBeenCalled();
  });

  test("toggleItem failure sets error and keeps the plan", async () => {
    svc.getPlan.mockResolvedValue(samplePlan);
    svc.updatePlanItem.mockRejectedValue(new Error("500"));
    const { result } = renderHook(() => usePlan());

    await act(async () => {
      await result.current.load();
    });
    await act(async () => {
      await result.current.toggleItem(0);
    });

    expect(result.current.error).toEqual(new Error("500"));
    expect(result.current.plan).toEqual(samplePlan);
  });
});
