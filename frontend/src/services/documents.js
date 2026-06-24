import { request, requestBlob } from "./auth";

export const generateResumes = () => request("/resumes/generate", { method: "POST" });

export const listResumes = () => request("/resumes");

export const updateResume = (id, editedText) =>
  request(`/resumes/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ edited_text: editedText }),
  });

export const downloadResume = async (id, filename) => {
  const blob = await requestBlob(`/resumes/${id}/download`);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};
