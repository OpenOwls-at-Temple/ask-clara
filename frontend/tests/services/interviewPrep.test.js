import {
  generateLeadPrep,
  generatePostingPrep,
  generateRolePrep,
  listInterviewPreps,
} from "../../src/services/interviewPrep";

function jsonResponse(body) {
  return { ok: true, status: 200, json: async () => body };
}

describe("interviewPrep service", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue(jsonResponse({}));
  });

  test("generateRolePrep POSTs the target rank", async () => {
    await generateRolePrep(2);
    expect(fetch).toHaveBeenCalledWith(
      "/api/interview-prep",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ target_rank: 2 }),
      }),
    );
  });

  test("generatePostingPrep POSTs the posting under a posting key", async () => {
    const posting = { title: "SWE Intern", employer: "Acme" };
    await generatePostingPrep(posting);
    expect(fetch).toHaveBeenCalledWith(
      "/api/interview-prep",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ posting }),
      }),
    );
  });

  test("generateLeadPrep POSTs to the lead-scoped endpoint", async () => {
    await generateLeadPrep("lead-1");
    expect(fetch).toHaveBeenCalledWith(
      "/api/leads/lead-1/interview-prep",
      expect.objectContaining({ method: "POST" }),
    );
  });

  test("listInterviewPreps GETs /interview-prep", async () => {
    await listInterviewPreps();
    expect(fetch.mock.calls[0][0]).toBe("/api/interview-prep");
  });
});
