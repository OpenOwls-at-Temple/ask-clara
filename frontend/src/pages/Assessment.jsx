import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAssessment } from "../hooks/useAssessment";
import NavBar from "../components/NavBar";

export default function Assessment() {
  const { assessments, loading, error, load, run } = useAssessment();
  const navigate = useNavigate();

  useEffect(() => { load(); }, []);

  const latest = assessments[0];

  return (
    <>
      <NavBar />
      <div className="page-shell">
        <div className="page-content fade-up">

          {/* Header */}
          <div className="page-header">
            <button className="page-back" onClick={() => navigate("/dashboard")}>← Dashboard</button>
          </div>
          <div className="page-title-block" style={{ marginBottom: "var(--s8)" }}>
            <p className="page-eyebrow">AI-Powered</p>
            <h1 className="page-title">Career Assessment</h1>
          </div>

          {/* Run card */}
          <div className="assessment-run-card">
            <div className="assessment-run-info">
              <div className="assessment-run-title">
                {latest ? "Run a new assessment" : "Get your first assessment"}
              </div>
              <div className="assessment-run-desc">
                Clara reviews your profile and resume against your target roles to identify
                strengths, gaps, and concrete next steps.
              </div>
            </div>
            <button className="btn btn-primary btn-lg" onClick={run} disabled={loading}>
              {loading ? (
                <><div className="spinner" style={{ borderTopColor: "white", borderColor: "rgba(255,255,255,0.3)" }} /> Analyzing…</>
              ) : latest ? "Run New Assessment" : "Run Assessment"}
            </button>
          </div>

          {error && (
            <div className="status-error" style={{ marginBottom: "var(--s6)" }}>
              ⚠ {error.message || "Something went wrong. Please try again."}
            </div>
          )}

          {loading && !latest && (
            <div className="loading-state">
              <div className="spinner" />
              <span>Clara is reviewing your profile…</span>
            </div>
          )}

          {!loading && !latest && !error && (
            <div className="empty-state">
              <div className="empty-state-icon">🧠</div>
              <div className="empty-state-title">No assessment yet</div>
              <div className="empty-state-desc">
                Run your first assessment to get personalized insights.
              </div>
            </div>
          )}

          {latest && (
            <div>
              <div className="assessment-meta">
                Generated {new Date(latest.created_at).toLocaleString()}
              </div>

              {/* Strengths */}
              <div className="result-section">
                <div className="result-section-header">
                  <span className="result-section-label">Strengths</span>
                  <div className="result-section-line" />
                </div>
                {latest.strengths.length === 0 ? (
                  <p className="t-small">None identified.</p>
                ) : (
                  <div className="result-list">
                    {latest.strengths.map((s, i) => (
                      <div key={i} className="result-item item-strength">
                        <div className="result-item-icon">✓</div>
                        <div className="result-item-body">{s}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Gaps */}
              <div className="result-section">
                <div className="result-section-header">
                  <span className="result-section-label">Gaps</span>
                  <div className="result-section-line" />
                </div>
                {latest.gaps.length === 0 ? (
                  <p className="t-small">No gaps identified.</p>
                ) : (
                  <div className="result-list">
                    {latest.gaps.map((g, i) => (
                      <div key={i} className="result-item item-gap">
                        <div className="result-item-icon">△</div>
                        <div className="result-item-body">
                          <div className="result-item-label">
                            {g.area}
                            <span className="result-item-tag">Role #{g.target_rank}</span>
                          </div>
                          {g.why && <div>{g.why}</div>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Recommendations */}
              <div className="result-section">
                <div className="result-section-header">
                  <span className="result-section-label">Recommendations</span>
                  <div className="result-section-line" />
                </div>
                {latest.recommendations.length === 0 ? (
                  <p className="t-small">No recommendations.</p>
                ) : (
                  <div className="result-list">
                    {latest.recommendations.map((r, i) => (
                      <div key={i} className="result-item item-rec">
                        <div className="result-item-icon" style={{ fontWeight: 700, color: "var(--cherry)" }}>
                          {i + 1}
                        </div>
                        <div className="result-item-body">
                          <div className="result-item-label">{r.action}</div>
                          {r.rationale && <div>{r.rationale}</div>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="counselor-note">
                This assessment is a starting point. A Temple Career Center counselor can help
                you go further — visit <strong>temple.edu/life-at-temple/careers</strong> to book an appointment.
              </div>
            </div>
          )}

        </div>
      </div>
    </>
  );
}
