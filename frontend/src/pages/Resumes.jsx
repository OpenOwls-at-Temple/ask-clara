import { useNavigate } from "react-router-dom";
import NavBar from "../components/NavBar";

export default function Resumes() {
  const navigate = useNavigate();

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

          <div className="empty-state">
            <div className="empty-state-icon">📄</div>
            <div className="empty-state-title">Coming soon</div>
            <div className="empty-state-desc">
              Resume generation will be available in the next release.
            </div>
            <button className="btn btn-secondary" onClick={() => navigate("/dashboard")}>
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
