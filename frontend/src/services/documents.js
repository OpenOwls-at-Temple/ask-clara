import { request } from "./auth";

export const generateResumes = () => request("/resumes/generate", { method: "POST" });

export const listResumes = () => request("/resumes");

export const updateResume = (id, editedText) =>
  request(`/resumes/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ edited_text: editedText }),
  });
