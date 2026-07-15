import { request } from "./auth";

// Resolve a pasted job-posting link into title/employer/description (no LLM).
export const fetchPosting = (url) =>
  request("/materials/fetch-posting", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

// Generate tailored resume + cover letter + employer brief for a posting the
// student provided (fetched-and-confirmed or entered manually).
export const generateMaterials = (posting) =>
  request("/materials", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(posting),
  });

// Same generation for one of the student's stored job leads. Clara fetches
// the posting page unless the student pasted the description.
export const generateLeadMaterials = (leadId, description) =>
  request(`/leads/${leadId}/materials`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description: description || null }),
  });

export const listMaterials = () => request("/materials");
