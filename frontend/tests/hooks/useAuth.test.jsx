import { renderHook, act, waitFor } from "@testing-library/react";

jest.mock("../../src/services/auth", () => ({
  login: jest.fn(),
  logout: jest.fn(),
  refreshToken: jest.fn(),
  setAccessToken: jest.fn(),
}));

const svc = require("../../src/services/auth");
const { AuthProvider, useAuth } = require("../../src/hooks/useAuth");

const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;

const sessionData = {
  access_token: "tok-1",
  user: { id: "u1", display_name: "Jane Doe" },
};

describe("useAuth", () => {
  afterEach(() => {
    jest.useRealTimers();
    jest.clearAllMocks();
  });

  test("restores the session from the refresh cookie on mount", async () => {
    svc.refreshToken.mockResolvedValue(sessionData);
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.loading).toBe(true);
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toEqual(sessionData.user);
    expect(svc.setAccessToken).toHaveBeenCalledWith("tok-1");
  });

  test("a failed restore leaves the user signed out without throwing", async () => {
    svc.refreshToken.mockRejectedValue(new Error("401"));
    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.user).toBeNull();
  });

  test("login stores the token and user", async () => {
    svc.refreshToken.mockRejectedValue(new Error("401"));
    svc.login.mockResolvedValue(sessionData);
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    let returned;
    await act(async () => {
      returned = await result.current.login("google-cred");
    });

    expect(svc.login).toHaveBeenCalledWith("google-cred");
    expect(svc.setAccessToken).toHaveBeenCalledWith("tok-1");
    expect(result.current.user).toEqual(sessionData.user);
    expect(returned).toEqual(sessionData.user);
  });

  test("logout clears the token and user", async () => {
    svc.refreshToken.mockResolvedValue(sessionData);
    svc.logout.mockResolvedValue({});
    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.user).toBeTruthy());

    await act(async () => {
      await result.current.logout();
    });

    expect(svc.setAccessToken).toHaveBeenLastCalledWith(null);
    expect(result.current.user).toBeNull();
  });

  test("refreshes the token every 10 minutes and signs out when refresh fails", async () => {
    jest.useFakeTimers();
    svc.refreshToken.mockResolvedValue(sessionData);
    const { result } = renderHook(() => useAuth(), { wrapper });

    // Flush the mount-time restore (no waitFor under fake timers).
    await act(async () => {});
    expect(result.current.user).toEqual(sessionData.user);
    expect(svc.refreshToken).toHaveBeenCalledTimes(1);

    await act(async () => {
      jest.advanceTimersByTime(10 * 60 * 1000);
    });
    expect(svc.refreshToken).toHaveBeenCalledTimes(2);
    expect(result.current.user).toEqual(sessionData.user);

    svc.refreshToken.mockRejectedValue(new Error("401"));
    await act(async () => {
      jest.advanceTimersByTime(10 * 60 * 1000);
    });
    expect(result.current.user).toBeNull();
    expect(svc.setAccessToken).toHaveBeenLastCalledWith(null);
  });
});
