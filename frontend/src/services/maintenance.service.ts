import { apiClient } from "@/services/api";
import type { PaginatedResponse } from "@/types/assets";

export interface MaintenanceTicket {
  id: number;
  asset: number;
  asset_tag: string;
  asset_name?: string;
  reported_by: number;
  reported_by_code: string;
  assigned_to: number | null;
  assigned_to_email: string | null;
  title: string;
  issue_description: string;
  status:
    | "PENDING_APPROVAL"
    | "OPEN"
    | "IN_PROGRESS"
    | "COMPLETED"
    | "CANCELLED"
    | "REJECTED";
  approval_comments?: string;
  cost: string | null;
  started_at: string | null;
  completed_at: string | null;
  resolution_notes: string;
  created_at: string;
}

export const maintenanceService = {
  async list(
    params: Record<string, string | number> = {}
  ): Promise<PaginatedResponse<MaintenanceTicket>> {
    const { data } = await apiClient.get("/maintenance/tickets/", { params });
    return data;
  },
  async create(payload: {
    asset: number;
    title: string;
    issue_description: string;
  }): Promise<MaintenanceTicket> {
    const { data } = await apiClient.post("/maintenance/tickets/", payload);
    return data;
  },
  async approve(id: number, comments = ""): Promise<MaintenanceTicket> {
    const { data } = await apiClient.post(`/maintenance/tickets/${id}/approve/`, {
      comments,
    });
    return data;
  },
  async reject(id: number, comments = ""): Promise<MaintenanceTicket> {
    const { data } = await apiClient.post(`/maintenance/tickets/${id}/reject/`, {
      comments,
    });
    return data;
  },
  async complete(id: number, resolution_notes = ""): Promise<MaintenanceTicket> {
    const { data } = await apiClient.post(`/maintenance/tickets/${id}/complete/`, {
      resolution_notes,
    });
    return data;
  },
  async start(id: number): Promise<MaintenanceTicket> {
    const { data } = await apiClient.post(`/maintenance/tickets/${id}/start/`);
    return data;
  },
};
