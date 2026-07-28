import { useEffect, useMemo, useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { notificationService } from "@/services/notification.service";
import { cn } from "@/lib/utils";
import type { AppRole } from "@/utils/roles";

type NavItem = {
  label: string;
  to: string;
  roles?: AppRole[];
};

const ALL_NAV: NavItem[] = [
  { label: "Dashboard", to: "/dashboard" },
  { label: "Assets", to: "/assets" },
  { label: "Scan QR", to: "/assets/scan" },
  { label: "Master data", to: "/master-data", roles: ["ADMIN", "IT_TEAM"] },
  { label: "Employees", to: "/employees", roles: ["ADMIN", "IT_TEAM", "MANAGER"] },
  { label: "Approvals", to: "/approvals" },
  { label: "Maintenance", to: "/maintenance" },
  { label: "Notifications", to: "/notifications" },
  { label: "Reports", to: "/reports", roles: ["ADMIN", "IT_TEAM", "MANAGER"] },
  { label: "Audit", to: "/audit", roles: ["ADMIN", "IT_TEAM"] },
];

export function MainLayout() {
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [unread, setUnread] = useState(0);

  const navItems = useMemo(() => {
    const role = user?.role;
    return ALL_NAV.filter((item) => {
      if (!item.roles) return true;
      return role != null && item.roles.includes(role);
    });
  }, [user?.role]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const count = await notificationService.unreadCount();
        if (!cancelled) setUnread(count);
      } catch {
        // ignore badge errors
      }
    };
    void load();
    const id = window.setInterval(() => {
      if (document.visibilityState === "visible") void load();
    }, 60000);
    return () => {
      cancelled = true;
      window.clearInterval(id);
    };
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-4">
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="text-lg font-semibold">
              AssetFlow
            </Link>
            <nav className="hidden flex-wrap gap-3 lg:flex" aria-label="Primary">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      "text-sm hover:text-foreground",
                      isActive ? "font-medium text-foreground" : "text-muted-foreground"
                    )
                  }
                >
                  {item.label}
                  {item.to === "/notifications" && unread > 0 ? ` (${unread})` : ""}
                </NavLink>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            {user && (
              <span className="hidden text-sm text-muted-foreground sm:inline">
                {user.email}
                {user.role ? ` · ${user.role}` : ""}
              </span>
            )}
            <Button
              variant="outline"
              size="sm"
              className="lg:hidden"
              aria-expanded={mobileOpen}
              aria-controls="mobile-nav"
              onClick={() => setMobileOpen((v) => !v)}
            >
              Menu
            </Button>
            <Button variant="outline" size="sm" onClick={logout}>
              Logout
            </Button>
          </div>
        </div>
        {mobileOpen && (
          <nav
            id="mobile-nav"
            className="flex flex-col gap-2 border-t px-4 py-3 lg:hidden"
            aria-label="Mobile"
          >
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  cn(
                    "rounded-md px-2 py-1.5 text-sm",
                    isActive ? "bg-muted font-medium" : "text-muted-foreground"
                  )
                }
              >
                {item.label}
                {item.to === "/notifications" && unread > 0 ? ` (${unread})` : ""}
              </NavLink>
            ))}
          </nav>
        )}
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
