import { useState } from "react";
import {
  listLeads,
  markLeadsSeen,
  runScan,
  updateLeadStatus,
} from "../services/leads";

export function useLeads() {
  const [leads, setLeads] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [scanNotice, setScanNotice] = useState(null);

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

  async function scan() {
    setScanning(true);
    setScanNotice(null);
    setError(null);
    try {
      const { created } = await runScan();
      await load();
      setScanNotice(
        created
          ? `Found ${created} new lead${created === 1 ? "" : "s"} for you.`
          : "No new matches this time — Clara will keep scanning nightly.",
      );
    } catch (err) {
      // request() surfaces only the HTTP status code as the error message.
      if (err.message === "429") {
        setScanNotice(
          "Clara already scanned for you in the last 24 hours. Try again tomorrow.",
        );
      } else if (err.message === "400") {
        setScanNotice(
          "Add your three ranked target roles in your profile first.",
        );
      } else {
        setError(err);
      }
    } finally {
      setScanning(false);
    }
  }

  return { leads, loading, error, load, setStatus, scan, scanning, scanNotice };
}
