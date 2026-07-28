import { isAxiosError } from "axios";
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { RequestTimeline } from "@/components/approvals/RequestTimeline";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/hooks/useAuth";
import { approvalService } from "@/services/approval.service";
import { assetService } from "@/services/asset.service";
import type { AssetRequest } from "@/types/approvals";
import type { AssetListItem } from "@/types/assets";

export function ApprovalDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [request, setRequest] = useState<AssetRequest | null>(null);
  const [auditLogs, setAuditLogs] = useState<
    Array<{
      id: number;
      action: string;
      actor_email: string | null;
      changes: Record<string, unknown>;
      created_at: string;
    }>
  >([]);
  const [availableAssets, setAvailableAssets] = useState<AssetListItem[]>([]);
  const [comments, setComments] = useState("");
  const [fulfillAssetId, setFulfillAssetId] = useState<number | "">("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const role = user?.role;
  const isManager = role === "MANAGER" || role === "ADMIN";
  const isIT =
    role === "IT_TEAM" || role === "ASSET_MANAGER" || role === "ADMIN";
  const isOwner =
    user?.employee_profile?.id != null &&
    request?.requested_by === user.employee_profile.id;

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [detail, logs] = await Promise.all([
        approvalService.get(Number(id)),
        approvalService.auditLogs(Number(id)),
      ]);
      setRequest(detail);
      setAuditLogs(logs);
      if (detail.asset) {
        setFulfillAssetId(detail.asset);
      }
      if (detail.status === "APPROVED") {
        const assets = await assetService.list({
          status: "AVAILABLE",
          category: detail.category ?? "",
          page: 1,
        });
        // Include the locked REQUESTED asset if present
        setAvailableAssets(assets.results);
      }
    } catch {
      setError("Request not found or access denied.");
      setRequest(null);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  const runAction = async (action: () => Promise<AssetRequest>) => {
    setBusy(true);
    setError(null);
    try {
      const updated = await action();
      setRequest(updated);
      setAuditLogs(await approvalService.auditLogs(updated.id));
      setComments("");
    } catch (err) {
      if (isAxiosError(err) && err.response?.data) {
        const data = err.response.data as { detail?: string };
        setError(data.detail ?? JSON.stringify(err.response.data));
      } else {
        setError("Action failed.");
      }
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading request…</p>;
  }

  if (!request) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-destructive">{error ?? "Not found"}</p>
        <Button asChild variant="outline">
          <Link to="/approvals">Back</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link to="/approvals" className="text-sm text-muted-foreground hover:text-foreground">
            ← Back to approvals
          </Link>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight font-mono">
              {request.request_number}
            </h1>
            <Badge>{request.status}</Badge>
            <Badge variant="secondary">{request.priority}</Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            {request.requested_by_email} · {request.department_name}
          </p>
        </div>
      </div>

      {error && (
        <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2 space-y-0">
          <CardHeader>
            <CardTitle className="text-base">Request</CardTitle>
            <CardDescription>Details and workflow actions.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <dl className="grid gap-3 sm:grid-cols-2 text-sm">
              <div>
                <dt className="text-xs uppercase text-muted-foreground">Category</dt>
                <dd>{request.category_name ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-xs uppercase text-muted-foreground">Asset</dt>
                <dd>
                  {request.asset_tag
                    ? `${request.asset_tag} — ${request.asset_name ?? ""}`
                    : "Not selected yet"}
                </dd>
              </div>
            </dl>
            <div className="rounded-md border bg-muted/30 p-3 text-sm whitespace-pre-wrap">
              {request.justification}
            </div>

            {isManager && request.status === "PENDING" && (
              <div className="space-y-3 rounded-lg border p-4">
                <Label htmlFor="comments">Decision comments</Label>
                <Textarea
                  id="comments"
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  placeholder="Optional notes for the requester / IT"
                />
                <div className="flex flex-wrap gap-2">
                  <Button
                    disabled={busy}
                    onClick={() =>
                      void runAction(() => approvalService.approve(request.id, comments))
                    }
                  >
                    Approve &amp; assign
                  </Button>
                  <Button
                    variant="destructive"
                    disabled={busy}
                    onClick={() =>
                      void runAction(() => approvalService.reject(request.id, comments))
                    }
                  >
                    Reject
                  </Button>
                </div>
              </div>
            )}

            {isIT && request.status === "APPROVED" && (
              <div className="space-y-3 rounded-lg border p-4">
                <Label htmlFor="fulfill-asset">Allocate asset</Label>
                {request.asset ? (
                  <p className="text-sm text-muted-foreground">
                    Locked to {request.asset_tag}. Confirm allocation below.
                  </p>
                ) : (
                  <select
                    id="fulfill-asset"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                    value={fulfillAssetId}
                    onChange={(e) =>
                      setFulfillAssetId(e.target.value ? Number(e.target.value) : "")
                    }
                  >
                    <option value="">Select available asset</option>
                    {availableAssets.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.asset_tag} — {a.name}
                      </option>
                    ))}
                  </select>
                )}
                <Button
                  disabled={busy || (!request.asset && !fulfillAssetId)}
                  onClick={() =>
                    void runAction(() =>
                      approvalService.fulfill(request.id, {
                        asset_id: request.asset ?? Number(fulfillAssetId),
                      })
                    )
                  }
                >
                  Allocate & fulfill
                </Button>
              </div>
            )}

            {(isOwner || role === "ADMIN") &&
              (request.status === "PENDING" || request.status === "APPROVED") && (
                <Button
                  variant="outline"
                  disabled={busy}
                  onClick={() => {
                    if (!window.confirm("Cancel this request?")) return;
                    void runAction(() => approvalService.cancel(request.id));
                  }}
                >
                  Cancel request
                </Button>
              )}

            {request.status === "FULFILLED" && request.asset && (
              <Button asChild variant="secondary">
                <Link to={`/assets/${request.asset}`}>View allocated asset</Link>
              </Button>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Status timeline</CardTitle>
            <CardDescription>Workflow progress for this request.</CardDescription>
          </CardHeader>
          <CardContent>
            <RequestTimeline events={request.timeline} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Audit log</CardTitle>
          <CardDescription>Immutable trail for this request.</CardDescription>
        </CardHeader>
        <CardContent>
          {auditLogs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No entries yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b text-muted-foreground">
                  <tr>
                    <th className="py-2 pr-4 font-medium">When</th>
                    <th className="py-2 pr-4 font-medium">Action</th>
                    <th className="py-2 pr-4 font-medium">Actor</th>
                    <th className="py-2 font-medium">Changes</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((log) => (
                    <tr key={log.id} className="border-b last:border-0 align-top">
                      <td className="py-2 pr-4 whitespace-nowrap">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="py-2 pr-4 font-medium">{log.action}</td>
                      <td className="py-2 pr-4">{log.actor_email ?? "system"}</td>
                      <td className="py-2">
                        <pre className="max-w-xl overflow-x-auto rounded bg-muted/40 p-2 text-xs">
                          {JSON.stringify(log.changes, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
