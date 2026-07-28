import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { AssetQrPanel } from "@/components/assets/AssetQrPanel";
import { AssetStatusBadge } from "@/components/assets/AssetStatusBadge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";
import { assetService } from "@/services/asset.service";
import type { Asset, AssetAuditLog } from "@/types/assets";

function canManageAssets(role?: string): boolean {
  return role === "ADMIN" || role === "IT_TEAM";
}

export function AssetDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const manage = canManageAssets(user?.role);

  const [asset, setAsset] = useState<Asset | null>(null);
  const [auditLogs, setAuditLogs] = useState<AssetAuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [detail, logs] = await Promise.all([
        assetService.get(Number(id)),
        assetService.auditLogs(Number(id)),
      ]);
      setAsset(detail);
      setAuditLogs(logs);
    } catch {
      setError("Asset not found or you do not have access.");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleRegenerateQr = async () => {
    if (!asset) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await assetService.regenerateQr(asset.id);
      setAsset(updated);
      const logs = await assetService.auditLogs(asset.id);
      setAuditLogs(logs);
    } catch {
      setError("Failed to regenerate QR code.");
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!asset) return;
    if (!window.confirm(`Delete asset ${asset.asset_tag}?`)) return;
    setBusy(true);
    try {
      await assetService.remove(asset.id);
      navigate("/assets");
    } catch {
      setError("Delete failed.");
      setBusy(false);
    }
  };

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading asset…</p>;
  }

  if (!asset) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-destructive">{error ?? "Asset not found."}</p>
        <Button asChild variant="outline">
          <Link to="/assets">Back to assets</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link to="/assets" className="text-sm text-muted-foreground hover:text-foreground">
            ← Back to assets
          </Link>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">{asset.name}</h1>
            <AssetStatusBadge status={asset.status} />
          </div>
          <p className="font-mono text-sm text-muted-foreground">{asset.asset_tag}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to="/assets/scan">Scan QR</Link>
          </Button>
          {manage && (
            <>
              <Button asChild variant="secondary">
                <Link to={`/assets/${asset.id}/edit`}>Edit</Link>
              </Button>
              <Button variant="destructive" onClick={handleDelete} disabled={busy}>
                Delete
              </Button>
            </>
          )}
        </div>
      </div>

      {error && (
        <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Details</CardTitle>
            <CardDescription>Master data for this asset.</CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-3 sm:grid-cols-2">
              <Detail label="Category" value={asset.category_detail?.name} />
              <Detail label="Serial number" value={asset.serial_number} mono />
              <Detail label="Brand" value={asset.brand || "—"} />
              <Detail label="Model" value={asset.model || "—"} />
              <Detail label="Vendor" value={asset.vendor_detail?.name ?? "—"} />
              <Detail label="Purchase date" value={asset.purchase_date ?? "—"} />
              <Detail label="Purchase cost" value={asset.purchase_cost ?? "—"} />
              <Detail label="Warranty expiry" value={asset.warranty_expiry ?? "—"} />
              <Detail label="Created by" value={asset.created_by_email ?? "—"} />
              <Detail
                label="Created at"
                value={new Date(asset.created_at).toLocaleString()}
              />
            </dl>
            {asset.notes && (
              <div className="mt-4 rounded-md border bg-muted/30 p-3 text-sm">
                <p className="mb-1 font-medium">Notes</p>
                <p className="whitespace-pre-wrap text-muted-foreground">{asset.notes}</p>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Image</CardTitle>
            </CardHeader>
            <CardContent>
              {asset.image_url ? (
                <img
                  src={asset.image_url}
                  alt={asset.name}
                  className="max-h-56 w-full rounded-md border object-contain"
                />
              ) : (
                <p className="text-sm text-muted-foreground">No image uploaded.</p>
              )}
            </CardContent>
          </Card>

          <AssetQrPanel
            assetTag={asset.asset_tag}
            name={asset.name}
            serialNumber={asset.serial_number}
            qrPayload={asset.qr_payload}
            qrCodeUrl={asset.qr_code_url}
            canRegenerate={manage}
            regenerating={busy}
            onRegenerate={handleRegenerateQr}
          />
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Audit log</CardTitle>
          <CardDescription>Recent changes for this asset.</CardDescription>
        </CardHeader>
        <CardContent>
          {auditLogs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No audit entries yet.</p>
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
                      <td className="whitespace-nowrap py-2 pr-4">
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

function Detail({
  label,
  value,
  mono,
}: {
  label: string;
  value?: string | null;
  mono?: boolean;
}) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className={mono ? "font-mono text-sm" : "text-sm"}>{value ?? "—"}</dd>
    </div>
  );
}
