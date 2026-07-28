import { apiClient } from "@/services/api";
import type { PaginatedResponse } from "@/types/assets";

export interface Assignment {
  id: number;
  asset: number;
  asset_tag: string;
  asset_name: string;
  employee: number;
  employee_code: string;
  employee_email: string;
  status: string;
  assigned_at: string;
  returned_at: string | null;
  notes: string;
}

export const assignmentService = {
  async list(params: Record<string, string | number> = {}): Promise<PaginatedResponse<Assignment>> {
    const { data } = await apiClient.get("/assets/assignments/", { params });
    return data;
  },
  async assign(payload: {
    asset_id: number;
    employee_id: number;
    notes?: string;
  }): Promise<Assignment> {
    const { data } = await apiClient.post("/assets/assignments/assign/", payload);
    return data;
  },
  async returnAsset(id: number, notes = ""): Promise<Assignment> {
    const { data } = await apiClient.post(`/assets/assignments/${id}/return_asset/`, { notes });
    return data;
  },
};
