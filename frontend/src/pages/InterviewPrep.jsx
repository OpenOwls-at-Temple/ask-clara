import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useInterviewPrep } from "../hooks/useInterviewPrep";
import { useProfile } from "../hooks/useProfile";
import NavBar from "../components/NavBar";

function errorText(err, fallback) {
  if (err?.message === "429")
    return "You have reached the generation limit for this pilot. Please contact the team if you need more.";
  return fallback;
}

function targetLabel(target) {
  if (target.mode === "role") {
    return target.rank
      ? `${target.title} (role #${target.rank})`
      : target.title;
  }
  return target.employer
    ? `${target.title} · ${target.employer}`
    : target.title;
}

function PrepCard({ doc, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="resume-card">
      <div className="resume-card-header">
        <div>
          <div className="resume-card-title">
            {doc.target.title}
            {doc.lead_id && (
              <span className="badge badge-pending lead-new-chip">
                From a lead
              </span>
            )}
          </div>
          <div className="resume-card-meta">
            {targetLabel(doc.target)} · generated{" "}
            {new Date(doc.created_at).toLocaleDateString()}
          </div>
        </div>
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => setOpen((v) => !v)}
        >
          {open ? "Hide" : "View"}
        </button>
      </div>

      {open && (
        <div className="resume-card-body">
          <div className="result-section">
            <div className="result-section-header">
              <span className="result-section-label">
                Interview formats to expect
              </span>
              <div className="result-section-line" />
            </div>
            <div className="result-list">
              {doc.formats.map((f, i) => (
                <div key={i} className="result-item">
                  <div
                    className="result-item-icon"
                    style={{ fontWeight: 700, color: "var(--cherry)" }}
                  >
                    {i + 1}
                  </div>
                  <div className="result-item-body">
                    <div className="result-item-label">{f.name}</div>
                    <div>{f.what_to_expect}</div>
                    <div className="t-small">
                      <strong>How to prepare:</strong> {f.how_to_prepare}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="result-section">
            <div className="result-section-header">
              <span className="result-section-label">What to focus on</span>
              <div className="result-section-line" />
            </div>
            <div className="result-list">
              {doc.focus_areas.map((a, i) => (
                <div key={i} className="result-item">
                  <div className="result-item-icon">◆</div>
                  <div className="result-item-body">
                    <div className="result-item-label">{a.area}</div>
                    <div>{a.why}</div>
                    <div className="t-small">
                      <strong>How to prepare:</strong> {a.how_to_prepare}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="result-section">
            <div className="result-section-header">
              <span className="result-section-label">Practice questions</span>
              <div className="result-section-line" />
            </div>
            <div className="result-list">
              {doc.practice_questions.map((q, i) => (
                <div key={i} className="result-item">
                  <div className="result-item-icon">?</div>
                  <div className="result-item-body">
                    <div className="result-item-label">
                      {q.question}
                      <span className="result-item-tag">{q.type}</span>
                    </div>
                    <div className="t-small">
                      <strong>What they're looking for:</strong>{" "}
                      {q.what_they_look_for}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {doc.questions_to_ask.length > 0 && (
            <div className="result-section">
              <div className="result-section-header">
                <span className="result-section-label">
                  Questions to ask them
                </span>
                <div className="result-section-line" />
              </div>
              <div className="result-list">
                {doc.questions_to_ask.map((q, i) => (
                  <div key={i} className="result-item">
                    <div className="result-item-icon">💬</div>
                    <div className="result-item-body">{q}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {doc.notes_for_student && doc.notes_for_student.length > 0 && (
            <div className="resume-notes">
              <div className="resume-notes-label">Notes from Clara</div>
              {doc.notes_for_student.map((note, i) => (
                <div key={i} className="resume-notes-item">
                  {note}
                </div>
              ))}
            </div>
          )}

          {doc.target.url && (
            <div className="resume-card-actions">
              <a
                className="btn btn-ghost btn-sm"
                href={doc.target.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                View original posting ↗
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function InterviewPrep() {
  const {
    preps,
    loading,
    generating,
    error,
    load,
    generateForRole,
    generateForPosting,
    generateForLead,
  } = useInterviewPrep();
  const { profile } = useProfile();
  const navigate = useNavigate();
  const location = useLocation();
  const lead = location.state?.lead ?? null;

  const [mode, setMode] = useState(lead ? "posting" : "role");
  const [rank, setRank] = useState(1);
  const [title, setTitle] = useState(lead?.title ?? "");
  const [employer, setEmployer] = useState(lead?.employer ?? "");
  const [url, setUrl] = useState(lead?.url ?? "");
  const [description, setDescription] = useState("");
  const [justGeneratedId, setJustGeneratedId] = useState(null);

  useEffect(() => {
    load();
  }, []);

  const roles = [...(profile?.target_roles ?? [])].sort(
    (a, b) => a.rank - b.rank,
  );

  async function handleGenerate() {
    let doc;
    if (mode === "role") {
      doc = await generateForRole(Number(rank));
    } else if (lead) {
      doc = await generateForLead(lead.id);
    } else {
      doc = await generateForPosting({
        title: title.trim(),
        employer: employer.trim() || null,
        description: description.trim() || null,
        url: url.trim() || null,
      });
    }
    if (doc) setJustGeneratedId(doc.id);
  }

  const canGenerate =
    mode === "role" ? roles.length > 0 : Boolean(lead) || title.trim();

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
            <p className="page-eyebrow">Get Ready</p>
            <h1 className="page-title">Interview Prep</h1>
          </div>

          <div className="assessment-run-card">
            <div className="assessment-run-info">
              <div className="assessment-run-title">
                {lead
                  ? `Prep for “${lead.title}” at ${lead.employer}`
                  : "Prepare for one target role or one posting"}
              </div>
              <div className="assessment-run-desc">
                Clara outlines the interview rounds you're likely to face, what
                to study, and practice questions drawn from your own background
                — plus good questions to ask your interviewer.
              </div>
            </div>
          </div>

          <div className="form-card" style={{ marginBottom: "var(--s6)" }}>
            <div className="form-stack">
              {!lead && (
                <div className="form-group">
                  <label className="form-label" htmlFor="prep-mode">
                    What are you preparing for?
                  </label>
                  <select
                    id="prep-mode"
                    className="form-select"
                    value={mode}
                    onChange={(e) => setMode(e.target.value)}
                  >
                    <option value="role">One of my target roles</option>
                    <option value="posting">A specific job posting</option>
                  </select>
                </div>
              )}

              {mode === "role" && (
                <div className="form-group">
                  <label className="form-label" htmlFor="prep-role">
                    Target role
                  </label>
                  {roles.length === 0 ? (
                    <div className="form-hint">
                      Add your ranked target roles in your profile first.
                    </div>
                  ) : (
                    <select
                      id="prep-role"
                      className="form-select"
                      value={rank}
                      onChange={(e) => setRank(e.target.value)}
                    >
                      {roles.map((r) => (
                        <option key={r.rank} value={r.rank}>
                          #{r.rank} — {r.title}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              )}

              {mode === "posting" && (
                <>
                  <div className="form-grid">
                    <div className="form-group">
                      <label className="form-label" htmlFor="prep-title">
                        Job title
                      </label>
                      <input
                        id="prep-title"
                        className="form-input"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="e.g. Software Engineer Intern"
                        disabled={Boolean(lead)}
                      />
                    </div>
                    <div className="form-group">
                      <label className="form-label" htmlFor="prep-employer">
                        Company
                      </label>
                      <input
                        id="prep-employer"
                        className="form-input"
                        value={employer}
                        onChange={(e) => setEmployer(e.target.value)}
                        placeholder="e.g. Acme Corp"
                        disabled={Boolean(lead)}
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label" htmlFor="prep-url">
                      Job posting link (optional)
                    </label>
                    <input
                      id="prep-url"
                      className="form-input"
                      type="url"
                      placeholder="https://…"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      disabled={Boolean(lead)}
                    />
                    <div className="form-hint">
                      Clara reads the posting when she can. If the link can't be
                      read, she still preps you from the title and company.
                    </div>
                  </div>

                  {!lead && (
                    <div className="form-group">
                      <label className="form-label" htmlFor="prep-description">
                        Job description (optional)
                      </label>
                      <textarea
                        id="prep-description"
                        className="form-textarea"
                        rows={6}
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Paste the responsibilities and requirements for sharper prep…"
                      />
                    </div>
                  )}
                </>
              )}

              <div>
                <button
                  className="btn btn-primary btn-lg"
                  onClick={handleGenerate}
                  disabled={generating || !canGenerate}
                >
                  {generating ? (
                    <>
                      <div
                        className="spinner"
                        style={{
                          borderTopColor: "white",
                          borderColor: "rgba(255,255,255,0.3)",
                        }}
                      />{" "}
                      Preparing…
                    </>
                  ) : (
                    "Get interview prep"
                  )}
                </button>
              </div>
            </div>
          </div>

          {error && (
            <div className="status-error" style={{ marginBottom: "var(--s6)" }}>
              ⚠ {errorText(error, "Something went wrong. Please try again.")}
            </div>
          )}

          {generating && (
            <div className="loading-state">
              <div className="spinner" />
              <span>
                Clara is building your interview prep — this may take up to a
                minute…
              </span>
            </div>
          )}

          {loading && (
            <div className="loading-state">
              <div className="spinner" />
              <span>Loading your interview prep…</span>
            </div>
          )}

          {!loading && preps && preps.length === 0 && !generating && (
            <div className="empty-state">
              <div className="empty-state-icon">🎤</div>
              <div className="empty-state-title">No interview prep yet</div>
              <div className="empty-state-desc">
                Pick a target role above — or start from one of your job leads —
                to see the formats, focus areas, and practice questions to
                expect.
              </div>
              <button
                className="btn btn-secondary"
                onClick={() => navigate("/leads")}
              >
                Browse my job leads
              </button>
            </div>
          )}

          {!loading && preps && preps.length > 0 && (
            <div className="result-section">
              <div className="result-section-header">
                <span className="result-section-label">
                  Your interview prep — newest first
                </span>
                <div className="result-section-line" />
              </div>
              {preps.map((doc) => (
                <PrepCard
                  key={doc.id}
                  doc={doc}
                  defaultOpen={doc.id === justGeneratedId}
                />
              ))}
            </div>
          )}

          {!loading && preps && preps.length > 0 && (
            <div className="counselor-note">
              Practice out loud, not just on the page. The Temple Career Center
              runs mock interviews with a real counselor — the natural next step
              once you've worked through these questions.
            </div>
          )}
        </div>
      </div>
    </>
  );
}
