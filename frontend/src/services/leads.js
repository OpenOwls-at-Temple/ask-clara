import { request } from "./auth";

// Phase 2 — not active in Phase 1
export const listLeads = () => request("/leads");

export const generateLeadMaterials = (leadId) =>
  request(`/leads/${leadId}/materials`, { method: "POST" });
