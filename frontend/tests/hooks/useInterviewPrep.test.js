import { renderHook, act } from "@testing-library/react";

jest.mock("../../src/services/interviewPrep", () => ({
  generateLeadPrep: jest.fn(),
  generatePostingPrep: jest.fn(),
  generateRolePrep: jest.fn(),
  listInterviewPreps: jest.fn(),
}));

const svc = require("../../src/services/interviewPrep");
const { useInterviewPrep } = require("../../src/hooks/useInterviewPrep");

const samplePrep = { id: "prep-1", target: { mode: "role", title: "SWE" } };

describe("useInterviewPrep", () => {
  afterEach(() => jest.clearAllMocks());

  test("load fetches saved prep guides", async () => {
    svc.listInterviewPreps.mockResolvedValue([samplePrep]);
    const { result } = renderHook(() => useInterviewPrep());

    await act(async () => {
      await result.current.load();
    });

    expect(result.current.preps).toEqual([samplePrep]);
  });

  test("generateForRole prepends the new prep and clears the error", async () => {
    svc.listInterviewPreps.mockRejectedValue(new Error("500"));
    svc.generateRolePrep.mockResolvedValue(samplePrep);
    const { result } = renderHook(() => useInterviewPrep());

    await act(async () => {
      await result.current.load();
    });
    expect(result.current.error).not.toBeNull();

    await act(async () => {
      await result.current.generateForRole(1);
    });

    expect(svc.generateRolePrep).toHaveBeenCalledWith(1);
    expect(result.current.error).toBeNull();
    expect(result.current.preps).toEqual([samplePrep]);
  });

  test("generateForPosting passes the posting through", async () => {
    const posting = { title: "SWE Intern" };
    svc.generatePostingPrep.mockResolvedValue(samplePrep);
    const { result } = renderHook(() => useInterviewPrep());

    await act(async () => {
      await result.current.generateForPosting(posting);
    });

    expect(svc.generatePostingPrep).toHaveBeenCalledWith(posting);
  });

  test("generateForLead uses the lead-scoped call", async () => {
    svc.generateLeadPrep.mockResolvedValue(samplePrep);
    const { result } = renderHook(() => useInterviewPrep());

    await act(async () => {
      await result.current.generateForLead("lead-1");
    });

    expect(svc.generateLeadPrep).toHaveBeenCalledWith("lead-1");
    expect(result.current.preps).toEqual([samplePrep]);
  });

  test("a failed generation sets the error and returns null", async () => {
    svc.generateRolePrep.mockRejectedValue(new Error("429"));
    const { result } = renderHook(() => useInterviewPrep());

    let returned;
    await act(async () => {
      returned = await result.current.generateForRole(1);
    });

    expect(returned).toBeNull();
    expect(result.current.error).toEqual(new Error("429"));
    expect(result.current.generating).toBe(false);
  });
});
