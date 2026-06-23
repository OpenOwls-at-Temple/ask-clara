import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useProfile } from "../hooks/useProfile";

const DEGREE_LEVELS = ["undergrad", "grad", "phd"];
const TRACKS = ["industry", "academia", "government", "undecided"];

function RankedRoleInput({ rank, value, onChange }) {
  return (
    <div>
      <label>
        #{rank} target role
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(rank, e.target.value)}
          placeholder={`e.g. ${rank === 1 ? "Software Engineer" : rank === 2 ? "Data Scientist" : "Product Manager"}`}
          maxLength={200}
        />
      </label>
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

  const [resumeFile, setResumeFile] = useState(null);
  const [linkedInUrl, setLinkedInUrl] = useState("");
  const [saving, setSaving] = useState(false);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [savingLinkedIn, setSavingLinkedIn] = useState(false);
  const [error, setError] = useState(null);
  const [resumeStatus, setResumeStatus] = useState(null);
  const [linkedInStatus, setLinkedInStatus] = useState(null);

  // Pre-fill from saved profile
  useEffect(() => {
    if (!profile) return;
    const roles = ["", "", ""];
    (profile.target_roles || []).forEach((r) => {
      roles[r.rank - 1] = r.title;
    });
    setForm({
      degree_level: profile.degree_level || "",
      major_program: profile.major_program || "",
      expected_graduation: profile.expected_graduation || "",
      track: profile.track || "",
      is_first_gen: profile.is_first_gen ?? false,
      roles,
    });
    if (profile.resume_doc_id) setResumeStatus("Uploaded");
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

  if (loading) return <p>Loading...</p>;

  return (
    <div>
      <h1>Build Your Profile</h1>

      {/* Questionnaire */}
      <section>
        <h2>Your Background &amp; Goals</h2>
        <form onSubmit={handleSaveQuestionnaire}>
          <label>
            Degree level
            <select
              value={form.degree_level}
              onChange={(e) => setForm((p) => ({ ...p, degree_level: e.target.value }))}
            >
              <option value="">Select…</option>
              {DEGREE_LEVELS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </label>

          <label>
            Major / Program
            <input
              type="text"
              value={form.major_program}
              onChange={(e) => setForm((p) => ({ ...p, major_program: e.target.value }))}
              placeholder="e.g. Computer Science"
            />
          </label>

          <label>
            Expected graduation (YYYY-MM)
            <input
              type="month"
              value={form.expected_graduation}
              onChange={(e) => setForm((p) => ({ ...p, expected_graduation: e.target.value }))}
            />
          </label>

          <label>
            Career track
            <select
              value={form.track}
              onChange={(e) => setForm((p) => ({ ...p, track: e.target.value }))}
            >
              <option value="">Select…</option>
              {TRACKS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>

          <label>
            <input
              type="checkbox"
              checked={form.is_first_gen}
              onChange={(e) => setForm((p) => ({ ...p, is_first_gen: e.target.checked }))}
            />
            {" "}I am a first-generation college student (optional)
          </label>

          <h3>Target Roles — ranked 1 to 3</h3>
          {[1, 2, 3].map((rank) => (
            <RankedRoleInput
              key={rank}
              rank={rank}
              value={form.roles[rank - 1]}
              onChange={handleRoleChange}
            />
          ))}

          {error && <p style={{ color: "red" }}>{error}</p>}
          <button type="submit" disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </button>
        </form>
      </section>

      {/* Resume upload */}
      <section>
        <h2>Resume</h2>
        <p>Upload a PDF or DOCX (max 5 MB).</p>
        {resumeStatus && <p>{resumeStatus}</p>}
        <input
          type="file"
          accept=".pdf,.docx"
          onChange={(e) => setResumeFile(e.target.files[0] || null)}
        />
        <button onClick={handleResumeUpload} disabled={!resumeFile || uploadingResume}>
          {uploadingResume ? "Uploading…" : "Upload"}
        </button>
      </section>

      {/* LinkedIn */}
      <section>
        <h2>LinkedIn Profile</h2>
        {linkedInStatus && <p>{linkedInStatus}</p>}
        <input
          type="url"
          value={linkedInUrl}
          onChange={(e) => setLinkedInUrl(e.target.value)}
          placeholder="https://linkedin.com/in/your-profile"
        />
        <button onClick={handleLinkedInSave} disabled={!linkedInUrl.trim() || savingLinkedIn}>
          {savingLinkedIn ? "Saving…" : "Save"}
        </button>
      </section>

      <button onClick={() => navigate("/dashboard")}>Back to dashboard</button>
    </div>
  );
}
