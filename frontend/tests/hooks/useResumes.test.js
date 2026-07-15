import { renderHook, act } from "@testing-library/react";

jest.mock("../../src/services/documents", () => ({
  generateResumes: jest.fn(),
  listResumes: jest.fn(),
  updateResume: jest.fn(),
}));

const svc = require("../../src/services/documents");
const { useResumes } = require("../../src/hooks/useResumes");

const drafts = [
  { id: "r1", target_rank: 1, raw_text: "one" },
  { id: "r2", target_rank: 2, raw_text: "two" },
];

describe("useResumes", () => {
  afterEach(() => jest.clearAllMocks());

  test("load fetches the resume list", async () => {
    svc.listResumes.mockResolvedValue(drafts);
    const { result } = renderHook(() => useResumes());

    await act(async () => {
      await result.current.load();
    });

    expect(result.current.resumes).toEqual(drafts);
    expect(result.current.loading).toBe(false);
  });

  test("load failure sets error", async () => {
    svc.listResumes.mockRejectedValue(new Error("500"));
    const { result } = renderHook(() => useResumes());

    await act(async () => {
      await result.current.load();
    });

    expect(result.current.error).toEqual(new Error("500"));
  });

  test("generate replaces the list and clears a previous error", async () => {
    svc.listResumes.mockRejectedValue(new Error("500"));
    svc.generateResumes.mockResolvedValue(drafts);
    const { result } = renderHook(() => useResumes());

    await act(async () => {
      await result.current.load();
    });
    expect(result.current.error).not.toBeNull();

    await act(async () => {
      await result.current.generate();
    });

    expect(result.current.error).toBeNull();
    expect(result.current.resumes).toEqual(drafts);
  });

  test("saveEdit patches only the matching resume's edited_text", async () => {
    svc.listResumes.mockResolvedValue(drafts);
    svc.updateResume.mockResolvedValue({});
    const { result } = renderHook(() => useResumes());

    await act(async () => {
      await result.current.load();
    });
    await act(async () => {
      await result.current.saveEdit("r2", "edited");
    });

    expect(svc.updateResume).toHaveBeenCalledWith("r2", "edited");
    expect(result.current.resumes[0]).not.toHaveProperty("edited_text");
    expect(result.current.resumes[1].edited_text).toBe("edited");
  });
});
