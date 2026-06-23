import { useState } from "react";
import { listAssessments, runAssessment } from "../services/assessment";

export function useAssessment() {
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function load() {
    setLoading(true);
    try {
      const data = await listAssessments();
      setAssessments(data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const result = await runAssessment();
      setAssessments((prev) => [result, ...prev]);
      return result;
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  return { assessments, loading, error, load, run };
}
