import { request } from "./auth";

export const getProfile = () => request("/profile");

export const updateProfile = (body) =>
  request("/profile", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

export const uploadResume = (file) => {
  const form = new FormData();
  form.append("file", file);
  return request("/profile/resume", { method: "POST", body: form });
};

export const submitLinkedIn = (url) =>
  request("/profile/linkedin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });

export const uploadLinkedInExport = (file) => {
  const form = new FormData();
  form.append("file", file);
  return request("/profile/linkedin/upload", { method: "POST", body: form });
};
