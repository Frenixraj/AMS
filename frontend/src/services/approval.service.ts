import { apiClient } from "@/services/api";
import type {
  AssetRequest,
  AssetRequestCreatePayload,
  AssetRequestListItem,
  AssetRequestListParams,
} from "@/types/approvals";
import type { PaginatedResponse } from "@/types/assets";

function toQuery(params: AssetRequestListParams): Record<string, string | number> {
  const query: Record<string, string | number> = {};
  if (params.page) query.page = params.page;
  if (params.search) query.search = params.search;
  if (params.status) query.status = params.status;
  if (params.priority) query.priority = params.priority;
  if (params.ordering) query.ordering = params.ordering;
  return query;
}

export const approvalService = {
  async list(
    params: AssetRequestListParams = {}
  ): Promise<PaginatedResponse<AssetRequestListItem>> {
    const { data } = await apiClient.get<PaginatedResponse<AssetRequestListItem>>(
      "/approvals/requests/",
      { params: toQuery(params) }
    );
    return data;
  },

  async get(id: number): Promise<AssetRequest> {
    const { data } = await apiClient.get<AssetRequest>(`/approvals/requests/${id}/`);
    return data;
  },

  async create(payload: AssetRequestCreatePayload): Promise<AssetRequest> {
    const { data } = await apiClient.post<AssetRequest>("/approvals/requests/", payload);
    return data;
  },

  async approve(id: number, comments = ""): Promise<AssetRequest> {
    const { data } = await apiClient.post<AssetRequest>(
      `/approvals/requests/${id}/approve/`,
      { comments }
    );
    return data;
  },

  async reject(id: number, comments = ""): Promise<AssetRequest> {
    const { data } = await apiClient.post<AssetRequest>(
      `/approvals/requests/${id}/reject/`,
      { comments }
    );
    return data;
  },

  async cancel(id: number): Promise<AssetRequest> {
    const { data } = await apiClient.post<AssetRequest>(
      `/approvals/requests/${id}/cancel/`
    );
    return data;
  },

  async fulfill(
    id: number,
    payload: { asset_id?: number | null; notes?: string } = {}
  ): Promise<AssetRequest> {
    const { data } = await apiClient.post<AssetRequest>(
      `/approvals/requests/${id}/fulfill/`,
      payload
    );
    return data;
  },

  async auditLogs(id: number): Promise<
    Array<{
      id: number;
      action: string;
      actor_email: string | null;
      changes: Record<string, unknown>;
      created_at: string;
    }>
  > {
    const { data } = await apiClient.get(`/approvals/requests/${id}/audit-logs/`);
    return data;
  },
};
