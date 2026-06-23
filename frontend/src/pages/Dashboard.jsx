import { useNavigate } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";
import { useProfile } from "../hooks/useProfile";

export default function Dashboard() {
  const { user, logout } = useAuth();
  const { profile, loading } = useProfile();
  const navigate = useNavigate();

  const hasResume = profile?.resume_doc_id;
  const hasLinkedIn = profile?.linkedin_doc_id;
  const roleCount = profile?.target_roles?.length ?? 0;
  const profileComplete = hasResume && roleCount === 3;

  async function handleLogout() {
    await logout();
    navigate("/signin", { replace: true });
  }

  return (
    <div>
      <header>
        <h1>Ask Clara</h1>
        <span>
          {user?.display_name} &bull;{" "}
          <button onClick={handleLogout}>Sign out</button>
        </span>
      </header>

      <h2>Your Progress</h2>

      <ul>
        <li>
          <strong>Profile &amp; Intake</strong>{" "}
          {loading ? "…" : profileComplete ? "✓ Complete" : "Incomplete"}{" "}
          <button onClick={() => navigate("/intake")}>
            {profileComplete ? "Edit" : "Get started"}
          </button>
        </li>
        <li>
          <strong>AI Assessment</strong>{" "}
          {profileComplete ? (
            <button onClick={() => navigate("/assessment")}>View / Run</button>
          ) : (
            <span>Complete your profile first</span>
          )}
        </li>
        <li>
          <strong>Tailored Resumes</strong>{" "}
          {profileComplete ? (
            <button onClick={() => navigate("/resumes")}>View / Generate</button>
          ) : (
            <span>Complete your profile first</span>
          )}
        </li>
      </ul>

      {!loading && !hasResume && (
        <p>
          <strong>Next step:</strong>{" "}
          <button onClick={() => navigate("/intake")}>Upload your resume</button> to get started.
        </p>
      )}
    </div>
  );
}
