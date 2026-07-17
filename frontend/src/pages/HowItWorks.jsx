import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { useProfile } from "../hooks/useProfile";
import { markTutorialSeen } from "../utils/tutorial";
import NavBar from "../components/NavBar";

const STEPS = [
  {
    key: "profile",
    icon: "👤",
    title: "Build your profile",
    desc: "Upload your resume (PDF or DOCX), optionally add your LinkedIn export, answer a short questionnaire, and pick your 3 ranked target roles.",
    route: "/intake",
    action: "Go to Profile",
  },
  {
    key: "assessment",
    icon: "🧠",
    title: "Run your AI assessment",
    desc: "Clara reviews your profile against your target roles to surface strengths, gaps, and concrete next steps.",
    route: "/assessment",
    action: "Go to Assessment",
  },
  {
    key: "resumes",
    icon: "📄",
    title: "Generate tailored resumes",
    desc: "Get a customized resume draft for each of your three target roles — edit them and download as PDF or DOCX.",
    route: "/resumes",
    action: "Go to Resumes",
  },
  {
    key: "plan",
    icon: "🗺️",
    title: "Follow your 6-month plan",
    desc: "A roadmap of skills, experiences, and credentials with milestones you can check off as you go.",
    route: "/plan",
    action: "Go to Plan",
  },
  {
    key: "leads",
    icon: "🔍",
    title: "Review matched job leads",
    desc: "Clara scans for postings that fit your target roles every night — or on demand — and explains why each one fits.",
    route: "/leads",
    action: "Go to Leads",
  },
  {
    key: "materials",
    icon: "✉️",
    title: "Create application materials",
    desc: "For any specific posting, generate a tailored resume, cover letter, and employer brief.",
    route: "/materials",
    action: "Go to Materials",
  },
];

export default function HowItWorks() {
  const { profile, loading } = useProfile();
  const navigate = useNavigate();

  // Visiting the tutorial counts as having seen it — the dashboard will
  // never auto-redirect here again on this browser.
  useEffect(() => {
    markTutorialSeen();
  }, []);

  const hasResume = Boolean(profile?.resume_doc_id);
  const roleCount = profile?.target_roles?.length ?? 0;
  const profileComplete = hasResume && roleCount === 3;

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
          <div className="page-title-block">
            <p className="page-eyebrow">Getting Started</p>
            <h1 className="page-title">How Clara works</h1>
          </div>
          <p className="hiw-intro">
            Six steps from resume to application-ready. Complete step 1 to
            unlock everything else.
          </p>

          {/* Steps */}
          <ol className="hiw-steps">
            {STEPS.map((step, i) => {
              const locked = i > 0 && !profileComplete;
              return (
                <li key={step.key} className="hiw-step">
                  <div className="hiw-step-num">{i + 1}</div>
                  <div className="card-icon icon-cherry">{step.icon}</div>
                  <div className="hiw-step-body">
                    <div className="card-title">{step.title}</div>
                    <div className="card-desc">{step.desc}</div>
                  </div>
                  {locked ? (
                    <span className="badge badge-incomplete">
                      Unlocks after step 1
                    </span>
                  ) : (
                    <button
                      className="btn btn-ghost btn-sm"
                      onClick={() => navigate(step.route)}
                    >
                      {step.action} →
                    </button>
                  )}
                </li>
              );
            })}
          </ol>

          {/* CTA */}
          {!loading && !profileComplete && (
            <div className="next-step-banner">
              <div>
                <p className="next-step-label">Ready?</p>
                <p className="next-step-text">
                  Start with your profile — everything else unlocks from there.
                </p>
              </div>
              <button
                className="btn btn-primary"
                onClick={() => navigate("/intake")}
              >
                Get Started — Build Your Profile →
              </button>
            </div>
          )}

          {!loading && profileComplete && (
            <div className="next-step-banner">
              <div>
                <p className="next-step-label">You're all set</p>
                <p className="next-step-text">
                  Your profile is complete — pick up where you left off.
                </p>
              </div>
              <button
                className="btn btn-secondary"
                onClick={() => navigate("/dashboard")}
              >
                Back to Dashboard →
              </button>
            </div>
          )}

          <div className="counselor-note">
            Clara complements the Temple Career Center — she never replaces a
            counselor and never applies to jobs on your behalf. Visit{" "}
            <strong>temple.edu/life-at-temple/careers</strong> to book an
            appointment.
          </div>
        </div>
      </div>
    </>
  );
}
