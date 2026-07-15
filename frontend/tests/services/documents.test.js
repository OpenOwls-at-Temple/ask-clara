import {
  generateResumes,
  listResumes,
  updateResume,
  downloadResume,
} from "../../src/services/documents";

function jsonResponse(body) {
  return { ok: true, status: 200, json: async () => body };
}

describe("documents service", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue(jsonResponse({}));
  });

  test("generateResumes POSTs to /resumes/generate", async () => {
    await generateResumes();
    expect(fetch).toHaveBeenCalledWith(
      "/api/resumes/generate",
      expect.objectContaining({ method: "POST" }),
    );
  });

  test("listResumes GETs /resumes", async () => {
    await listResumes();
    expect(fetch.mock.calls[0][0]).toBe("/api/resumes");
  });

  test("updateResume PATCHes edited_text to the resume id", async () => {
    await updateResume("r1", "new text");
    expect(fetch).toHaveBeenCalledWith(
      "/api/resumes/r1",
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({ edited_text: "new text" }),
      }),
    );
  });

  describe("downloadResume", () => {
    let clickedAnchor;

    beforeEach(() => {
      clickedAnchor = null;
      URL.createObjectURL = jest.fn(() => "blob:fake-url");
      URL.revokeObjectURL = jest.fn();
      jest
        .spyOn(HTMLAnchorElement.prototype, "click")
        .mockImplementation(function () {
          clickedAnchor = this;
        });
    });

    afterEach(() => {
      jest.restoreAllMocks();
      delete URL.createObjectURL;
      delete URL.revokeObjectURL;
    });

    test("fetches the blob, triggers an <a> download, and revokes the URL", async () => {
      const fakeBlob = { size: 10 };
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        status: 200,
        blob: async () => fakeBlob,
      });

      await downloadResume("r1", "clara-resume-software-engineer.docx");

      expect(fetch.mock.calls[0][0]).toBe("/api/resumes/r1/download");
      expect(URL.createObjectURL).toHaveBeenCalledWith(fakeBlob);
      expect(clickedAnchor).not.toBeNull();
      expect(clickedAnchor.download).toBe(
        "clara-resume-software-engineer.docx",
      );
      expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:fake-url");
    });
  });
});
