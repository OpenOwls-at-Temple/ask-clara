function jsonResponse(body, { ok = true, status = 200 } = {}) {
  return { ok, status, json: async () => body, blob: async () => body };
}

describe("auth service", () => {
  let auth;

  beforeEach(() => {
    // auth.js keeps the access token in module-level state — reset it per test.
    jest.resetModules();
    global.fetch = jest.fn();
    auth = require("../../src/services/auth");
  });

  test("request prefixes the API base and sends credentials", async () => {
    fetch.mockResolvedValue(jsonResponse({ ok: true }));
    const result = await auth.request("/profile");
    expect(fetch).toHaveBeenCalledWith(
      "/api/profile",
      expect.objectContaining({ credentials: "include" }),
    );
    expect(result).toEqual({ ok: true });
  });

  test("request sends no Authorization header before a token is set", async () => {
    fetch.mockResolvedValue(jsonResponse({}));
    await auth.request("/profile");
    const { headers } = fetch.mock.calls[0][1];
    expect(headers).not.toHaveProperty("Authorization");
  });

  test("request sends Bearer token after setAccessToken", async () => {
    fetch.mockResolvedValue(jsonResponse({}));
    auth.setAccessToken("tok-123");
    await auth.request("/profile");
    const { headers } = fetch.mock.calls[0][1];
    expect(headers.Authorization).toBe("Bearer tok-123");
  });

  test("request preserves caller headers alongside Authorization", async () => {
    fetch.mockResolvedValue(jsonResponse({}));
    auth.setAccessToken("tok-123");
    await auth.request("/profile", {
      headers: { "Content-Type": "application/json" },
    });
    const { headers } = fetch.mock.calls[0][1];
    expect(headers["Content-Type"]).toBe("application/json");
    expect(headers.Authorization).toBe("Bearer tok-123");
  });

  test("request throws the status code as the error message on non-ok", async () => {
    fetch.mockResolvedValue(jsonResponse({}, { ok: false, status: 404 }));
    // The stringified-status contract is load-bearing: useProfile branches
    // on err.message === "404" to treat a missing profile as "no profile yet".
    await expect(auth.request("/profile")).rejects.toThrow("404");
  });

  test("requestBlob returns the blob and shares the auth/error contract", async () => {
    const fakeBlob = { size: 3 };
    fetch.mockResolvedValue({
      ok: true,
      status: 200,
      blob: async () => fakeBlob,
    });
    auth.setAccessToken("tok-123");
    const blob = await auth.requestBlob("/resumes/r1/download");
    expect(blob).toBe(fakeBlob);
    expect(fetch.mock.calls[0][1].headers.Authorization).toBe("Bearer tok-123");

    fetch.mockResolvedValue({ ok: false, status: 403, blob: async () => null });
    await expect(auth.requestBlob("/resumes/r1/download")).rejects.toThrow(
      "403",
    );
  });

  test("login POSTs the Google credential as JSON", async () => {
    fetch.mockResolvedValue(jsonResponse({ access_token: "t" }));
    await auth.login("google-cred");
    expect(fetch).toHaveBeenCalledWith(
      "/api/auth/login",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ credential: "google-cred" }),
      }),
    );
  });

  test("refreshToken POSTs to /auth/refresh", async () => {
    fetch.mockResolvedValue(jsonResponse({ access_token: "t" }));
    await auth.refreshToken();
    expect(fetch).toHaveBeenCalledWith(
      "/api/auth/refresh",
      expect.objectContaining({ method: "POST" }),
    );
  });

  test("getMe GETs /auth/me", async () => {
    fetch.mockResolvedValue(jsonResponse({ user: {} }));
    await auth.getMe();
    expect(fetch.mock.calls[0][0]).toBe("/api/auth/me");
  });

  test("logout POSTs with credentials and does not throw on non-ok", async () => {
    fetch.mockResolvedValue({ ok: false, status: 500 });
    await expect(auth.logout()).resolves.toBeDefined();
    expect(fetch).toHaveBeenCalledWith(
      "/api/auth/logout",
      expect.objectContaining({ method: "POST", credentials: "include" }),
    );
  });
});
