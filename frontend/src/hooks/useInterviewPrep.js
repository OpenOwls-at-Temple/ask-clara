import { useState } from "react";
import {
  generateLeadPrep,
  generatePostingPrep,
  generateRolePrep,
  listInterviewPreps,
} from "../services/interviewPrep";

export function useInterviewPrep() {
  const [preps, setPreps] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  async function load() {
    setLoading(true);
    try {
      setPreps(await listInterviewPreps());
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  // Returns the new prep document, or null on failure (error is set).
  async function run(call) {
    setGenerating(true);
    setError(null);
    try {
      const doc = await call();
      setPreps((prev) => [doc, ...(prev ?? [])]);
      return doc;
    } catch (err) {
      setError(err);
      return null;
    } finally {
      setGenerating(false);
    }
  }

  const generateForRole = (targetRank) =>
    run(() => generateRolePrep(targetRank));
  // posting: {title, employer?, description?, url?}
  const generateForPosting = (posting) =>
    run(() => generatePostingPrep(posting));
  const generateForLead = (leadId) => run(() => generateLeadPrep(leadId));

  return {
    preps,
    loading,
    generating,
    error,
    load,
    generateForRole,
    generateForPosting,
    generateForLead,
  };
}
