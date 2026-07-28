import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAuth } from "@/hooks/useAuth";
import { assetService } from "@/services/asset.service";
import { maintenanceService, type MaintenanceTicket } from "@/services/maintenance.service";
import type { AssetListItem } from "@/types/assets";

export function MaintenancePage() {
  const { user } = useAuth();
  const isIT = user?.role === "IT_TEAM" || user?.role === "ADMIN";
  const canReport = Boolean(user?.employee_profile);
  const [tickets, setTickets] = useState<MaintenanceTicket[]>([]);
  const [assets, setAssets] = useState<AssetListItem[]>([]);
  const [form, setForm] = useState({ asset: "", title: "", issue_description: "" });
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [t, a] = await Promise.all([
        maintenanceService.list({ page_size: 50 }),
        assetService.list({ page: 1 }),
      ]);
      setTickets(t.results);
      setAssets(a.results);
    } catch {
      setError("Failed to load maintenance tickets.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const submit = async () => {
    if (!form.asset || !form.title || form.issue_description.length < 5) return;
    try {
      await maintenanceService.create({
        asset: Number(form.asset),
        title: form.title,
        issue_description: form.issue_description,
      });
      setForm({ asset: "", title: "", issue_description: "" });
      await load();
    } catch {
      setError("Could not create ticket.");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Maintenance</h1>
        <p className="text-sm text-muted-foreground">Report issues and track repairs.</p>
      </div>
      {error && <p className="text-sm text-destructive">{error}</p>}

      {canReport && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Report an issue</CardTitle>
            <CardDescription>Sets the asset status to Maintenance.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            <div className="space-y-1 md:col-span-2">
              <Label>Asset</Label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
                value={form.asset}
                onChange={(e) => setForm({ ...form, asset: e.target.value })}
              >
                <option value="">Select asset</option>
                {assets.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.asset_tag} — {a.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1 md:col-span-2">
              <Label>Title</Label>
              <Input
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
              />
            </div>
            <div className="space-y-1 md:col-span-2">
              <Label>Description</Label>
              <Textarea
                rows={3}
                value={form.issue_description}
                onChange={(e) => setForm({ ...form, issue_description: e.target.value })}
              />
            </div>
            <Button onClick={() => void submit()}>Submit ticket</Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Tickets</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {tickets.map((t) => (
            <div key={t.id} className="rounded-md border p-3 text-sm">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="font-medium">
                  {t.title}{" "}
                  <span className="font-mono text-xs text-muted-foreground">{t.asset_tag}</span>
                </div>
                <Badge variant="secondary">{t.status}</Badge>
              </div>
              <p className="mt-1 text-muted-foreground">{t.issue_description}</p>
              {isIT && (t.status === "OPEN" || t.status === "IN_PROGRESS") && (
                <div className="mt-2 flex gap-2">
                  {t.status === "OPEN" && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => void maintenanceService.start(t.id).then(load)}
                    >
                      Start
                    </Button>
                  )}
                  <Button
                    size="sm"
                    onClick={() => void maintenanceService.complete(t.id, "Resolved").then(load)}
                  >
                    Complete
                  </Button>
                </div>
              )}
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
