import { apiClient } from "@/services/api";
import type { AuthTokens, LoginCredentials, User } from "@/types";

export interface ManagedUser {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_staff: boolean;
  has_employee_profile: boolean;
  date_joined: string;
}

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
    results: ManagedUser[];
  }> {
    const { data } = await apiClient.get("/auth/users/", {
      params: params.without_employee ? { without_employee: true } : undefined,
    });
    return data;
  },

  async createUser(payload: {
    email: string;
    password: string;
    first_name?: string;
    last_name?: string;
    role?: string;
    is_active?: boolean;
  }): Promise<ManagedUser> {
    const { data } = await apiClient.post<ManagedUser>("/auth/users/", payload);
    return data;
  },
};
