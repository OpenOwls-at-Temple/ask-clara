import { useState, useEffect } from "react";
import { getProfile } from "../services/profile";

export function useProfile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    getProfile()
      .then(setProfile)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  return { profile, setProfile, loading, error };
}
