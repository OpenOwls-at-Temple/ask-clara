import { useState } from "react";
import { generateResumes, listResumes, updateResume } from "../services/documents";

export function useResumes() {
  const [resumes, setResumes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function load() {
    setLoading(true);
    try {
      const data = await listResumes();
      setResumes(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  async function generate() {
    setLoading(true);
    setError(null);
    try {
      const results = await generateResumes();
      setResumes(results);
      return results;
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  async function saveEdit(id, editedText) {
    await updateResume(id, editedText);
    setResumes((prev) =>
      prev.map((r) => (r.id === id ? { ...r, edited_text: editedText } : r))
    );
  }

  return { resumes, loading, error, load, generate, saveEdit };
}
