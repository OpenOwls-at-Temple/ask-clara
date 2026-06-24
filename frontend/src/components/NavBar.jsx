import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

const NAV_LINKS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/intake",    label: "Profile" },
  { to: "/assessment",label: "Assessment" },
  { to: "/resumes",   label: "Resumes" },
];

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  async function handleLogout() {
    await logout();
    navigate("/signin", { replace: true });
  }

  return (
    <nav className="app-nav">
      <div className="nav-wordmark" onClick={() => navigate("/dashboard")} style={{ cursor: "pointer" }}>
        <div className="nav-wordmark-icon">C</div>
        <span className="nav-wordmark-text">Ask Clara</span>
      </div>

      <div className="nav-links">
        {NAV_LINKS.map(({ to, label }) => (
          <button
            key={to}
            className={`nav-link${location.pathname === to ? " active" : ""}`}
            onClick={() => navigate(to)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="nav-user">
        {user?.display_name && (
          <span className="nav-user-name">{user.display_name}</span>
        )}
        <button className="nav-signout" onClick={handleLogout}>
          Sign out
        </button>
      </div>
    </nav>
  );
}
