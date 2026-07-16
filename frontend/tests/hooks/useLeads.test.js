import { renderHook, act, waitFor } from "@testing-library/react";

jest.mock("../../src/services/leads", () => ({
  listLeads: jest.fn(),
  markLeadsSeen: jest.fn(),
  updateLeadStatus: jest.fn(),
  runScan: jest.fn(),
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

  test("scan reloads leads and reports how many were found", async () => {
    svc.runScan.mockResolvedValue({ created: 2 });
    svc.listLeads.mockResolvedValue([
      { id: "1", status: "new" },
      { id: "2", status: "new" },
    ]);
    svc.markLeadsSeen.mockResolvedValue({});
    const { result } = renderHook(() => useLeads());

    await act(async () => {
      await result.current.scan();
    });

    expect(svc.runScan).toHaveBeenCalledTimes(1);
    expect(result.current.leads).toHaveLength(2);
    expect(result.current.scanNotice).toMatch(/Found 2 new leads/);
    expect(result.current.scanning).toBe(false);
    expect(result.current.error).toBeNull();
  });

  test("scan with zero matches sets the keep-scanning notice", async () => {
    svc.runScan.mockResolvedValue({ created: 0 });
    svc.listLeads.mockResolvedValue([]);
    const { result } = renderHook(() => useLeads());

    await act(async () => {
      await result.current.scan();
    });

    expect(result.current.scanNotice).toMatch(/No new matches/);
  });

  test("scan 429 shows the once-per-day notice without setting error", async () => {
    svc.runScan.mockRejectedValue(new Error("429"));
    const { result } = renderHook(() => useLeads());

    await act(async () => {
      await result.current.scan();
    });

    expect(result.current.scanNotice).toMatch(/last 24 hours/);
    expect(result.current.error).toBeNull();
    expect(svc.listLeads).not.toHaveBeenCalled();
  });

  test("scan 400 prompts for target roles without setting error", async () => {
    svc.runScan.mockRejectedValue(new Error("400"));
    const { result } = renderHook(() => useLeads());

    await act(async () => {
      await result.current.scan();
    });

    expect(result.current.scanNotice).toMatch(/target roles/);
    expect(result.current.error).toBeNull();
  });

  test("scan server failure sets error", async () => {
    svc.runScan.mockRejectedValue(new Error("503"));
    const { result } = renderHook(() => useLeads());

    await act(async () => {
      await result.current.scan();
    });

    expect(result.current.error).toEqual(new Error("503"));
    expect(result.current.scanNotice).toBeNull();
  });
});
