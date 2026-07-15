import { runAssessment, listAssessments } from "../../src/services/assessment";

function jsonResponse(body) {
  return { ok: true, status: 200, json: async () => body };
}

describe("assessment service", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue(jsonResponse([]));
  });

  test("runAssessment POSTs to /assessment", async () => {
    await runAssessment();
    expect(fetch).toHaveBeenCalledWith(
      "/api/assessment",
      expect.objectContaining({ method: "POST" }),
    );
  });

  test("listAssessments GETs /assessment", async () => {
    await listAssessments();
    const [path, options] = fetch.mock.calls[0];
    expect(path).toBe("/api/assessment");
    expect(options.method).toBeUndefined();
  });
});
