import { apiClient } from "@/services/api";
import type { PaginatedResponse } from "@/types/assets";

export interface AppNotification {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  is_read: boolean;
  link: string;
  entity_type: string;
  entity_id: string;
  created_at: string;
}

export const notificationService = {
  async list(params: Record<string, string | number | boolean> = {}): Promise<PaginatedResponse<AppNotification>> {
    const { data } = await apiClient.get("/notifications/", { params });
    return data;
  },
  async unreadCount(): Promise<number> {
    const { data } = await apiClient.get<{ unread_count: number }>("/notifications/unread_count/");
    return data.unread_count;
  },
  async markRead(id: number): Promise<AppNotification> {
    const { data } = await apiClient.post(`/notifications/${id}/mark_read/`);
    return data;
  },
  async markAllRead(): Promise<void> {
    await apiClient.post("/notifications/mark_all_read/");
  },
};
