import { generatePlan, getPlan, updatePlanItem } from "../../src/services/plan";

function jsonResponse(body) {
  return { ok: true, status: 200, json: async () => body };
}

describe("plan service", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue(jsonResponse({}));
  });

  test("generatePlan POSTs to /plan/generate", async () => {
    await generatePlan();
    expect(fetch).toHaveBeenCalledWith(
      "/api/plan/generate",
      expect.objectContaining({ method: "POST" }),
    );
  });

  test("getPlan GETs /plan", async () => {
    await getPlan();
    expect(fetch.mock.calls[0][0]).toBe("/api/plan");
  });

  test("updatePlanItem PATCHes status to the plan id and item index", async () => {
    await updatePlanItem("plan-1", 2, "complete");
    expect(fetch).toHaveBeenCalledWith(
      "/api/plan/plan-1/items/2",
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ status: "complete" }),
      }),
    );
  });
});
