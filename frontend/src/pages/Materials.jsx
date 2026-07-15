import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useMaterials } from "../hooks/useMaterials";
import { fetchPosting } from "../services/materials";
import { fetchMaterialsResumePdf } from "../services/documents";
import {
  ResumePdfViewer,
  TextPreviewModal,
} from "../components/DocumentModals";
import NavBar from "../components/NavBar";

function errorText(err, fallback) {
  if (err?.message === "429")
    return "You have reached the generation limit for this pilot. Please contact the team if you need more.";
  if (err?.message === "422")
    return "Clara couldn't read a job posting at that link. Please paste the job details manually below.";
  return fallback;
}

function renderResumeText(sections) {
  return sections
    .map(
      (s) =>
        `${s.heading.toUpperCase()}\n${"-".repeat(s.heading.length)}\n${s.content}`,
    )
    .join("\n\n");
}

function CopyButton({ text, label }) {
  const [copied, setCopied] = useState(false);
  async function handleCopy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }
  return (
    <button className="btn btn-ghost btn-sm" onClick={handleCopy}>
      {copied ? "✓ Copied!" : label}
    </button>
  );
}

function MaterialsCard({ doc, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  const [showText, setShowText] = useState(false);

  const slug = (doc.posting.title || "resume")
    .toLowerCase()
    .replace(/\s+/g, "-");

  return (
    <div className="resume-card">
      <div className="resume-card-header">
        <div>
          <div className="resume-card-title">
            {doc.posting.title}
            {doc.lead_id && (
              <span className="badge badge-pending lead-new-chip">
                From a lead
              </span>
            )}
          </div>
          <div className="resume-card-meta">
            {doc.posting.employer}
            {doc.posting.location ? ` · ${doc.posting.location}` : ""} ·
            generated {new Date(doc.created_at).toLocaleDateString()}
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
          {doc.fit_summary && (
            <div className="lead-reason">
              <span className="lead-reason-label">
                How this posting fits you
              </span>
              {doc.fit_summary}
            </div>
          )}

          <div className="resume-section">
            <div className="resume-section-heading">Employer brief</div>
            <div className="resume-section-content">{doc.employer_brief}</div>
          </div>

          <div className="resume-section">
            <div
              className="resume-section-heading"
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              Cover letter
              <CopyButton text={doc.cover_letter} label="Copy letter" />
            </div>
            <div
              className="resume-section-content"
              style={{ whiteSpace: "pre-wrap" }}
            >
              {doc.cover_letter}
            </div>
          </div>

          <div className="resume-section">
            <div
              className="resume-section-heading"
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              Tailored resume
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => setShowText(true)}
              >
                Copy resume
              </button>
            </div>
            <ResumePdfViewer
              fetchBlob={(format) => fetchMaterialsResumePdf(doc.id, format)}
              filename={`clara-resume-${slug}.pdf`}
              fallbackHint='use "Copy resume" instead.'
            />
          </div>

          {showText && (
            <TextPreviewModal
              title={`Tailored resume — ${doc.posting.title}`}
              text={renderResumeText(doc.resume_sections)}
              onClose={() => setShowText(false)}
            />
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

          {doc.posting.url && (
            <div className="resume-card-actions">
              <a
                className="btn btn-ghost btn-sm"
                href={doc.posting.url}
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

export default function Materials() {
  const { materials, loading, generating, error, load, generate } =
    useMaterials();
  const navigate = useNavigate();
  const location = useLocation();
  const lead = location.state?.lead ?? null;

  const [url, setUrl] = useState(lead?.url ?? "");
  const [title, setTitle] = useState(lead?.title ?? "");
  const [employer, setEmployer] = useState(lead?.employer ?? "");
  const [postingLocation, setPostingLocation] = useState("");
  const [description, setDescription] = useState("");
  const [fetching, setFetching] = useState(false);
  const [fetchError, setFetchError] = useState(null);
  const [fetched, setFetched] = useState(false);
  const [justGeneratedId, setJustGeneratedId] = useState(null);

  useEffect(() => {
    load();
  }, []);

  async function handleFetch() {
    setFetching(true);
    setFetchError(null);
    try {
      const posting = await fetchPosting(url);
      setTitle(posting.title);
      if (posting.employer) setEmployer(posting.employer);
      if (posting.location) setPostingLocation(posting.location);
      setDescription(posting.description);
      setFetched(true);
    } catch (err) {
      setFetchError(err);
    } finally {
      setFetching(false);
    }
  }

  async function handleGenerate() {
    const doc = await generate(
      {
        title: title.trim(),
        employer: employer.trim(),
        description: description.trim(),
        location: postingLocation.trim() || null,
        url: url.trim() || null,
      },
      lead?.id,
    );
    if (doc) {
      setJustGeneratedId(doc.id);
    }
  }

  // A lead's description can stay blank — the backend reads the posting page.
  const canGenerate = lead
    ? true
    : title.trim() && employer.trim() && description.trim();

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
            <p className="page-eyebrow">Per-Posting</p>
            <h1 className="page-title">Application Materials</h1>
          </div>

          <div className="assessment-run-card">
            <div className="assessment-run-info">
              <div className="assessment-run-title">
                {lead
                  ? `Tailor materials for “${lead.title}” at ${lead.employer}`
                  : "Tailor your application to one specific posting"}
              </div>
              <div className="assessment-run-desc">
                Paste a link to a job posting and Clara will read it, then draft
                a resume variant and cover letter tuned to that posting — plus a
                short brief on the employer. If the link can't be read, you can
                paste the job details yourself. Everything is grounded in your
                real experience.
              </div>
            </div>
          </div>

          <div className="form-card" style={{ marginBottom: "var(--s6)" }}>
            <div className="form-stack">
              <div className="form-group">
                <label className="form-label" htmlFor="posting-url">
                  Job posting link
                </label>
                <div style={{ display: "flex", gap: "var(--s3)" }}>
                  <input
                    id="posting-url"
                    className="form-input"
                    type="url"
                    placeholder="https://…"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    style={{ flex: 1 }}
                  />
                  <button
                    className="btn btn-secondary"
                    onClick={handleFetch}
                    disabled={fetching || !url.trim()}
                  >
                    {fetching ? "Fetching…" : "Fetch details"}
                  </button>
                </div>
                {fetched && !fetchError && (
                  <div
                    className="status-success"
                    style={{ marginTop: "var(--s3)" }}
                  >
                    ✓ Posting details loaded — review them below, then generate.
                  </div>
                )}
                {fetchError && (
                  <div
                    className="status-error"
                    style={{ marginTop: "var(--s3)" }}
                  >
                    ⚠{" "}
                    {errorText(
                      fetchError,
                      "Clara couldn't fetch that link. Please fill in the job details manually below.",
                    )}
                  </div>
                )}
              </div>

              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label" htmlFor="posting-title">
                    Job title
                  </label>
                  <input
                    id="posting-title"
                    className="form-input"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Software Engineer Intern"
                    disabled={Boolean(lead)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="posting-employer">
                    Company
                  </label>
                  <input
                    id="posting-employer"
                    className="form-input"
                    value={employer}
                    onChange={(e) => setEmployer(e.target.value)}
                    placeholder="e.g. Acme Corp"
                    disabled={Boolean(lead)}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="posting-description">
                  Job description{" "}
                  {lead && "(optional — Clara can read the posting page)"}
                </label>
                <textarea
                  id="posting-description"
                  className="form-textarea"
                  rows={8}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Paste the responsibilities and requirements from the posting…"
                />
              </div>

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
                      Generating…
                    </>
                  ) : (
                    "Generate materials"
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
                Clara is tailoring your resume, cover letter, and employer brief
                — this may take up to a minute…
              </span>
            </div>
          )}

          {loading && (
            <div className="loading-state">
              <div className="spinner" />
              <span>Loading your materials…</span>
            </div>
          )}

          {!loading && materials && materials.length === 0 && !generating && (
            <div className="empty-state">
              <div className="empty-state-icon">✉️</div>
              <div className="empty-state-title">No tailored materials yet</div>
              <div className="empty-state-desc">
                Add a posting above — or pick one of your job leads — to get a
                resume and cover letter aimed at that exact role.
              </div>
              <button
                className="btn btn-secondary"
                onClick={() => navigate("/leads")}
              >
                Browse my job leads
              </button>
            </div>
          )}

          {!loading && materials && materials.length > 0 && (
            <div className="result-section">
              <div className="result-section-header">
                <span className="result-section-label">
                  Your tailored materials — newest first
                </span>
                <div className="result-section-line" />
              </div>
              {materials.map((doc) => (
                <MaterialsCard
                  key={doc.id}
                  doc={doc}
                  defaultOpen={doc.id === justGeneratedId}
                />
              ))}
            </div>
          )}

          {!loading && materials && materials.length > 0 && (
            <div className="counselor-note">
              Review every document before you send it — these drafts are
              grounded in your uploaded resume, but you know your story best. A
              Temple Career Center counselor can help you polish them further.
            </div>
          )}
        </div>
      </div>
    </>
  );
}
