import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useResumes } from "../hooks/useResumes";
import NavBar from "../components/NavBar";

const RANK_LABELS = { 1: "First Choice", 2: "Second Choice", 3: "Third Choice" };

function downloadText(text, filename) {
  const blob = new Blob([text], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function ResumeCard({ resume, onSave }) {
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState("");
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);

  const displayText = resume.edited_text ?? resume.raw_text;

  function startEdit() {
    setEditText(displayText);
    setEditing(true);
  }

  function cancelEdit() {
    setEditing(false);
    setEditText("");
  }

  async function handleSave() {
    setSaving(true);
    try {
      await onSave(resume.id, editText);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(displayText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleDownload() {
    const slug = (resume.target_title || `role-${resume.target_rank}`)
      .toLowerCase()
      .replace(/\s+/g, "-");
    downloadText(displayText, `clara-resume-${slug}.txt`);
  }

  const rankClass = resume.target_rank === 1 ? "" : resume.target_rank === 2 ? " rank-2" : " rank-3";

  return (
    <div className="resume-card">
      <div className="resume-card-header">
        <div style={{ display: "flex", alignItems: "center", gap: "var(--s3)", flex: 1 }}>
          <div className={`resume-rank-badge${rankClass}`}>{resume.target_rank}</div>
          <div>
            <div className="resume-card-title">{resume.target_title || `Role #${resume.target_rank}`}</div>
            <div className="t-small">{RANK_LABELS[resume.target_rank] || ""}</div>
          </div>
        </div>
        <div className="resume-card-meta">
          {resume.edited_text && (
            <span className="badge badge-pending" style={{ marginRight: "var(--s2)" }}>Edited</span>
          )}
          {new Date(resume.created_at).toLocaleDateString()}
        </div>
      </div>

      <div className="resume-card-actions">
        <button className="btn btn-ghost btn-sm" onClick={handleCopy}>
          {copied ? "✓ Copied!" : "Copy text"}
        </button>
        <button className="btn btn-ghost btn-sm" onClick={handleDownload}>
          Download .txt
        </button>
        {!editing && (
          <button className="btn btn-secondary btn-sm" onClick={startEdit}>
            Edit
          </button>
        )}
      </div>

      <div className="resume-card-body">
        {editing ? (
          <>
            <textarea
              className="resume-edit-area"
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
            />
            <div className="resume-edit-actions">
              <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={saving}>
                {saving ? "Saving…" : "Save edits"}
              </button>
              <button className="btn btn-ghost btn-sm" onClick={cancelEdit} disabled={saving}>
                Cancel
              </button>
            </div>
          </>
        ) : (
          <>
            {resume.sections.map((section, i) => (
              <div key={i} className="resume-section">
                <div className="resume-section-heading">{section.heading}</div>
                <div className="resume-section-content">{section.content}</div>
              </div>
            ))}

            {resume.notes_for_student && resume.notes_for_student.length > 0 && (
              <div className="resume-notes">
                <div className="resume-notes-label">Notes from Clara</div>
                {resume.notes_for_student.map((note, i) => (
                  <div key={i} className="resume-notes-item">{note}</div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function Resumes() {
  const { resumes, loading, error, load, generate, saveEdit } = useResumes();
  const navigate = useNavigate();

  useEffect(() => { load(); }, []);

  const hasResumes = resumes.length > 0;

  return (
    <>
      <NavBar />
      <div className="page-shell">
        <div className="page-content fade-up">

          <div className="page-header">
            <button className="page-back" onClick={() => navigate("/dashboard")}>← Dashboard</button>
          </div>
          <div className="page-title-block" style={{ marginBottom: "var(--s8)" }}>
            <p className="page-eyebrow">AI-Generated</p>
            <h1 className="page-title">Tailored Resumes</h1>
          </div>

          <div className="assessment-run-card">
            <div className="assessment-run-info">
              <div className="assessment-run-title">
                {hasResumes ? "Regenerate all three drafts" : "Generate your tailored resume drafts"}
              </div>
              <div className="assessment-run-desc">
                Clara drafts one resume per target role using only your real experience.
                {hasResumes && " Generating will replace your current drafts."}
              </div>
            </div>
            <button className="btn btn-primary btn-lg" onClick={generate} disabled={loading}>
              {loading ? (
                <><div className="spinner" style={{ borderTopColor: "white", borderColor: "rgba(255,255,255,0.3)" }} /> Generating…</>
              ) : hasResumes ? "Regenerate" : "Generate Resumes"}
            </button>
          </div>

          {error && (
            <div className="status-error" style={{ marginBottom: "var(--s6)" }}>
              ⚠ {error.message || "Something went wrong. Please try again."}
            </div>
          )}

          {loading && !hasResumes && (
            <div className="loading-state">
              <div className="spinner" />
              <span>Clara is drafting your resumes — this may take up to 30 seconds…</span>
            </div>
          )}

          {!loading && !hasResumes && !error && (
            <div className="empty-state">
              <div className="empty-state-icon">📄</div>
              <div className="empty-state-title">No resume drafts yet</div>
              <div className="empty-state-desc">
                Generate your first set to get three tailored starting points.
              </div>
            </div>
          )}

          {hasResumes && (
            <>
              <div className="assessment-meta">
                {resumes.length} draft{resumes.length !== 1 ? "s" : ""} · generated{" "}
                {new Date(resumes[0].created_at).toLocaleString()}
              </div>

              {resumes.map((resume) => (
                <ResumeCard key={resume.id} resume={resume} onSave={saveEdit} />
              ))}

              <div className="counselor-note">
                These drafts are starting points based on your uploaded resume. Review each one
                carefully and edit as needed. A Temple Career Center counselor can help you refine
                them — visit <strong>temple.edu/life-at-temple/careers</strong> to book an appointment.
              </div>
            </>
          )}

        </div>
      </div>
    </>
  );
}
