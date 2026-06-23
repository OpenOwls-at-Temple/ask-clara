const BASE = import.meta.env.VITE_API_BASE_URL;

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, { credentials: "include", ...options });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const getMe = () => request("/auth/me");

export const logout = () =>
  fetch(`${BASE}/auth/logout`, { method: "POST", credentials: "include" });
