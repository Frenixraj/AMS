import { apiClient } from "@/services/api";
import type {
  Asset,
  AssetAuditLog,
  AssetCategory,
  AssetListItem,
  AssetListParams,
  PaginatedResponse,
  Vendor,
} from "@/types/assets";

function toQuery(params: AssetListParams): Record<string, string | number> {
  const query: Record<string, string | number> = {};
  if (params.page) query.page = params.page;
  if (params.search) query.search = params.search;
  if (params.status) query.status = params.status;
  if (params.category) query.category = params.category;
  if (params.vendor) query.vendor = params.vendor;
  if (params.ordering) query.ordering = params.ordering;
  return query;
}

export const assetService = {
  async list(params: AssetListParams = {}): Promise<PaginatedResponse<AssetListItem>> {
    const { data } = await apiClient.get<PaginatedResponse<AssetListItem>>("/assets/", {
      params: toQuery(params),
    });
    return data;
  },

  async get(id: number): Promise<Asset> {
    const { data } = await apiClient.get<Asset>(`/assets/${id}/`);
    return data;
  },

  async getByTag(assetTag: string): Promise<Asset> {
    const { data } = await apiClient.get<Asset>(
      `/assets/by-tag/${encodeURIComponent(assetTag)}/`
    );
    return data;
  },

  async create(formData: FormData): Promise<Asset> {
    const { data } = await apiClient.post<Asset>("/assets/", formData);
    return data;
  },

  async update(id: number, formData: FormData): Promise<Asset> {
    const { data } = await apiClient.patch<Asset>(`/assets/${id}/`, formData);
    return data;
  },

  async remove(id: number): Promise<void> {
    await apiClient.delete(`/assets/${id}/`);
  },

  async regenerateQr(id: number): Promise<Asset> {
    const { data } = await apiClient.post<Asset>(`/assets/${id}/regenerate-qr/`);
    return data;
  },

  async auditLogs(id: number): Promise<AssetAuditLog[]> {
    const { data } = await apiClient.get<AssetAuditLog[]>(`/assets/${id}/audit-logs/`);
    return data;
  },

  async listCategories(): Promise<PaginatedResponse<AssetCategory>> {
    const { data } = await apiClient.get<PaginatedResponse<AssetCategory>>(
      "/assets/categories/",
      { params: { page_size: 100, is_active: true } }
    );
    return data;
  },

  async listVendors(): Promise<PaginatedResponse<Vendor>> {
    const { data } = await apiClient.get<PaginatedResponse<Vendor>>("/assets/vendors/", {
      params: { page_size: 100, is_active: true },
    });
    return data;
  },

  async createCategory(payload: {
    name: string;
    code: string;
    description?: string;
  }): Promise<AssetCategory> {
    const { data } = await apiClient.post<AssetCategory>("/assets/categories/", payload);
    return data;
  },

  async createVendor(payload: {
    name: string;
    contact_person?: string;
    email?: string;
    phone?: string;
    address?: string;
  }): Promise<Vendor> {
    const { data } = await apiClient.post<Vendor>("/assets/vendors/", payload);
    return data;
  },
};
