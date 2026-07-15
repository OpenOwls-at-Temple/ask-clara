import { renderHook, act } from "@testing-library/react";

jest.mock("../../src/services/assessment", () => ({
  listAssessments: jest.fn(),
  runAssessment: jest.fn(),
}));

const svc = require("../../src/services/assessment");
const { useAssessment } = require("../../src/hooks/useAssessment");

describe("useAssessment", () => {
  afterEach(() => jest.clearAllMocks());

  test("load fetches the assessment history", async () => {
    svc.listAssessments.mockResolvedValue([{ id: "a1" }]);
    const { result } = renderHook(() => useAssessment());

    await act(async () => {
      await result.current.load();
    });

    expect(result.current.assessments).toEqual([{ id: "a1" }]);
  });

  test("run prepends the new assessment to the list", async () => {
    svc.listAssessments.mockResolvedValue([{ id: "a1" }]);
    svc.runAssessment.mockResolvedValue({ id: "a2" });
    const { result } = renderHook(() => useAssessment());

    await act(async () => {
      await result.current.load();
    });
    await act(async () => {
      await result.current.run();
    });

    expect(result.current.assessments).toEqual([{ id: "a2" }, { id: "a1" }]);
  });

  test("run failure sets error and leaves the list intact", async () => {
    svc.listAssessments.mockResolvedValue([{ id: "a1" }]);
    svc.runAssessment.mockRejectedValue(new Error("429"));
    const { result } = renderHook(() => useAssessment());

    await act(async () => {
      await result.current.load();
    });
    await act(async () => {
      await result.current.run();
    });

    expect(result.current.error).toEqual(new Error("429"));
    expect(result.current.assessments).toEqual([{ id: "a1" }]);
  });
});
