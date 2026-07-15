import { useEffect, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { listLeads } from "../services/leads";

const NAV_LINKS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/intake", label: "Profile" },
  { to: "/assessment", label: "Assessment" },
  { to: "/resumes", label: "Resumes" },
  { to: "/plan", label: "Plan" },
  { to: "/leads", label: "Leads" },
  { to: "/materials", label: "Materials" },
];

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [newLeadCount, setNewLeadCount] = useState(0);

  // In-app notification: count of unseen job leads (Feature 7).
  useEffect(() => {
    let cancelled = false;
    listLeads()
      .then((leads) => {
        if (!cancelled) {
          setNewLeadCount(leads.filter((l) => l.status === "new").length);
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [location.pathname]);

  async function handleLogout() {
    await logout();
    navigate("/signin", { replace: true });
  }

  return (
    <nav className="app-nav">
      <div
        className="nav-wordmark"
        onClick={() => navigate("/dashboard")}
        style={{ cursor: "pointer" }}
      >
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
            {to === "/leads" && newLeadCount > 0 && (
              <span className="nav-badge">{newLeadCount}</span>
            )}
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
