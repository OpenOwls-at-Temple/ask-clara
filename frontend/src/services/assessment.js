import { request } from "./auth";

export const runAssessment = () => request("/assessment", { method: "POST" });

export const listAssessments = () => request("/assessment");
