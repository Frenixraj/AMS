import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "@/hooks/useAuth";
import type { AppRole } from "@/utils/roles";
import { hasRole } from "@/utils/roles";

type RequireRoleProps = {
  roles: AppRole[];
  /** Where to send authenticated users who lack the role. */
  fallback?: string;
};

/**
 * Nest under ProtectedRoute. Allows only the listed roles through.
 */
export function RequireRole({ roles, fallback = "/dashboard" }: RequireRoleProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (!hasRole(user, roles)) {
    return <Navigate to={fallback} replace />;
  }

  return <Outlet />;
}
