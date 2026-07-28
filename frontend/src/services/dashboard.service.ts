import { apiClient } from "@/services/api";
import type { DashboardSummary } from "@/types/dashboard";

export const dashboardService = {
  async getSummary(warrantyDays = 90): Promise<DashboardSummary> {
    const { data } = await apiClient.get<DashboardSummary>("/dashboard/summary/", {
      params: { warranty_days: warrantyDays },
    });
    return data;
  },
};
