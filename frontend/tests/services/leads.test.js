import {
  listLeads,
  updateLeadStatus,
  markLeadsSeen,
} from "../../src/services/leads";

function jsonResponse(body) {
  return { ok: true, status: 200, json: async () => body };
}

describe("leads service", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue(jsonResponse([]));
  });

  test("listLeads GETs /leads", async () => {
    await listLeads();
    expect(fetch.mock.calls[0][0]).toBe("/api/leads");
  });

  test("updateLeadStatus PATCHes the status to the lead id", async () => {
    await updateLeadStatus("lead-1", "applied");
    expect(fetch).toHaveBeenCalledWith(
      "/api/leads/lead-1",
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ status: "applied" }),
      }),
    );
  });

  test("markLeadsSeen POSTs to /leads/mark-seen", async () => {
    await markLeadsSeen();
    expect(fetch).toHaveBeenCalledWith(
      "/api/leads/mark-seen",
      expect.objectContaining({ method: "POST" }),
    );
  });
});
