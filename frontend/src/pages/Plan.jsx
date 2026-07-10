import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { usePlan } from "../hooks/usePlan";
import NavBar from "../components/NavBar";

export default function Plan() {
  const { plan, loading, error, load, generate, toggleItem } = usePlan();
  const navigate = useNavigate();

  useEffect(() => {
    load();
  }, []);

  const items = plan?.items ?? [];
  const doneCount = items.filter((item) => item.status === "complete").length;
  const pct = items.length ? Math.round((doneCount / items.length) * 100) : 0;

  return (
    <>
      <NavBar />
      <div className="page-shell">
        <div className="page-content fade-up">
          {/* Header */}
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
            <p className="page-eyebrow">Your Roadmap</p>
            <h1 className="page-title">6-Month Development Plan</h1>
          </div>

          {/* Generate card */}
          <div className="assessment-run-card">
            <div className="assessment-run-info">
              <div className="assessment-run-title">
                {plan ? "Regenerate your plan" : "Build your development plan"}
              </div>
              <div className="assessment-run-desc">
                Clara turns your latest assessment into a 6-month roadmap of
                skills, experiences, and credentials aimed at your target roles.
                {plan
                  ? " Regenerating replaces your current plan and progress."
                  : ""}
              </div>
            </div>
            <button
              className="btn btn-primary btn-lg"
              onClick={generate}
              disabled={loading}
            >
              {loading ? (
                <>
                  <div
                    className="spinner"
                    style={{
                      borderTopColor: "white",
                      borderColor: "rgba(255,255,255,0.3)",
                    }}
                  />{" "}
                  Planning…
                </>
              ) : plan ? (
                "Regenerate Plan"
              ) : (
                "Generate Plan"
              )}
            </button>
          </div>

          {error && (
            <div className="status-error" style={{ marginBottom: "var(--s6)" }}>
              ⚠ {error.message || "Something went wrong. Please try again."}
            </div>
          )}

          {loading && !plan && (
            <div className="loading-state">
              <div className="spinner" />
              <span>Clara is building your roadmap…</span>
            </div>
          )}

          {!loading && !plan && !error && (
            <div className="empty-state">
              <div className="empty-state-icon">🗺️</div>
              <div className="empty-state-title">No plan yet</div>
              <div className="empty-state-desc">
                Run an assessment first, then generate your personalized
                roadmap.
              </div>
            </div>
          )}

          {plan && (
            <div>
              <div className="assessment-meta">
                Generated {new Date(plan.created_at).toLocaleString()} ·{" "}
                {plan.horizon_months}-month horizon
              </div>

              {/* Progress */}
              <div className="plan-progress">
                <div className="plan-progress-text">
                  <span className="plan-progress-count">
                    {doneCount} of {items.length} complete
                  </span>
                  <span className="plan-progress-pct">{pct}%</span>
                </div>
                <div className="plan-progress-track">
                  <div
                    className="plan-progress-fill"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>

              {/* Items */}
              <div className="result-section">
                <div className="result-section-header">
                  <span className="result-section-label">Milestones</span>
                  <div className="result-section-line" />
                </div>
                <div className="result-list">
                  {items.map((item, i) => (
                    <div
                      key={i}
                      className={`result-item plan-item${item.status === "complete" ? " plan-item-done" : ""}`}
                    >
                      <button
                        className={`plan-item-check${item.status === "complete" ? " checked" : ""}`}
                        onClick={() => toggleItem(i)}
                        aria-label={
                          item.status === "complete"
                            ? "Mark as pending"
                            : "Mark as complete"
                        }
                      >
                        {item.status === "complete" ? "✓" : ""}
                      </button>
                      <div className="result-item-body">
                        <div className="result-item-label">
                          {item.skill}
                          {item.target_rank && (
                            <span className="result-item-tag">
                              Role #{item.target_rank}
                            </span>
                          )}
                        </div>
                        {item.why && <div>{item.why}</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="counselor-note">
                This plan is a starting point. A Temple Career Center counselor
                can help you refine it — visit{" "}
                <strong>temple.edu/life-at-temple/careers</strong> to book an
                appointment.
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
