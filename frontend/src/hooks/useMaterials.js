import { useState } from "react";
import {
  generateLeadMaterials,
  generateMaterials,
  listMaterials,
} from "../services/materials";

export function useMaterials() {
  const [materials, setMaterials] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  async function load() {
    setLoading(true);
    try {
      setMaterials(await listMaterials());
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  // posting: {title, employer, description, location?, url?}; leadId optional.
  // Returns the new materials document, or null on failure (error is set).
  async function generate(posting, leadId) {
    setGenerating(true);
    setError(null);
    try {
      const doc = leadId
        ? await generateLeadMaterials(leadId, posting.description)
        : await generateMaterials(posting);
      setMaterials((prev) => [doc, ...(prev ?? [])]);
      return doc;
    } catch (err) {
      setError(err);
      return null;
    } finally {
      setGenerating(false);
    }
  }

  return { materials, loading, generating, error, load, generate };
}
