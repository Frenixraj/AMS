import { apiClient } from "@/services/api";
import type { HealthCheckResponse } from "@/types";

export const healthService = {
  async checkApi(): Promise<HealthCheckResponse> {
    const response = await apiClient.get<HealthCheckResponse>("/health/");
    return response.data;
  },
};
