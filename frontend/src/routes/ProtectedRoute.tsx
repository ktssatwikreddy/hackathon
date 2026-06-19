import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../store/auth";
import type { Role } from "../types";

interface Props {
  children: ReactNode;
  roles?: Role[];
}

export default function ProtectedRoute({ children, roles }: Props) {
  const user = useAuth((s) => s.user);
  const token = useAuth((s) => s.accessToken);
  if (!token || !user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return <>{children}</>;
}
