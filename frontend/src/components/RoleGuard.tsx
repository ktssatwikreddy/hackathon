import type { ReactNode } from "react";

import { useAuth } from "../store/auth";
import type { Role } from "../types";

interface Props {
  roles: Role[];
  children: ReactNode;
}

/** Renders children only if the current user has one of the allowed roles. */
export default function RoleGuard({ roles, children }: Props) {
  const user = useAuth((s) => s.user);
  if (!user || !roles.includes(user.role)) return null;
  return <>{children}</>;
}
