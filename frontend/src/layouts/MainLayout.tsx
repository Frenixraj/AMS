import { useEffect, useMemo, useState } from "react";
import { Link, NavLink, Outlet } from "react-router-dom";

import { Logo } from "@/components/brand/Logo";
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

/**
 * Role-aware navigation.
 * Every account is a person (login + department profile). Roles add privileges:
 * - Employee / Manager: owned assets, Your requests, Maintenance, Profile
 * - Manager (+): Approvals, People (dept), Reports
 * - Admin / Asset Manager: inventory tools, People, Audit, …
 */
const ALL_NAV: NavItem[] = [
  { label: "Dashboard", to: "/dashboard" },
  { label: "Assets", to: "/assets" },
  {
    label: "Your requests",
    to: "/your-requests",
    roles: ["EMPLOYEE", "MANAGER"],
  },
  {
    label: "Approvals",
    to: "/approvals",
    roles: ["ADMIN", "ASSET_MANAGER", "IT_TEAM", "MANAGER"],
  },
  {
    label: "Scan QR",
    to: "/assets/scan",
    roles: ["ADMIN", "ASSET_MANAGER", "IT_TEAM"],
  },
  {
    label: "Master data",
    to: "/master-data",
    roles: ["ADMIN", "ASSET_MANAGER", "IT_TEAM"],
  },
  {
    label: "People",
    to: "/employees",
    roles: ["ADMIN", "ASSET_MANAGER", "IT_TEAM", "MANAGER"],
  },
  { label: "Maintenance", to: "/maintenance" },
  {
    label: "Reports",
    to: "/reports",
    roles: ["ADMIN", "ASSET_MANAGER", "IT_TEAM", "MANAGER"],
  },
  {
    label: "Audit",
    to: "/audit",
    roles: ["ADMIN", "ASSET_MANAGER", "IT_TEAM"],
  },
  { label: "Notifications", to: "/notifications" },
  { label: "Profile", to: "/profile" },
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
        // ignore
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
            <Link to="/dashboard" className="shrink-0" aria-label="AssetFlow home">
              <Logo imgClassName="h-8" />
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
              <Link
                to="/profile"
                className="hidden items-center gap-2 text-sm text-muted-foreground hover:text-foreground sm:flex"
              >
                {user.profile_picture_url ? (
                  <img
                    src={user.profile_picture_url}
                    alt=""
                    className="h-8 w-8 rounded-full object-cover"
                  />
                ) : (
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-xs font-medium">
                    {(user.first_name || user.email || "?").charAt(0).toUpperCase()}
                  </span>
                )}
                <span>
                  {user.email}
                  {user.role ? ` · ${user.role.replaceAll("_", " ")}` : ""}
                </span>
              </Link>
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
