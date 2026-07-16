import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";
import { testLogin } from "../services/auth";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

export default function SignIn() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const btnRef = useRef(null);
  const [testEmail, setTestEmail] = useState("test1@temple.edu");

  const handleTestLogin = async (e) => {
    e.preventDefault();
    try {
      await testLogin(testEmail);
      // Full reload so the AuthProvider restores the session from the new refresh cookie
      window.location.href = "/dashboard";
    } catch {
      alert(
        "Test login failed. Check that the backend runs with ENVIRONMENT=local and TEST_LOGIN_SECRET set.",
      );
    }
  };

  useEffect(() => {
    if (user) {
      navigate("/dashboard", { replace: true });
      return;
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    document.body.appendChild(script);

    script.onload = () => {
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: async ({ credential }) => {
          try {
            await login(credential);
            navigate("/dashboard", { replace: true });
          } catch {
            alert(
              "Sign-in failed. Make sure you're using your Temple University email.",
            );
          }
        },
      });
      if (btnRef.current) {
        window.google.accounts.id.renderButton(btnRef.current, {
          theme: "outline",
          size: "large",
          text: "signin_with",
          width: "320",
        });
      }
    };

    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
    };
  }, [user, login, navigate]);

  return (
    <div className="signin-page">
      {/* Left brand panel */}
      <div className="signin-brand fade-up">
        <div className="signin-brand-stripe" />
        <div className="signin-brand-grid" />

        <div className="signin-brand-content">
          <div className="signin-wordmark">
            <div className="signin-wordmark-icon">C</div>
            <span className="signin-wordmark-text">Ask Clara</span>
            <span className="signin-wordmark-beta">(Beta Version)</span>
          </div>

          <h1 className="signin-headline">
            Your career.
            <br />
            <em>Coached by AI.</em>
          </h1>

          <p className="signin-tagline">
            Clara uses your resume and goals to give you personalized career
            coaching — assessments, tailored resumes, and concrete next steps.
          </p>

          <div className="signin-features">
            {[
              "AI-powered career assessment",
              "Tailored resumes for each role",
              "Gap analysis and action plans",
              "Built for Temple University students",
            ].map((f) => (
              <div key={f} className="signin-feature">
                <div className="signin-feature-dot" />
                <span>{f}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="signin-footer">
          Developed in partnership with Temple University Career Center. Clara
          complements, not replaces, your career counselor.
        </div>
      </div>

      {/* Right auth panel */}
      <div className="signin-panel">
        <div className="signin-panel-inner fade-up">
          <p className="signin-panel-eyebrow">Temple University</p>
          <h2 className="signin-panel-title">Welcome back</h2>
          <p className="signin-panel-sub">
            Sign in with your Temple University Google account to access your
            coaching dashboard.
          </p>

          <div className="signin-google-wrap">
            <div ref={btnRef} />
          </div>

          {import.meta.env.MODE === "development" && (
            <div
              style={{
                marginTop: "2rem",
                padding: "1rem",
                background: "rgba(255,255,255,0.05)",
                borderRadius: "8px",
              }}
            >
              <p
                style={{
                  fontSize: "0.8rem",
                  opacity: 0.7,
                  marginBottom: "0.5rem",
                }}
              >
                Local Development Only:
              </p>
              <form
                onSubmit={handleTestLogin}
                style={{ display: "flex", gap: "0.5rem" }}
              >
                <input
                  type="email"
                  value={testEmail}
                  onChange={(e) => setTestEmail(e.target.value)}
                  className="input input-sm"
                  style={{ flex: 1 }}
                />
                <button type="submit" className="btn btn-sm btn-secondary">
                  Test Login
                </button>
              </form>
            </div>
          )}

          <div className="signin-divider">
            <span className="signin-divider-text">
              temple.edu accounts only
            </span>
          </div>

          <p className="signin-note">
            By signing in you agree to Clara's terms of service. Your data is
            used only to personalize your coaching experience.
          </p>
        </div>
      </div>
    </div>
  );
}
