import { request, requestBlob } from "./auth";

export const generateResumes = () =>
  request("/resumes/generate", { method: "POST" });

export const listResumes = () => request("/resumes");

export const updateResume = (id, editedText) =>
  request(`/resumes/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ edited_text: editedText }),
  });

export const saveBlob = (blob, filename) => {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};

// Blob fetchers — the inline viewer shows a PNG render of the resume (no
// browser PDF chrome) and fetches the real PDF only on download.
export const fetchResumePdf = (id, format = "pdf") =>
  requestBlob(`/resumes/${id}/download?format=${format}`);

export const fetchMaterialsResumePdf = (id, format = "pdf") =>
  requestBlob(`/materials/${id}/resume/download?format=${format}`);

// format: "pdf" (Typst-rendered, one page) or "docx"
export const downloadResume = async (id, filename, format = "pdf") => {
  const blob = await requestBlob(`/resumes/${id}/download?format=${format}`);
  saveBlob(blob, filename);
};
