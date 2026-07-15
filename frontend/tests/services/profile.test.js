import {
  getProfile,
  updateProfile,
  uploadResume,
  submitLinkedIn,
  uploadLinkedInExport,
} from "../../src/services/profile";

function jsonResponse(body) {
  return { ok: true, status: 200, json: async () => body };
}

describe("profile service", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue(jsonResponse({}));
  });

  test("getProfile GETs /profile", async () => {
    await getProfile();
    expect(fetch.mock.calls[0][0]).toBe("/api/profile");
  });

  test("updateProfile PUTs the body as JSON", async () => {
    await updateProfile({ major_program: "CS" });
    expect(fetch).toHaveBeenCalledWith(
      "/api/profile",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ major_program: "CS" }),
        headers: expect.objectContaining({
          "Content-Type": "application/json",
        }),
      }),
    );
  });

  test("uploadResume sends the file as FormData without manual Content-Type", async () => {
    const file = new File(["resume"], "resume.pdf", {
      type: "application/pdf",
    });
    await uploadResume(file);
    const [path, options] = fetch.mock.calls[0];
    expect(path).toBe("/api/profile/resume");
    expect(options.method).toBe("POST");
    expect(options.body).toBeInstanceOf(FormData);
    expect(options.body.get("file")).toBe(file);
    // The browser must set the multipart boundary itself.
    expect(options.headers).not.toHaveProperty("Content-Type");
  });

  test("submitLinkedIn POSTs the url as JSON", async () => {
    await submitLinkedIn("https://linkedin.com/in/test");
    expect(fetch).toHaveBeenCalledWith(
      "/api/profile/linkedin",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ url: "https://linkedin.com/in/test" }),
      }),
    );
  });

  test("uploadLinkedInExport sends the file as FormData", async () => {
    const file = new File(["export"], "linkedin.pdf", {
      type: "application/pdf",
    });
    await uploadLinkedInExport(file);
    const [path, options] = fetch.mock.calls[0];
    expect(path).toBe("/api/profile/linkedin/upload");
    expect(options.body).toBeInstanceOf(FormData);
    expect(options.body.get("file")).toBe(file);
  });
});
