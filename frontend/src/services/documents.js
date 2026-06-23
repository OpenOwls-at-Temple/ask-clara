const BASE = import.meta.env.VITE_API_BASE_URL;

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, { credentials: "include", ...options });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const generateResumes = () => request("/resumes/generate", { method: "POST" });

export const listResumes = () => request("/resumes");
