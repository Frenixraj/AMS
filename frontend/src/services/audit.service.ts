import { apiClient } from "@/services/api";
import type { PaginatedResponse } from "@/types/assets";

export interface AuditLogEntry {
  id: number;
  actor: number | null;
  actor_email: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  changes: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

export const auditService = {
  async list(
    params: Record<string, string | number> = {}
  ): Promise<PaginatedResponse<AuditLogEntry>> {
    const { data } = await apiClient.get<PaginatedResponse<AuditLogEntry>>("/audit-logs/", {
      params,
    });
    return data;
  },
};
