import type { AssetCategory, AssetListParams, AssetStatus, Vendor } from "@/types/assets";
import { ASSET_STATUSES } from "@/types/assets";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface AssetFiltersProps {
  value: AssetListParams;
  categories: AssetCategory[];
  vendors: Vendor[];
  onChange: (next: AssetListParams) => void;
}

export function AssetFilters({
  value,
  categories,
  vendors,
  onChange,
}: AssetFiltersProps) {
  return (
    <div className="grid gap-4 rounded-lg border p-4 md:grid-cols-4">
      <div className="space-y-2 md:col-span-2">
        <Label htmlFor="asset-search">Search</Label>
        <Input
          id="asset-search"
          placeholder="Tag, name, serial, brand…"
          value={value.search ?? ""}
          onChange={(e) => onChange({ ...value, search: e.target.value, page: 1 })}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="asset-status">Status</Label>
        <select
          id="asset-status"
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
          value={value.status ?? ""}
          onChange={(e) =>
            onChange({
              ...value,
              status: e.target.value as AssetStatus | "",
              page: 1,
            })
          }
        >
          <option value="">All statuses</option>
          {ASSET_STATUSES.map((status) => (
            <option key={status} value={status}>
              {status.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </div>
      <div className="space-y-2">
        <Label htmlFor="asset-category">Category</Label>
        <select
          id="asset-category"
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
          value={value.category ?? ""}
          onChange={(e) =>
            onChange({
              ...value,
              category: e.target.value ? Number(e.target.value) : "",
              page: 1,
            })
          }
        >
          <option value="">All categories</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>
      </div>
      <div className="space-y-2 md:col-span-2">
        <Label htmlFor="asset-vendor">Vendor</Label>
        <select
          id="asset-vendor"
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
          value={value.vendor ?? ""}
          onChange={(e) =>
            onChange({
              ...value,
              vendor: e.target.value ? Number(e.target.value) : "",
              page: 1,
            })
          }
        >
          <option value="">All vendors</option>
          {vendors.map((vendor) => (
            <option key={vendor.id} value={vendor.id}>
              {vendor.name}
            </option>
          ))}
        </select>
      </div>
      <div className="space-y-2 md:col-span-2">
        <Label htmlFor="asset-ordering">Sort</Label>
        <select
          id="asset-ordering"
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 text-sm"
          value={value.ordering ?? "-created_at"}
          onChange={(e) => onChange({ ...value, ordering: e.target.value, page: 1 })}
        >
          <option value="-created_at">Newest first</option>
          <option value="created_at">Oldest first</option>
          <option value="asset_tag">Tag A–Z</option>
          <option value="name">Name A–Z</option>
          <option value="status">Status</option>
          <option value="-purchase_cost">Cost high–low</option>
        </select>
      </div>
    </div>
  );
}
