const BASE = import.meta.env.VITE_API_BASE_URL;

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, { credentials: "include", ...options });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

// Phase 2 — not active in Phase 1
export const listLeads = () => request("/leads");

export const generateLeadMaterials = (leadId) =>
  request(`/leads/${leadId}/materials`, { method: "POST" });
