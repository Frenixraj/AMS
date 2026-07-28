import { Link } from "react-router-dom";

import { AssetStatusBadge } from "@/components/assets/AssetStatusBadge";
import { Button } from "@/components/ui/button";
import type { AssetListItem } from "@/types/assets";

interface AssetTableProps {
  assets: AssetListItem[];
  canManage: boolean;
  onDelete?: (asset: AssetListItem) => void;
}

export function AssetTable({ assets, canManage, onDelete }: AssetTableProps) {
  if (assets.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-10 text-center text-sm text-muted-foreground">
        No assets match your filters.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="border-b bg-muted/40">
          <tr>
            <th className="px-4 py-3 font-medium">Tag</th>
            <th className="px-4 py-3 font-medium">Name</th>
            <th className="px-4 py-3 font-medium">Category</th>
            <th className="px-4 py-3 font-medium">Serial</th>
            <th className="px-4 py-3 font-medium">Status</th>
            <th className="px-4 py-3 font-medium">Vendor</th>
            <th className="px-4 py-3 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          {assets.map((asset) => (
            <tr key={asset.id} className="border-b last:border-0 hover:bg-muted/20">
              <td className="px-4 py-3 font-mono text-xs">{asset.asset_tag}</td>
              <td className="px-4 py-3">
                <div className="font-medium">{asset.name}</div>
                <div className="text-xs text-muted-foreground">
                  {[asset.brand, asset.model].filter(Boolean).join(" · ") || "—"}
                </div>
              </td>
              <td className="px-4 py-3">{asset.category_name}</td>
              <td className="px-4 py-3 font-mono text-xs">{asset.serial_number}</td>
              <td className="px-4 py-3">
                <AssetStatusBadge status={asset.status} />
              </td>
              <td className="px-4 py-3">{asset.vendor_name ?? "—"}</td>
              <td className="px-4 py-3">
                <div className="flex justify-end gap-2">
                  <Button asChild variant="outline" size="sm">
                    <Link to={`/assets/${asset.id}`}>View</Link>
                  </Button>
                  {canManage && (
                    <>
                      <Button asChild variant="secondary" size="sm">
                        <Link to={`/assets/${asset.id}/edit`}>Edit</Link>
                      </Button>
                      {onDelete && (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => onDelete(asset)}
                        >
                          Delete
                        </Button>
                      )}
                    </>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
