import { request } from "./auth";

export const generateResumes = () => request("/resumes/generate", { method: "POST" });

export const listResumes = () => request("/resumes");
