import { apiClient } from "@/services/api";
import type { AuthTokens, LoginCredentials, User } from "@/types";

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await apiClient.post<AuthTokens>("/auth/token/", credentials);
    return response.data;
  },

  async refreshToken(refresh: string): Promise<{ access: string }> {
    const response = await apiClient.post<{ access: string }>("/auth/token/refresh/", {
      refresh,
    });
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>("/auth/me/");
    return response.data;
  },

  async listUsers(params: { without_employee?: boolean } = {}): Promise<{
    count: number;
    results: Array<{
      id: number;
      email: string;
      first_name: string;
      last_name: string;
      role: string;
      full_name: string;
    }>;
  }> {
    const { data } = await apiClient.get("/auth/users/", {
      params: params.without_employee ? { without_employee: true } : undefined,
    });
    return data;
  },
};
