const BASE = import.meta.env.VITE_API_BASE_URL;

// Access token lives only in memory — never written to localStorage or sessionStorage.
let _token = null;

export function setAccessToken(token) {
  _token = token;
}

export async function request(path, options = {}) {
  const headers = { ...options.headers };
  if (_token) headers["Authorization"] = `Bearer ${_token}`;
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include",
    ...options,
    headers,
  });
  if (!res.ok) throw new Error(String(res.status));
  return res.json();
}

export const getMe = () => request("/auth/me");

export const login = (credential) =>
  request("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ credential }),
  });

// Called on page load to restore the session from the httpOnly refresh cookie.
export const refreshToken = () => request("/auth/refresh", { method: "POST" });

export const logout = () =>
  fetch(`${BASE}/auth/logout`, { method: "POST", credentials: "include" });
