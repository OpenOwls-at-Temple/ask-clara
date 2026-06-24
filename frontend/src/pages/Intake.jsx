import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useProfile } from "../hooks/useProfile";
import NavBar from "../components/NavBar";

const DEGREE_LEVELS = [
  { value: "undergrad", label: "Undergraduate" },
  { value: "grad",      label: "Graduate" },
  { value: "phd",       label: "PhD" },
];
const TRACKS = [
  { value: "industry",   label: "Industry" },
  { value: "academia",   label: "Academia" },
  { value: "government", label: "Government" },
  { value: "undecided",  label: "Undecided" },
];

function RankedRoleInput({ rank, value, onChange }) {
  const numClass = rank === 1 ? "" : rank === 2 ? " rank-2" : " rank-3";
  return (
    <div className="ranked-role-row">
      <div className={`ranked-role-num${numClass}`}>{rank}</div>
      <input
        className="form-input"
        type="text"
        value={value}
        onChange={(e) => onChange(rank, e.target.value)}
        placeholder={
          rank === 1 ? "e.g. Software Engineer"
          : rank === 2 ? "e.g. Data Scientist"
          : "e.g. Product Manager"
        }
        maxLength={200}
      />
    </div>
  );
}

export default function Intake() {
  const { profile, loading, save, saveResume, saveLinkedIn } = useProfile();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    degree_level: "",
    major_program: "",
    expected_graduation: "",
    track: "",
    is_first_gen: false,
    roles: ["", "", ""],
  });

  const [resumeFile,     setResumeFile]     = useState(null);
  const [linkedInUrl,    setLinkedInUrl]    = useState("");
  const [saving,         setSaving]         = useState(false);
  const [uploadingResume,setUploadingResume]= useState(false);
  const [savingLinkedIn, setSavingLinkedIn] = useState(false);
  const [error,          setError]          = useState(null);
  const [saveSuccess,    setSaveSuccess]    = useState(false);
  const [resumeStatus,   setResumeStatus]   = useState(null);
  const [linkedInStatus, setLinkedInStatus] = useState(null);

  useEffect(() => {
    if (!profile) return;
    const roles = ["", "", ""];
    (profile.target_roles || []).forEach((r) => { roles[r.rank - 1] = r.title; });
    setForm({
      degree_level: profile.degree_level || "",
      major_program: profile.major_program || "",
      expected_graduation: profile.expected_graduation
        ? profile.expected_graduation.substring(0, 7) : "",
      track: profile.track || "",
      is_first_gen: profile.is_first_gen ?? false,
      roles,
    });
    if (profile.resume_doc_id)  setResumeStatus("Uploaded");
    if (profile.linkedin_doc_id) setLinkedInStatus("Saved");
  }, [profile]);

  function handleRoleChange(rank, title) {
    setForm((prev) => {
      const roles = [...prev.roles];
      roles[rank - 1] = title;
      return { ...prev, roles };
    });
  }

  async function handleSaveQuestionnaire(e) {
    e.preventDefault();
    setError(null);
    setSaveSuccess(false);
    setSaving(true);
    try {
      const target_roles = form.roles
        .map((title, i) => ({ rank: i + 1, title: title.trim() }))
        .filter((r) => r.title.length > 0);
      await save({
        degree_level: form.degree_level || null,
        major_program: form.major_program || null,
        expected_graduation: form.expected_graduation || null,
        track: form.track || null,
        is_first_gen: form.is_first_gen,
        target_roles,
      });
      setSaveSuccess(true);
    } catch {
      setError("Failed to save. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  async function handleResumeUpload() {
    if (!resumeFile) return;
    setUploadingResume(true);
    setResumeStatus(null);
    try {
      await saveResume(resumeFile);
      setResumeStatus("Uploaded successfully");
      setResumeFile(null);
    } catch {
      setResumeStatus("Upload failed — check file type (PDF/DOCX, max 5 MB)");
    } finally {
      setUploadingResume(false);
    }
  }

  async function handleLinkedInSave() {
    if (!linkedInUrl.trim()) return;
    setSavingLinkedIn(true);
    setLinkedInStatus(null);
    try {
      await saveLinkedIn(linkedInUrl.trim());
      setLinkedInStatus("Saved");
    } catch {
      setLinkedInStatus("Failed to save. Check the URL and try again.");
    } finally {
      setSavingLinkedIn(false);
    }
  }

  if (loading) {
    return (
      <>
        <NavBar />
        <div className="page-shell">
          <div className="loading-state">
            <div className="spinner" />
            <span>Loading your profile…</span>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <NavBar />
      <div className="page-shell">
        <div className="page-content intake-page fade-up">

          {/* Header */}
          <div className="page-header">
            <button className="page-back" onClick={() => navigate("/dashboard")}>
              ← Back
            </button>
          </div>
          <div className="page-title-block" style={{ marginBottom: "var(--s8)" }}>
            <p className="page-eyebrow">Step 1</p>
            <h1 className="page-title">Build Your Profile</h1>
          </div>

          {/* Background & Goals */}
          <div className="form-card">
            <div className="form-card-header">
              <div className="form-card-title">Background & Goals</div>
              <div className="form-card-desc">
                Tell Clara about your academic program and career direction.
              </div>
            </div>

            <form onSubmit={handleSaveQuestionnaire}>
              <div className="form-grid" style={{ marginBottom: "var(--s5)" }}>
                <div className="form-group">
                  <label className="form-label" htmlFor="degree_level">Degree level</label>
                  <select
                    id="degree_level"
                    className="form-select"
                    value={form.degree_level}
                    onChange={(e) => setForm((p) => ({ ...p, degree_level: e.target.value }))}
                  >
                    <option value="">Select…</option>
                    {DEGREE_LEVELS.map((d) => (
                      <option key={d.value} value={d.value}>{d.label}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="major_program">Major / Program</label>
                  <input
                    id="major_program"
                    className="form-input"
                    type="text"
                    value={form.major_program}
                    onChange={(e) => setForm((p) => ({ ...p, major_program: e.target.value }))}
                    placeholder="e.g. Computer Science"
                  />
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="expected_graduation">Expected graduation</label>
                  <input
                    id="expected_graduation"
                    className="form-input"
                    type="month"
                    value={form.expected_graduation}
                    onChange={(e) => setForm((p) => ({ ...p, expected_graduation: e.target.value }))}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label" htmlFor="track">Career track</label>
                  <select
                    id="track"
                    className="form-select"
                    value={form.track}
                    onChange={(e) => setForm((p) => ({ ...p, track: e.target.value }))}
                  >
                    <option value="">Select…</option>
                    {TRACKS.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-checkbox-row" style={{ marginBottom: "var(--s6)" }}>
                <input
                  id="first_gen"
                  type="checkbox"
                  checked={form.is_first_gen}
                  onChange={(e) => setForm((p) => ({ ...p, is_first_gen: e.target.checked }))}
                />
                <label htmlFor="first_gen" className="form-label" style={{ fontWeight: 500, cursor: "pointer" }}>
                  I am a first-generation college student <span style={{ color: "var(--mist)", fontWeight: 400 }}>(optional)</span>
                </label>
              </div>

              <div style={{ marginBottom: "var(--s6)" }}>
                <p className="form-label" style={{ marginBottom: "var(--s3)" }}>
                  Target Roles <span style={{ color: "var(--mist)", fontWeight: 400 }}>— ranked 1 to 3</span>
                </p>
                <div className="form-stack">
                  {[1, 2, 3].map((rank) => (
                    <RankedRoleInput
                      key={rank}
                      rank={rank}
                      value={form.roles[rank - 1]}
                      onChange={handleRoleChange}
                    />
                  ))}
                </div>
              </div>

              {error   && <div className="status-error"   style={{ marginBottom: "var(--s4)" }}>{error}</div>}
              {saveSuccess && <div className="status-success" style={{ marginBottom: "var(--s4)" }}>✓ Profile saved successfully</div>}

              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? "Saving…" : "Save Profile"}
              </button>
            </form>
          </div>

          {/* Resume upload */}
          <div className="form-card">
            <div className="form-card-header">
              <div className="form-card-title">Resume</div>
              <div className="form-card-desc">Upload a PDF or DOCX (max 5 MB). Clara will parse it automatically.</div>
            </div>

            {resumeStatus && (
              <div className={resumeStatus.includes("fail") || resumeStatus.includes("failed")
                ? "status-error" : "status-success"}
                style={{ marginBottom: "var(--s4)" }}
              >
                {resumeStatus.includes("fail") || resumeStatus.includes("failed") ? "⚠ " : "✓ "}
                {resumeStatus}
              </div>
            )}

            <div className="upload-zone" style={{ marginBottom: "var(--s4)" }}>
              <div className="upload-zone-icon">📎</div>
              <div className="upload-zone-label">
                {resumeFile ? resumeFile.name : "Click to select a file"}
              </div>
              <div className="upload-zone-hint">PDF or DOCX — max 5 MB</div>
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={(e) => setResumeFile(e.target.files[0] || null)}
                style={{
                  position: "absolute",
                  inset: 0,
                  opacity: 0,
                  cursor: "pointer",
                  width: "100%",
                  height: "100%",
                }}
              />
            </div>

            <div style={{ position: "relative" }}>
              <button
                className="btn btn-primary"
                onClick={handleResumeUpload}
                disabled={!resumeFile || uploadingResume}
              >
                {uploadingResume ? "Uploading…" : "Upload Resume"}
              </button>
            </div>
          </div>

          {/* LinkedIn */}
          <div className="form-card">
            <div className="form-card-header">
              <div className="form-card-title">LinkedIn Profile</div>
              <div className="form-card-desc">
                Optionally share your LinkedIn URL so Clara can enrich your profile.
              </div>
            </div>

            {linkedInStatus && (
              <div className={linkedInStatus.includes("fail") ? "status-error" : "status-success"}
                style={{ marginBottom: "var(--s4)" }}
              >
                {linkedInStatus.includes("fail") ? "⚠ " : "✓ "}{linkedInStatus}
              </div>
            )}

            <div className="form-group" style={{ marginBottom: "var(--s4)" }}>
              <label className="form-label" htmlFor="linkedin_url">LinkedIn URL</label>
              <input
                id="linkedin_url"
                className="form-input"
                type="url"
                value={linkedInUrl}
                onChange={(e) => setLinkedInUrl(e.target.value)}
                placeholder="https://linkedin.com/in/your-profile"
              />
            </div>

            <button
              className="btn btn-primary"
              onClick={handleLinkedInSave}
              disabled={!linkedInUrl.trim() || savingLinkedIn}
            >
              {savingLinkedIn ? "Saving…" : "Save LinkedIn"}
            </button>
          </div>

        </div>
      </div>
    </>
  );
}
