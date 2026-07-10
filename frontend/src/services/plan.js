import { request } from "./auth";

export const generatePlan = () => request("/plan/generate", { method: "POST" });

export const getPlan = () => request("/plan");

export const updatePlanItem = (planId, itemIndex, status) =>
  request(`/plan/${planId}/items/${itemIndex}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
