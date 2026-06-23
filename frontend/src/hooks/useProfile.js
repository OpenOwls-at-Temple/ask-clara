import { useCallback, useEffect, useState } from "react";

import { getProfile, updateProfile, uploadResume, submitLinkedIn } from "../services/profile";

export function useProfile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getProfile();
      setProfile(data);
    } catch (err) {
      // 404 means no profile yet — that's expected for new users
      if (err.message !== "404") setError(err);
      setProfile(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function save(body) {
    const data = await updateProfile(body);
    setProfile(data);
    return data;
  }

  async function saveResume(file) {
    const data = await uploadResume(file);
    setProfile((prev) => ({ ...prev, resume_doc_id: data.resume_doc_id }));
    return data;
  }

  async function saveLinkedIn(url) {
    const data = await submitLinkedIn(url);
    setProfile((prev) => ({ ...prev, linkedin_doc_id: data.linkedin_doc_id }));
    return data;
  }

  return { profile, loading, error, save, saveResume, saveLinkedIn, reload: load };
}
