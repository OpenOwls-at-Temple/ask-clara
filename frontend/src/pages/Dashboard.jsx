import { useNavigate } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";
import { useProfile } from "../hooks/useProfile";
import NavBar from "../components/NavBar";

export default function Dashboard() {
  const { user } = useAuth();
  const { profile, loading } = useProfile();
  const navigate = useNavigate();

  const hasResume   = Boolean(profile?.resume_doc_id);
  const hasLinkedIn = Boolean(profile?.linkedin_doc_id);
  const roleCount   = profile?.target_roles?.length ?? 0;
  const profileComplete = hasResume && roleCount === 3;

  const firstName = user?.display_name?.split(" ")[0] ?? "there";

  const cards = [
    {
      key: "profile",
      icon: "👤",
      iconClass: profileComplete ? "icon-success" : "icon-cherry",
      title: "Profile & Intake",
      desc: "Your academic background, career track, and target roles.",
      status: loading ? "pending" : profileComplete ? "complete" : "active",
      badgeLabel: loading ? "Loading…" : profileComplete ? "Complete" : "Incomplete",
      action: profileComplete ? "Edit Profile" : "Get started",
      onAction: () => navigate("/intake"),
    },
    {
      key: "assessment",
      icon: "🧠",
      iconClass: profileComplete ? "icon-cherry" : "",
      title: "AI Assessment",
      desc: "Clara reviews your profile against your target roles to find strengths, gaps, and next steps.",
      status: !profileComplete ? "locked" : "active",
      badgeLabel: !profileComplete ? "Profile required" : "Ready",
      action: "View / Run",
      onAction: () => navigate("/assessment"),
      locked: !profileComplete,
    },
    {
      key: "resumes",
      icon: "📄",
      iconClass: profileComplete ? "icon-cherry" : "",
      title: "Tailored Resumes",
      desc: "Generate a customized resume for each of your target roles.",
      status: !profileComplete ? "locked" : "active",
      badgeLabel: !profileComplete ? "Profile required" : "Ready",
      action: "View / Generate",
      onAction: () => navigate("/resumes"),
      locked: !profileComplete,
    },
  ];

  const badgeClass = {
    complete: "badge-complete",
    active:   "badge-incomplete",
    locked:   "badge-incomplete",
    pending:  "badge-pending",
  };

  const cardClass = {
    complete: "card-complete",
    active:   "card-active",
    locked:   "card-locked",
    pending:  "",
  };

  return (
    <>
      <NavBar />
      <div className="page-shell">
        <div className="page-content fade-up">

          {/* Welcome */}
          <div className="dashboard-welcome">
            <p className="dashboard-greeting">Career Dashboard</p>
            <h1 className="dashboard-title">Hello, {firstName}</h1>
            <p className="dashboard-subtitle">
              Here's your coaching progress. Complete each step to unlock AI-powered insights.
            </p>
          </div>

          {/* Progress cards */}
          <p className="progress-label">Your Progress</p>
          <div className="progress-grid">
            {cards.map((card) => (
              <div
                key={card.key}
                className={`progress-card ${cardClass[card.status] || ""}`}
              >
                <div className="card-top">
                  <div className={`card-icon ${card.iconClass}`}>{card.icon}</div>
                  <span className={`badge ${badgeClass[card.status] || "badge-incomplete"}`}>
                    {card.badgeLabel}
                  </span>
                </div>

                <div>
                  <div className="card-title">{card.title}</div>
                  <div className="card-desc">{card.desc}</div>
                </div>

                <div className="card-action">
                  {card.locked ? (
                    <button className="btn btn-ghost btn-sm" disabled>
                      {card.action}
                    </button>
                  ) : (
                    <button
                      className={`btn btn-sm ${card.status === "complete" ? "btn-secondary" : "btn-primary"}`}
                      onClick={card.onAction}
                    >
                      {card.action}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Next-step banner */}
          {!loading && !hasResume && (
            <div className="next-step-banner">
              <div>
                <p className="next-step-label">Next Step</p>
                <p className="next-step-text">
                  Upload your resume to unlock your AI assessment and tailored resume generator.
                </p>
              </div>
              <button className="btn btn-primary" onClick={() => navigate("/intake")}>
                Upload Resume →
              </button>
            </div>
          )}

          {!loading && hasResume && !profileComplete && (
            <div className="next-step-banner">
              <div>
                <p className="next-step-label">Almost there</p>
                <p className="next-step-text">
                  Add {3 - roleCount} more target role{3 - roleCount !== 1 ? "s" : ""} to complete your profile.
                </p>
              </div>
              <button className="btn btn-primary" onClick={() => navigate("/intake")}>
                Edit Profile →
              </button>
            </div>
          )}

        </div>
      </div>
    </>
  );
}
