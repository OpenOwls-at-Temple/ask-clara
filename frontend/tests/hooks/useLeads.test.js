import { renderHook, act, waitFor } from "@testing-library/react";

jest.mock("../../src/services/leads", () => ({
  listLeads: jest.fn(),
  markLeadsSeen: jest.fn(),
  updateLeadStatus: jest.fn(),
}));

const svc = require("../../src/services/leads");
const { useLeads } = require("../../src/hooks/useLeads");

describe("useLeads", () => {
  afterEach(() => jest.clearAllMocks());

  test("load maps wasNew from status and marks leads seen", async () => {
    svc.listLeads.mockResolvedValue([
      { id: "1", status: "new" },
      { id: "2", status: "seen" },
    ]);
    svc.markLeadsSeen.mockResolvedValue({});
    const { result } = renderHook(() => useLeads());

    await act(async () => {
      await result.current.load();
    });

    expect(result.current.leads).toEqual([
      { id: "1", status: "new", wasNew: true },
      { id: "2", status: "seen", wasNew: false },
    ]);
    expect(svc.markLeadsSeen).toHaveBeenCalledTimes(1);
  });

  test("does not call markLeadsSeen when nothing is new", async () => {
    svc.listLeads.mockResolvedValue([{ id: "1", status: "seen" }]);
    const { result } = renderHook(() => useLeads());

    await act(async () => {
      await result.current.load();
    });

    expect(svc.markLeadsSeen).not.toHaveBeenCalled();
  });

  test("a markLeadsSeen failure never surfaces as an error", async () => {
    svc.listLeads.mockResolvedValue([{ id: "1", status: "new" }]);
    svc.markLeadsSeen.mockRejectedValue(new Error("500"));
    const { result } = renderHook(() => useLeads());

    await act(async () => {
      await result.current.load();
    });

    // Badge cleanup is fire-and-forget — the page must still work.
    await waitFor(() => expect(result.current.error).toBeNull());
    expect(result.current.leads).toHaveLength(1);
  });

  test("load failure sets error", async () => {
    svc.listLeads.mockRejectedValue(new Error("500"));
    const { result } = renderHook(() => useLeads());

    await act(async () => {
      await result.current.load();
    });

    expect(result.current.error).toEqual(new Error("500"));
    expect(result.current.leads).toBeNull();
  });

  test("setStatus merges the updated lead and preserves wasNew", async () => {
    svc.listLeads.mockResolvedValue([{ id: "1", status: "new" }]);
    svc.markLeadsSeen.mockResolvedValue({});
    svc.updateLeadStatus.mockResolvedValue({ id: "1", status: "applied" });
    const { result } = renderHook(() => useLeads());

    await act(async () => {
      await result.current.load();
    });
    await act(async () => {
      await result.current.setStatus("1", "applied");
    });

    expect(svc.updateLeadStatus).toHaveBeenCalledWith("1", "applied");
    expect(result.current.leads[0]).toEqual({
      id: "1",
      status: "applied",
      wasNew: true,
    });
  });

  test("setStatus failure sets error without dropping the list", async () => {
    svc.listLeads.mockResolvedValue([{ id: "1", status: "seen" }]);
    svc.updateLeadStatus.mockRejectedValue(new Error("500"));
    const { result } = renderHook(() => useLeads());

    await act(async () => {
      await result.current.load();
    });
    await act(async () => {
      await result.current.setStatus("1", "applied");
    });

    expect(result.current.error).toEqual(new Error("500"));
    expect(result.current.leads).toHaveLength(1);
  });
});
