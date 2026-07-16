import { request } from "./auth";

export const listLeads = () => request("/leads");

export const updateLeadStatus = (leadId, status) =>
  request(`/leads/${leadId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });

// Clears the in-app new-leads notification badge.
export const markLeadsSeen = () =>
  request("/leads/mark-seen", { method: "POST" });

// Student-triggered scan — the backend allows it once per 24 hours (429 after).
export const runScan = () => request("/leads/scan", { method: "POST" });

// Feature 8 lives in services/materials.js (generateLeadMaterials et al.).
