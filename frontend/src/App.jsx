import { Routes, Route, Navigate } from "react-router-dom";
import SignIn from "./pages/SignIn";
import Dashboard from "./pages/Dashboard";
import Intake from "./pages/Intake";
import Assessment from "./pages/Assessment";
import Resumes from "./pages/Resumes";
import JobLeads from "./pages/JobLeads";

export default function App() {
  return (
    <Routes>
      <Route path="/signin" element={<SignIn />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/intake" element={<Intake />} />
      <Route path="/assessment" element={<Assessment />} />
      <Route path="/resumes" element={<Resumes />} />
      <Route path="/leads" element={<JobLeads />} />
      <Route path="*" element={<Navigate to="/signin" replace />} />
    </Routes>
  );
}
