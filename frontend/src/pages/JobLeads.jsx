import { useNavigate } from "react-router-dom";
import NavBar from "../components/NavBar";

export default function JobLeads() {
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
            <p className="page-eyebrow">Curated</p>
            <h1 className="page-title">Job Leads</h1>
          </div>

          <div className="empty-state">
            <div className="empty-state-icon">🔍</div>
            <div className="empty-state-title">Coming soon</div>
            <div className="empty-state-desc">
              Job lead curation will be available in a future release.
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
