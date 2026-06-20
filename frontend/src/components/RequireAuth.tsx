import { Navigate } from "react-router-dom";

import { useAuth } from "../auth/context";

// Route guard: redirect unauthenticated users to /login.
export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="container">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
