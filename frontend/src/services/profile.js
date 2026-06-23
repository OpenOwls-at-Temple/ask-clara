const BASE = import.meta.env.VITE_API_BASE_URL;

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, { credentials: "include", ...options });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const getProfile = () => request("/profile");

export const updateProfile = (body) =>
  request("/profile", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const uploadResume = (file) => {
  const form = new FormData();
  form.append("file", file);
  return request("/profile/resume", { method: "POST", body: form });
};

export const submitLinkedIn = (body) =>
  request("/profile/linkedin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
