import { renderHook, act, waitFor } from "@testing-library/react";

jest.mock("../../src/services/profile", () => ({
  getProfile: jest.fn(),
  updateProfile: jest.fn(),
  uploadResume: jest.fn(),
  submitLinkedIn: jest.fn(),
  uploadLinkedInExport: jest.fn(),
}));

const svc = require("../../src/services/profile");
const { useProfile } = require("../../src/hooks/useProfile");

describe("useProfile", () => {
  afterEach(() => jest.clearAllMocks());

  test("auto-loads the profile on mount", async () => {
    svc.getProfile.mockResolvedValue({ id: "p1" });
    const { result } = renderHook(() => useProfile());

    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.profile).toEqual({ id: "p1" });
    expect(result.current.error).toBeNull();
  });

  test("swallows 404 as 'no profile yet'", async () => {
    svc.getProfile.mockRejectedValue(new Error("404"));
    const { result } = renderHook(() => useProfile());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.profile).toBeNull();
    expect(result.current.error).toBeNull();
  });

  test("surfaces non-404 load errors", async () => {
    svc.getProfile.mockRejectedValue(new Error("500"));
    const { result } = renderHook(() => useProfile());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toEqual(new Error("500"));
    expect(result.current.profile).toBeNull();
  });

  test("save replaces the profile with the server response", async () => {
    svc.getProfile.mockResolvedValue({ id: "p1", major_program: "CS" });
    svc.updateProfile.mockResolvedValue({ id: "p1", major_program: "Math" });
    const { result } = renderHook(() => useProfile());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.save({ major_program: "Math" });
    });

    expect(result.current.profile.major_program).toBe("Math");
  });

  test("saveResume merges resume_doc_id into the existing profile", async () => {
    svc.getProfile.mockResolvedValue({ id: "p1" });
    svc.uploadResume.mockResolvedValue({ resume_doc_id: "doc-1" });
    const { result } = renderHook(() => useProfile());
    await waitFor(() => expect(result.current.loading).toBe(false));

    const file = new File(["x"], "resume.pdf");
    await act(async () => {
      await result.current.saveResume(file);
    });

    expect(svc.uploadResume).toHaveBeenCalledWith(file);
    expect(result.current.profile).toEqual({
      id: "p1",
      resume_doc_id: "doc-1",
    });
  });

  test("saveLinkedIn and saveLinkedInExport merge linkedin_doc_id", async () => {
    svc.getProfile.mockResolvedValue({ id: "p1" });
    svc.submitLinkedIn.mockResolvedValue({ linkedin_doc_id: "li-1" });
    svc.uploadLinkedInExport.mockResolvedValue({ linkedin_doc_id: "li-2" });
    const { result } = renderHook(() => useProfile());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.saveLinkedIn("https://linkedin.com/in/x");
    });
    expect(result.current.profile.linkedin_doc_id).toBe("li-1");

    const file = new File(["x"], "linkedin.pdf");
    await act(async () => {
      await result.current.saveLinkedInExport(file);
    });
    expect(result.current.profile.linkedin_doc_id).toBe("li-2");
  });

  test("reload re-fetches the profile", async () => {
    svc.getProfile.mockResolvedValue({ id: "p1" });
    const { result } = renderHook(() => useProfile());
    await waitFor(() => expect(result.current.loading).toBe(false));

    svc.getProfile.mockResolvedValue({ id: "p1", track: "industry" });
    await act(async () => {
      await result.current.reload();
    });

    expect(svc.getProfile).toHaveBeenCalledTimes(2);
    expect(result.current.profile.track).toBe("industry");
  });
});
