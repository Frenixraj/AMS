import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { auditService, type AuditLogEntry } from "@/services/audit.service";

export function AuditLogPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [entityType, setEntityType] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await auditService.list({
        page,
        page_size: 25,
        ...(search.trim() ? { search: search.trim() } : {}),
        ...(entityType.trim() ? { entity_type: entityType.trim() } : {}),
      });
      setLogs(data.results);
      setCount(data.count);
    } catch {
      setError("Failed to load audit logs. Admin or IT access required.");
    } finally {
      setLoading(false);
    }
  }, [page, search, entityType]);

  useEffect(() => {
    void load();
  }, [load]);

  const totalPages = Math.max(1, Math.ceil(count / 25));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Audit log</h1>
        <p className="text-sm text-muted-foreground">
          System-wide activity trail for assets, assignments, and approvals.
        </p>
      </div>
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Filters</CardTitle>
          <CardDescription>{count} matching events</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap items-end gap-3">
          <div className="space-y-1">
            <Label htmlFor="audit-search">Search</Label>
            <Input
              id="audit-search"
              placeholder="email, entity id…"
              value={search}
              onChange={(e) => {
                setPage(1);
                setSearch(e.target.value);
              }}
            />
          </div>
          <div className="space-y-1">
            <Label htmlFor="audit-entity">Entity type</Label>
            <Input
              id="audit-entity"
              placeholder="Asset, AssetRequest…"
              value={entityType}
              onChange={(e) => {
                setPage(1);
                setEntityType(e.target.value);
              }}
            />
          </div>
          <Button variant="outline" onClick={() => void load()}>
            Refresh
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="pt-6">
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <caption className="sr-only">Audit log entries</caption>
                <thead className="border-b text-muted-foreground">
                  <tr>
                    <th scope="col" className="py-2 pr-3">
                      When
                    </th>
                    <th scope="col" className="py-2 pr-3">
                      Actor
                    </th>
                    <th scope="col" className="py-2 pr-3">
                      Action
                    </th>
                    <th scope="col" className="py-2 pr-3">
                      Entity
                    </th>
                    <th scope="col" className="py-2">
                      Changes
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id} className="border-b last:border-0 align-top">
                      <td className="py-2 pr-3 whitespace-nowrap text-xs">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="py-2 pr-3 text-xs">{log.actor_email ?? "—"}</td>
                      <td className="py-2 pr-3 font-mono text-xs">{log.action}</td>
                      <td className="py-2 pr-3 text-xs">
                        {log.entity_type} #{log.entity_id}
                      </td>
                      <td className="py-2 max-w-xs truncate text-xs text-muted-foreground">
                        {Object.keys(log.changes || {}).length
                          ? JSON.stringify(log.changes)
                          : "—"}
                      </td>
                    </tr>
                  ))}
                  {logs.length === 0 && (
                    <tr>
                      <td colSpan={5} className="py-6 text-muted-foreground">
                        No audit events found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
          <div className="mt-4 flex items-center justify-between">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <span className="text-xs text-muted-foreground">
              Page {page} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
