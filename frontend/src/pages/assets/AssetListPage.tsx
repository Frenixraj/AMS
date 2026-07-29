import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { AssetFilters } from "@/components/assets/AssetFilters";
import { AssetTable } from "@/components/assets/AssetTable";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";
import { assetService } from "@/services/asset.service";
import type {
  AssetCategory,
  AssetListItem,
  AssetListParams,
  Vendor,
} from "@/types/assets";

function canManageAssets(role?: string): boolean {
  return role === "ADMIN" || role === "ASSET_MANAGER" || role === "IT_TEAM";
}

export function AssetListPage() {
  const { user } = useAuth();
  const manage = canManageAssets(user?.role);

  const [params, setParams] = useState<AssetListParams>({
    page: 1,
    search: "",
    status: "",
    category: "",
    vendor: "",
    ordering: "-created_at",
  });
  const [assets, setAssets] = useState<AssetListItem[]>([]);
  const [count, setCount] = useState(0);
  const [categories, setCategories] = useState<AssetCategory[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const pageCount = useMemo(() => Math.max(1, Math.ceil(count / 20)), [count]);

  const loadLookups = useCallback(async () => {
    const [categoryPage, vendorPage] = await Promise.all([
      assetService.listCategories(),
      assetService.listVendors(),
    ]);
    setCategories(categoryPage.results);
    setVendors(vendorPage.results);
  }, []);

  const loadAssets = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await assetService.list(params);
      setAssets(data.results);
      setCount(data.count);
    } catch {
      setError("Failed to load assets. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    void loadLookups();
  }, [loadLookups]);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      void loadAssets();
    }, 250);
    return () => window.clearTimeout(handle);
  }, [loadAssets]);

  const handleDelete = async (asset: AssetListItem) => {
    if (!window.confirm(`Delete asset ${asset.asset_tag}? This cannot be undone.`)) {
      return;
    }
    try {
      await assetService.remove(asset.id);
      await loadAssets();
    } catch {
      setError("Delete failed. You may not have permission.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Assets</h1>
          <p className="text-sm text-muted-foreground">
            Inventory, QR codes, and lifecycle status.
          </p>
        </div>
        {!manage &&
        (user?.role === "EMPLOYEE" || user?.role === "MANAGER") ? null : manage ? (
          <div className="flex gap-2">
            <Button asChild variant="outline">
              <Link to="/assets/scan">Scan QR</Link>
            </Button>
            <Button asChild>
              <Link to="/assets/new">Add asset</Link>
            </Button>
          </div>
        ) : null}
      </div>

      <AssetFilters
        value={params}
        categories={categories}
        vendors={vendors}
        onChange={setParams}
      />

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle className="text-base">
              {user?.role === "EMPLOYEE" || user?.role === "MANAGER"
                ? "Your assets"
                : "Inventory"}
            </CardTitle>
            <CardDescription>
              {user?.role === "EMPLOYEE" || user?.role === "MANAGER"
                ? "Assets currently assigned to you"
                : `${count} asset${count === 1 ? "" : "s"} · page ${params.page ?? 1} of ${pageCount}`}
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <p className="rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading assets…</p>
          ) : (
            <AssetTable
              assets={assets}
              canManage={manage}
              onDelete={manage ? handleDelete : undefined}
            />
          )}
          <div className="flex items-center justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={(params.page ?? 1) <= 1 || loading}
              onClick={() => setParams((prev) => ({ ...prev, page: (prev.page ?? 1) - 1 }))}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={(params.page ?? 1) >= pageCount || loading}
              onClick={() => setParams((prev) => ({ ...prev, page: (prev.page ?? 1) + 1 }))}
            >
              Next
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
