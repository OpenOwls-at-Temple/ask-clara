import { useState } from "react";
import { listLeads, markLeadsSeen, updateLeadStatus } from "../services/leads";

export function useLeads() {
  const [leads, setLeads] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function load() {
    setLoading(true);
    try {
      const data = await listLeads();
      // Remember which leads were new at load time so "New" chips stay visible
      // for this visit even after the badge-clearing mark-seen call below.
      const withNewFlag = data.map((lead) => ({
        ...lead,
        wasNew: lead.status === "new",
      }));
      setLeads(withNewFlag);
      if (withNewFlag.some((lead) => lead.wasNew)) {
        markLeadsSeen().catch(() => {}); // badge cleanup — never block the page
      }
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }

  async function setStatus(leadId, status) {
    setError(null);
    try {
      const updated = await updateLeadStatus(leadId, status);
      setLeads((prev) =>
        prev?.map((lead) =>
          lead.id === leadId ? { ...lead, ...updated } : lead,
        ),
      );
    } catch (err) {
      setError(err);
    }
  }

  return { leads, loading, error, load, setStatus };
}
