import {
  AlertTriangle,
  Boxes,
  CheckCircle2,
  PackageCheck,
  ShieldAlert,
  Wrench,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  CategoryDistributionChart,
  DepartmentDistributionChart,
  MonthlyAllocationChart,
} from "@/components/dashboard/DashboardCharts";
import { RecentActivities } from "@/components/dashboard/RecentActivities";
import { StatWidget } from "@/components/dashboard/StatWidget";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { dashboardService } from "@/services/dashboard.service";
import type { DashboardSummary } from "@/types/dashboard";

export function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const summary = await dashboardService.getSummary(90);
        if (!cancelled) setData(summary);
      } catch {
        if (!cancelled) setError("Failed to load dashboard metrics.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Inventory health and allocation trends
            {user?.role ? ` · ${user.role.replaceAll("_", " ")}` : ""}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline" size="sm">
            <Link to="/assets">View assets</Link>
          </Button>
          <Button asChild variant="outline" size="sm">
            <Link to="/approvals">Approvals</Link>
          </Button>
        </div>
      </div>

      {error && (
        <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      {loading && !data ? (
        <p className="text-sm text-muted-foreground">Loading dashboard…</p>
      ) : data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
            <StatWidget
              title="Total assets"
              value={data.widgets.total_assets}
              icon={Boxes}
              tone="default"
            />
            <StatWidget
              title="Allocated"
              value={data.widgets.allocated}
              icon={PackageCheck}
              tone="info"
            />
            <StatWidget
              title="Available"
              value={data.widgets.available}
              icon={CheckCircle2}
              tone="success"
            />
            <StatWidget
              title="Maintenance"
              value={data.widgets.maintenance}
              icon={Wrench}
              tone="warning"
            />
            <StatWidget
              title="Lost"
              value={data.widgets.lost}
              icon={ShieldAlert}
              tone="danger"
            />
            <StatWidget
              title="Warranty expiring"
              value={data.widgets.warranty_expiring}
              hint={`Within ${data.widgets.warranty_window_days} days`}
              icon={AlertTriangle}
              tone="warning"
            />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <CategoryDistributionChart data={data.charts.category_distribution} />
            <DepartmentDistributionChart data={data.charts.department_distribution} />
          </div>

          <div className="grid gap-4 xl:grid-cols-5">
            <div className="xl:col-span-3">
              <MonthlyAllocationChart data={data.charts.monthly_allocations} />
            </div>
            <div className="xl:col-span-2">
              <RecentActivities items={data.recent_activities} />
            </div>
          </div>

          <p className="text-xs text-muted-foreground">
            Updated {new Date(data.generated_at).toLocaleString()}
          </p>
        </>
      ) : null}
    </div>
  );
}
