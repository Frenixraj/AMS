import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";
import { reportService, type ExportReportKey } from "@/services/report.service";
import { tokenStorage } from "@/utils/tokenStorage";

const EXPORTS: Array<{
  key: ExportReportKey;
  title: string;
  description: string;
}> = [
  {
    key: "assets-by-department",
    title: "Assets by Department",
    description: "Currently allocated assets grouped by holding department.",
  },
  {
    key: "assets-by-category",
    title: "Assets by Category",
    description: "Full inventory sorted by category with summary counts.",
  },
  {
    key: "allocation-history",
    title: "Allocation History",
    description: "All assignment records including returns.",
  },
  {
    key: "maintenance-history",
    title: "Maintenance History",
    description: "Issue tickets, status, assignees, and resolutions.",
  },
];

export function ReportsPage() {
  const { user } = useAuth();
  const canExport = user?.role === "ADMIN" || user?.role === "IT_TEAM";
  const [inventory, setInventory] = useState<Awaited<ReturnType<typeof reportService.inventory>> | null>(null);
  const [warranty, setWarranty] = useState<Awaited<ReturnType<typeof reportService.warranty>> | null>(null);
  const [allocations, setAllocations] = useState<Awaited<ReturnType<typeof reportService.allocations>> | null>(null);
  const [requests, setRequests] = useState<Awaited<ReturnType<typeof reportService.requests>> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [inv, war, alloc, req] = await Promise.all([
          reportService.inventory(),
          reportService.warranty(90),
          reportService.allocations(),
          reportService.requests(),
        ]);
        setInventory(inv);
        setWarranty(war);
        setAllocations(alloc);
        setRequests(req);
      } catch {
        setError("Failed to load reports.");
      }
    };
    void load();
  }, []);

  const downloadCsv = async () => {
    const token = tokenStorage.getAccessToken();
    const response = await fetch(reportService.inventoryCsvUrl(), {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "asset_inventory.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const runExport = async (key: ExportReportKey, format: "xlsx" | "pdf") => {
    setBusyKey(`${key}-${format}`);
    setError(null);
    try {
      if (format === "xlsx") {
        await reportService.downloadExcel(key);
      } else {
        await reportService.downloadPdf(key);
      }
    } catch {
      setError(`Failed to download ${key} (${format.toUpperCase()}).`);
    } finally {
      setBusyKey(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Reports</h1>
          <p className="text-sm text-muted-foreground">
            Live summaries plus Excel (openpyxl) and PDF (ReportLab) exports.
          </p>
        </div>
        {canExport && (
          <Button variant="outline" onClick={() => void downloadCsv()}>
            Export inventory CSV
          </Button>
        )}
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}

      {canExport && (
        <div className="grid gap-4 md:grid-cols-2">
          {EXPORTS.map((item) => (
            <Card key={item.key}>
              <CardHeader>
                <CardTitle className="text-base">{item.title}</CardTitle>
                <CardDescription>{item.description}</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  disabled={busyKey === `${item.key}-xlsx`}
                  onClick={() => void runExport(item.key, "xlsx")}
                >
                  {busyKey === `${item.key}-xlsx` ? "Preparing…" : "Excel (.xlsx)"}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busyKey === `${item.key}-pdf`}
                  onClick={() => void runExport(item.key, "pdf")}
                >
                  {busyKey === `${item.key}-pdf` ? "Preparing…" : "PDF"}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!canExport && (
        <p className="text-sm text-muted-foreground">
          Excel/PDF exports are available to Admin and IT Team roles.
        </p>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Inventory by status</CardTitle>
            <CardDescription>Total assets: {inventory?.total ?? "—"}</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {inventory?.by_status.map((row) => (
                <li key={row.status} className="flex justify-between border-b pb-1">
                  <span>{row.status}</span>
                  <span className="tabular-nums font-medium">{row.count}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Request pipeline</CardTitle>
            <CardDescription>Total requests: {requests?.total ?? "—"}</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {requests?.results.map((row) => (
                <li key={row.status} className="flex justify-between border-b pb-1">
                  <span>{row.status}</span>
                  <span className="tabular-nums font-medium">{row.count}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Allocations by department</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {allocations?.results.map((row) => (
                <li key={row.department_code} className="flex justify-between border-b pb-1">
                  <span>
                    {row.department} ({row.department_code})
                  </span>
                  <span className="tabular-nums font-medium">{row.active_allocations}</span>
                </li>
              ))}
              {!allocations?.results.length && (
                <li className="text-muted-foreground">No active allocations.</li>
              )}
            </ul>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Warranty expiring (90 days)</CardTitle>
            <CardDescription>{warranty?.count ?? 0} assets</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {warranty?.results.map((row) => (
                <li key={row.id} className="border-b pb-1">
                  <span className="font-mono text-xs">{row.asset_tag}</span> · {row.name}
                  <div className="text-xs text-muted-foreground">
                    Expires {row.warranty_expiry} · {row.status}
                  </div>
                </li>
              ))}
              {!warranty?.results.length && (
                <li className="text-muted-foreground">None in window.</li>
              )}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
