import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { approvalService } from "@/services/approval.service";
import { assetService } from "@/services/asset.service";
import type { AssetListItem } from "@/types/assets";
import type { AssetRequest } from "@/types/approvals";

/**
 * Employee: browse unassigned assets and request ownership.
 */
export function YourRequestsPage() {
  const [available, setAvailable] = useState<AssetListItem[]>([]);
  const [myRequests, setMyRequests] = useState<AssetRequest[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [justification, setJustification] = useState<Record<number, string>>({});

  const load = useCallback(async () => {
    setError(null);
    try {
      const [assets, requests] = await Promise.all([
        assetService.list({ status: "AVAILABLE", page: 1, page_size: 100 } as never),
        approvalService.list({ page_size: 50 }),
      ]);
      // Force for_request via raw params if list doesn't support it
      setAvailable(assets.results);
      setMyRequests(requests.results);
    } catch {
      setError("Failed to load available assets or your requests.");
    }
  }, []);

  useEffect(() => {
    const loadWithFlag = async () => {
      setError(null);
      try {
        const { apiClient } = await import("@/services/api");
        const [assetsRes, requests] = await Promise.all([
          apiClient.get("/assets/", {
            params: { for_request: 1, status: "AVAILABLE", page_size: 100 },
          }),
          approvalService.list({ page_size: 50 }),
        ]);
        setAvailable(assetsRes.data.results ?? []);
        setMyRequests(requests.results);
      } catch {
        setError("Failed to load available assets or your requests.");
      }
    };
    void loadWithFlag();
  }, []);

  const requestAsset = async (asset: AssetListItem) => {
    const text = (justification[asset.id] || "").trim();
    if (text.length < 10) {
      setError("Please explain why you need this asset (at least 10 characters).");
      return;
    }
    setBusyId(asset.id);
    setError(null);
    try {
      await approvalService.create({
        asset: asset.id,
        category: asset.category,
        justification: text,
        priority: "MEDIUM",
      });
      setJustification((prev) => ({ ...prev, [asset.id]: "" }));
      // reload
      const { apiClient } = await import("@/services/api");
      const [assetsRes, requests] = await Promise.all([
        apiClient.get("/assets/", {
          params: { for_request: 1, status: "AVAILABLE", page_size: 100 },
        }),
        approvalService.list({ page_size: 50 }),
      ]);
      setAvailable(assetsRes.data.results ?? []);
      setMyRequests(requests.results);
    } catch {
      setError("Could not submit request (asset may no longer be available).");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Your requests</h1>
        <p className="text-sm text-muted-foreground">
          Browse unassigned assets and request ownership. Manager or Admin will approve — you will
          be notified when assigned.
        </p>
      </div>
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Available assets</CardTitle>
          <CardDescription>{available.length} unassigned</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {available.map((asset) => (
            <div key={asset.id} className="rounded-md border p-4 space-y-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-medium">{asset.name}</p>
                  <p className="font-mono text-xs text-muted-foreground">
                    {asset.asset_tag} · {asset.category_name}
                    {asset.vendor_name ? ` · ${asset.vendor_name}` : ""}
                  </p>
                </div>
                <Button asChild variant="outline" size="sm">
                  <Link to={`/assets/${asset.id}`}>Details</Link>
                </Button>
              </div>
              <div className="space-y-1">
                <Label htmlFor={`why-${asset.id}`}>Why do you need this?</Label>
                <Textarea
                  id={`why-${asset.id}`}
                  rows={2}
                  value={justification[asset.id] || ""}
                  onChange={(e) =>
                    setJustification((prev) => ({ ...prev, [asset.id]: e.target.value }))
                  }
                  placeholder="I need this for my daily work because…"
                />
              </div>
              <Button
                disabled={busyId === asset.id}
                onClick={() => void requestAsset(asset)}
              >
                {busyId === asset.id ? "Submitting…" : "Request this asset"}
              </Button>
            </div>
          ))}
          {available.length === 0 && (
            <p className="text-sm text-muted-foreground">No available assets right now.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">My request history</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            {myRequests.map((r) => (
              <li key={r.id} className="flex flex-wrap justify-between gap-2 border-b pb-2">
                <span>
                  <Link className="font-medium hover:underline" to={`/approvals/${r.id}`}>
                    {r.request_number}
                  </Link>{" "}
                  · {r.asset_tag ?? r.category_name ?? "Asset"} · {r.status}
                </span>
                <span className="text-xs text-muted-foreground">
                  {new Date(r.created_at).toLocaleString()}
                </span>
              </li>
            ))}
            {myRequests.length === 0 && (
              <li className="text-muted-foreground">No requests yet.</li>
            )}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
