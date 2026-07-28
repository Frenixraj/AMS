import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/hooks/useAuth";
import { assetService } from "@/services/asset.service";
import { maintenanceService } from "@/services/maintenance.service";
import type { AssetListItem } from "@/types/assets";
import { isAdmin, isAdminOrAssetManager, isManager } from "@/utils/roles";

type Ticket = Awaited<ReturnType<typeof maintenanceService.list>>["results"][number];

export function MaintenancePage() {
  const { user } = useAuth();
  const canOps = isAdminOrAssetManager(user);
  const canApprove = isAdmin(user) || isManager(user);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [ownedAssets, setOwnedAssets] = useState<AssetListItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ asset: "", title: "", issue_description: "" });

  const load = useCallback(async () => {
    setError(null);
    try {
      const [tix, assets] = await Promise.all([
        maintenanceService.list({ page_size: 50 }),
        assetService.list({ page: 1 }),
      ]);
      setTickets(tix.results);
      setOwnedAssets(assets.results);
    } catch {
      setError("Failed to load maintenance data.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const raiseTicket = async () => {
    if (!form.asset || !form.title.trim() || form.issue_description.trim().length < 5) {
      setError("Pick an owned asset and describe the issue.");
      return;
    }
    try {
      await maintenanceService.create({
        asset: Number(form.asset),
        title: form.title.trim(),
        issue_description: form.issue_description.trim(),
      });
      setForm({ asset: "", title: "", issue_description: "" });
      await load();
    } catch {
      setError("Could not raise maintenance ticket.");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Maintenance</h1>
        <p className="text-sm text-muted-foreground">
          Raise a service ticket for assets you own. Manager or Admin must approve before work
          starts.
        </p>
      </div>
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      {user?.employee_profile && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Raise maintenance ticket</CardTitle>
            <CardDescription>Only assets currently assigned to you</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="maint-asset">Your asset</Label>
              <select
                id="maint-asset"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                value={form.asset}
                onChange={(e) => setForm({ ...form, asset: e.target.value })}
              >
                <option value="">Select asset</option>
                {ownedAssets.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.asset_tag} — {a.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="maint-title">Title</Label>
              <Input
                id="maint-title"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
              />
            </div>
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="maint-issue">Issue</Label>
              <Textarea
                id="maint-issue"
                rows={3}
                value={form.issue_description}
                onChange={(e) => setForm({ ...form, issue_description: e.target.value })}
              />
            </div>
            <div>
              <Button onClick={() => void raiseTicket()}>Raise maintenance ticket</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Tickets</CardTitle>
          <CardDescription>{tickets.length} records</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {tickets.map((t) => (
            <div key={t.id} className="rounded-md border p-3 space-y-2">
              <div className="flex flex-wrap justify-between gap-2">
                <div>
                  <p className="font-medium">{t.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {t.asset_tag} · {t.status}
                    {t.reported_by_code ? ` · by ${t.reported_by_code}` : ""}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  {canApprove && t.status === "PENDING_APPROVAL" && (
                    <>
                      <Button
                        size="sm"
                        onClick={() =>
                          void maintenanceService.approve(t.id).then(() => load())
                        }
                      >
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          void maintenanceService.reject(t.id).then(() => load())
                        }
                      >
                        Reject
                      </Button>
                    </>
                  )}
                  {canOps && t.status === "OPEN" && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => void maintenanceService.start(t.id).then(() => load())}
                    >
                      Start
                    </Button>
                  )}
                  {canOps && (t.status === "OPEN" || t.status === "IN_PROGRESS") && (
                    <Button
                      size="sm"
                      onClick={() => void maintenanceService.complete(t.id).then(() => load())}
                    >
                      Complete
                    </Button>
                  )}
                </div>
              </div>
              <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                {t.issue_description}
              </p>
            </div>
          ))}
          {tickets.length === 0 && (
            <p className="text-sm text-muted-foreground">No tickets yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
