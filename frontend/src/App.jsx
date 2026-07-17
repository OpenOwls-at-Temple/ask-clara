import { Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider, useAuth } from "./hooks/useAuth";
import Assessment from "./pages/Assessment";
import Dashboard from "./pages/Dashboard";
import HowItWorks from "./pages/HowItWorks";
import Intake from "./pages/Intake";
import JobLeads from "./pages/JobLeads";
import Materials from "./pages/Materials";
import Plan from "./pages/Plan";
import Resumes from "./pages/Resumes";
import SignIn from "./pages/SignIn";

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/signin" replace />;
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/signin" element={<SignIn />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/how-it-works"
          element={
            <ProtectedRoute>
              <HowItWorks />
            </ProtectedRoute>
          }
        />
        <Route
          path="/intake"
          element={
            <ProtectedRoute>
              <Intake />
            </ProtectedRoute>
          }
        />
        <Route
          path="/assessment"
          element={
            <ProtectedRoute>
              <Assessment />
            </ProtectedRoute>
          }
        />
        <Route
          path="/resumes"
          element={
            <ProtectedRoute>
              <Resumes />
            </ProtectedRoute>
          }
        />
        <Route
          path="/plan"
          element={
            <ProtectedRoute>
              <Plan />
            </ProtectedRoute>
          }
        />
        <Route
          path="/leads"
          element={
            <ProtectedRoute>
              <JobLeads />
            </ProtectedRoute>
          }
        />
        <Route
          path="/materials"
          element={
            <ProtectedRoute>
              <Materials />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/signin" replace />} />
      </Routes>
    </AuthProvider>
  );
}
