import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAssessment } from "../hooks/useAssessment";

export default function Assessment() {
  const { assessments, loading, error, load, run } = useAssessment();
  const navigate = useNavigate();

  useEffect(() => {
    load();
  }, []);

  const latest = assessments[0];

  async function handleRun() {
    await run();
  }

  return (
    <div className="assessment-page">
      <header>
        <button onClick={() => navigate("/dashboard")}>&larr; Dashboard</button>
        <h1>AI Assessment</h1>
      </header>

      <p>
        Clara reviews your profile and resume against your target roles to identify
        strengths, gaps, and concrete next steps.
      </p>

      {error && (
        <p className="error-message">
          {error.message || "Something went wrong. Please try again."}
        </p>
      )}

      <button onClick={handleRun} disabled={loading}>
        {loading ? "Running…" : latest ? "Run New Assessment" : "Run Assessment"}
      </button>

      {loading && !latest && <p>Clara is reviewing your profile…</p>}

      {!loading && !latest && !error && (
        <p>No assessment yet. Click &ldquo;Run Assessment&rdquo; to get started.</p>
      )}

      {latest && (
        <div className="assessment-result">
          <p className="assessment-date">
            Generated {new Date(latest.created_at).toLocaleString()}
          </p>

          <section>
            <h2>Strengths</h2>
            {latest.strengths.length === 0 ? (
              <p>None identified.</p>
            ) : (
              <ul>
                {latest.strengths.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h2>Gaps</h2>
            {latest.gaps.length === 0 ? (
              <p>No gaps identified.</p>
            ) : (
              <ul>
                {latest.gaps.map((g, i) => (
                  <li key={i}>
                    <strong>{g.area}</strong>{" "}
                    <span className="gap-rank">(Target role #{g.target_rank})</span>
                    {g.why && <span>: {g.why}</span>}
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section>
            <h2>Recommendations</h2>
            {latest.recommendations.length === 0 ? (
              <p>No recommendations.</p>
            ) : (
              <ol>
                {latest.recommendations.map((r, i) => (
                  <li key={i}>
                    <strong>{r.action}</strong>
                    {r.rationale && <span>: {r.rationale}</span>}
                  </li>
                ))}
              </ol>
            )}
          </section>

          <p className="counselor-note">
            This assessment is a starting point. A Temple Career Center counselor
            can help you go further.
          </p>
        </div>
      )}
    </div>
  );
}
