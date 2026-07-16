import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLeads } from "../hooks/useLeads";
import NavBar from "../components/NavBar";

function fitLabel(score) {
  if (score == null) return null;
  return `${Math.round(score * 100)}% fit`;
}

function LeadCard({ lead, onStatus, onTailor }) {
  const applied = lead.status === "applied";
  const dismissed = lead.status === "dismissed";

  return (
    <div className="resume-card lead-card">
      <div className="resume-card-header">
        <div>
          <div className="resume-card-title">
            {lead.title}
            {lead.wasNew && !dismissed && (
              <span className="badge badge-pending lead-new-chip">New</span>
            )}
            {applied && (
              <span className="badge badge-complete lead-new-chip">
                Applied
              </span>
            )}
          </div>
          <div className="resume-card-meta">
            {lead.employer} · found{" "}
            {new Date(lead.found_at).toLocaleDateString()}
          </div>
        </div>
        {lead.fit_score != null && (
          <span className="lead-fit">{fitLabel(lead.fit_score)}</span>
        )}
      </div>

      <div className="resume-card-body">
        {lead.fit_reason && (
          <div className="lead-reason">
            <span className="lead-reason-label">Why Clara picked this</span>
            {lead.fit_reason}
          </div>
        )}
        <div className="resume-card-actions">
          <a
            className="btn btn-primary btn-sm"
            href={lead.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            View posting ↗
          </a>
          {dismissed ? (
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => onStatus(lead.id, "seen")}
            >
              Restore
            </button>
          ) : (
            <>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => onTailor(lead)}
              >
                Tailor materials
              </button>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => onStatus(lead.id, applied ? "seen" : "applied")}
              >
                {applied ? "Undo applied" : "I applied"}
              </button>
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => onStatus(lead.id, "dismissed")}
              >
                Dismiss
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function JobLeads() {
  const { leads, loading, error, load, setStatus, scan, scanning, scanNotice } =
    useLeads();
  const [showDismissed, setShowDismissed] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    load();
  }, []);

  const active = (leads ?? []).filter((l) => l.status !== "dismissed");
  const dismissed = (leads ?? []).filter((l) => l.status === "dismissed");

  // Feature 8: hand the lead to the Materials page for per-posting tailoring.
  const tailor = (lead) => navigate("/materials", { state: { lead } });

  return (
    <>
      <NavBar />
      <div className="page-shell">
        <div className="page-content fade-up">
          <div className="page-header">
            <button
              className="page-back"
              onClick={() => navigate("/dashboard")}
            >
              ← Dashboard
            </button>
          </div>
          <div
            className="page-title-block"
            style={{ marginBottom: "var(--s8)" }}
          >
            <p className="page-eyebrow">Curated</p>
            <h1 className="page-title">Job Leads</h1>
          </div>

          <div className="assessment-run-card">
            <div className="assessment-run-info">
              <div className="assessment-run-title">
                Postings matched to your goals
              </div>
              <div className="assessment-run-desc">
                Clara scans employer job boards every night and surfaces
                postings that fit your ranked target roles — with a note on why
                each one fits you. You can also run a scan yourself, once per
                day.
              </div>
            </div>
            <button
              className="btn btn-primary"
              onClick={scan}
              disabled={scanning || loading}
            >
              {scanning ? "Scanning…" : "Scan now"}
            </button>
          </div>

          {scanNotice && (
            <div
              className="status-success"
              style={{ marginBottom: "var(--s6)" }}
            >
              {scanNotice}
            </div>
          )}

          {error && (
            <div className="status-error" style={{ marginBottom: "var(--s6)" }}>
              ⚠ {error.message || "Something went wrong. Please try again."}
            </div>
          )}

          {loading && (
            <div className="loading-state">
              <div className="spinner" />
              <span>Loading your leads…</span>
            </div>
          )}

          {!loading &&
            leads &&
            active.length === 0 &&
            dismissed.length === 0 && (
              <div className="empty-state">
                <div className="empty-state-icon">🔍</div>
                <div className="empty-state-title">No leads yet</div>
                <div className="empty-state-desc">
                  Clara scans for new postings on weekday mornings, or scan now
                  yourself (once per day). Make sure your three target roles are
                  up to date.
                </div>
                <div
                  style={{
                    display: "flex",
                    gap: "var(--s3)",
                    justifyContent: "center",
                  }}
                >
                  <button
                    className="btn btn-primary"
                    onClick={scan}
                    disabled={scanning}
                  >
                    {scanning ? "Scanning…" : "Scan now"}
                  </button>
                  <button
                    className="btn btn-secondary"
                    onClick={() => navigate("/intake")}
                  >
                    Review my target roles
                  </button>
                </div>
              </div>
            )}

          {!loading && active.length > 0 && (
            <div className="result-section">
              <div className="result-section-header">
                <span className="result-section-label">
                  Matched for you — best fit first
                </span>
                <div className="result-section-line" />
              </div>
              {active.map((lead) => (
                <LeadCard
                  key={lead.id}
                  lead={lead}
                  onStatus={setStatus}
                  onTailor={tailor}
                />
              ))}
            </div>
          )}

          {!loading && dismissed.length > 0 && (
            <div className="result-section">
              <div className="result-section-header">
                <span className="result-section-label">
                  Dismissed ({dismissed.length})
                </span>
                <div className="result-section-line" />
                <button
                  className="btn btn-text btn-sm"
                  onClick={() => setShowDismissed((v) => !v)}
                >
                  {showDismissed ? "Hide" : "Show"}
                </button>
              </div>
              {showDismissed &&
                dismissed.map((lead) => (
                  <LeadCard
                    key={lead.id}
                    lead={lead}
                    onStatus={setStatus}
                    onTailor={tailor}
                  />
                ))}
            </div>
          )}

          {!loading && leads && leads.length > 0 && (
            <div className="counselor-note">
              Leads are a starting point — a Temple Career Center counselor can
              help you evaluate offers and applications. Clara never applies on
              your behalf.
            </div>
          )}
        </div>
      </div>
    </>
  );
}
