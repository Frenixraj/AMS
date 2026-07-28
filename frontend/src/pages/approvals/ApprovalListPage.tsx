import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { RequestTable } from "@/components/approvals/RequestTable";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { approvalService } from "@/services/approval.service";
import type {
  AssetRequestListItem,
  AssetRequestListParams,
  RequestPriority,
  RequestStatus,
} from "@/types/approvals";
import { REQUEST_PRIORITIES, REQUEST_STATUSES } from "@/types/approvals";

export function ApprovalListPage() {
  const { user } = useAuth();
  const canCreate = Boolean(user?.employee_profile);

  const [params, setParams] = useState<AssetRequestListParams>({
    page: 1,
    search: "",
    status: "",
    priority: "",
    ordering: "-created_at",
  });
  const [rows, setRows] = useState<AssetRequestListItem[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const pageCount = useMemo(() => Math.max(1, Math.ceil(count / 20)), [count]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await approvalService.list(params);
      setRows(data.results);
      setCount(data.count);
    } catch {
      setError("Failed to load requests.");
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    const handle = window.setTimeout(() => void load(), 200);
    return () => window.clearTimeout(handle);
  }, [load]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Approvals</h1>
          <p className="text-sm text-muted-foreground">
            Request → Manager decision → IT allocation.
          </p>
        </div>
        {canCreate && (
          <Button asChild>
            <Link to="/approvals/new">New request</Link>
          </Button>
        )}
      </div>

      <div className="grid gap-4 rounded-lg border p-4 md:grid-cols-4">
        <div className="space-y-2 md:col-span-2">
          <Label htmlFor="req-search">Search</Label>
          <Input
            id="req-search"
            placeholder="Request number, email, tag…"
            value={params.search ?? ""}
            onChange={(e) => setParams({ ...params, search: e.target.value, page: 1 })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="req-status">Status</Label>
          <select
            id="req-status"
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
            value={params.status ?? ""}
            onChange={(e) =>
              setParams({
                ...params,
                status: e.target.value as RequestStatus | "",
                page: 1,
              })
            }
          >
            <option value="">All</option>
            {REQUEST_STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="req-priority">Priority</Label>
          <select
            id="req-priority"
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
            value={params.priority ?? ""}
            onChange={(e) =>
              setParams({
                ...params,
                priority: e.target.value as RequestPriority | "",
                page: 1,
              })
            }
          >
            <option value="">All</option>
            {REQUEST_PRIORITIES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Requests</CardTitle>
          <CardDescription>
            {count} total · page {params.page ?? 1} of {pageCount}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && <p className="text-sm text-destructive">{error}</p>}
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : (
            <RequestTable requests={rows} />
          )}
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={(params.page ?? 1) <= 1 || loading}
              onClick={() => setParams((p) => ({ ...p, page: (p.page ?? 1) - 1 }))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={(params.page ?? 1) >= pageCount || loading}
              onClick={() => setParams((p) => ({ ...p, page: (p.page ?? 1) + 1 }))}
            >
              Next
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
