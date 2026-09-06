import { request } from "./auth";

// Generate interview prep for one of the student's ranked target roles.
export const generateRolePrep = (targetRank) =>
  request("/interview-prep", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ target_rank: targetRank }),
  });

// Generate interview prep for one specific posting. Only the title is
// required — Clara reads the posting page when a link is given.
export const generatePostingPrep = (posting) =>
  request("/interview-prep", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ posting }),
  });

// Same generation for one of the student's stored job leads.
export const generateLeadPrep = (leadId) =>
  request(`/leads/${leadId}/interview-prep`, { method: "POST" });

export const listInterviewPreps = () => request("/interview-prep");
