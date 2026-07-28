export type AssetStatus =
  | "AVAILABLE"
  | "REQUESTED"
  | "ALLOCATED"
  | "MAINTENANCE"
  | "RETIRED"
  | "LOST";

export const ASSET_STATUSES: AssetStatus[] = [
  "AVAILABLE",
  "REQUESTED",
  "ALLOCATED",
  "MAINTENANCE",
  "RETIRED",
  "LOST",
];

export interface AssetCategory {
  id: number;
  name: string;
  code: string;
  description: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Vendor {
  id: number;
  name: string;
  contact_person: string;
  email: string;
  phone: string;
  address: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AssetListItem {
  id: number;
  asset_tag: string;
  name: string;
  category: number;
  category_name: string;
  brand: string;
  model: string;
  serial_number: string;
  status: AssetStatus;
  vendor: number | null;
  vendor_name: string | null;
  purchase_date: string | null;
  purchase_cost: string | null;
  warranty_expiry: string | null;
  image_url: string | null;
  qr_code_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface Asset extends AssetListItem {
  category_detail: AssetCategory;
  vendor_detail: Vendor | null;
  notes: string;
  created_by: number | null;
  created_by_email: string | null;
  qr_payload: string;
  image?: string | null;
  qr_code?: string | null;
}

export interface AssetFormValues {
  asset_tag: string;
  name: string;
  category: number | "";
  brand: string;
  model: string;
  serial_number: string;
  purchase_date: string;
  purchase_cost: string;
  vendor: number | "";
  warranty_expiry: string;
  status: AssetStatus;
  notes: string;
  image?: FileList;
}

export interface AssetListParams {
  page?: number;
  search?: string;
  status?: AssetStatus | "";
  category?: number | "";
  vendor?: number | "";
  ordering?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface AssetAuditLog {
  id: number;
  action: string;
  actor_email: string | null;
  changes: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}
