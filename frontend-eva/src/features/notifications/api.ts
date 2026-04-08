import { apiClient } from "@/lib/api-client";

// ── Types ────────────────────────────────────────────────────────────

export interface Notification {
  id: number;
  notification_type: string;
  title: string;
  body: string;
  data: Record<string, unknown>;
  channel: string;
  is_read: boolean;
  created_at: string;
}

export interface PaginatedNotifications {
  count: number;
  next_offset: number | null;
  results: Notification[];
}

export interface UnreadCount {
  count: number;
}

export interface MarkAllReadResponse {
  updated: number;
}

// ── API functions ────────────────────────────────────────────────────

export async function getNotifications(
  offset = 0,
  limit = 20,
): Promise<PaginatedNotifications> {
  const response = await apiClient.get<PaginatedNotifications>(
    "/notifications",
    { params: { offset, limit } },
  );
  return response.data;
}

export async function getUnreadCount(): Promise<UnreadCount> {
  const response = await apiClient.get<UnreadCount>(
    "/notifications/unread-count",
  );
  return response.data;
}

export async function markRead(notificationId: number): Promise<Notification> {
  const response = await apiClient.post<Notification>(
    `/notifications/${notificationId}/read`,
  );
  return response.data;
}

export async function markAllRead(): Promise<MarkAllReadResponse> {
  const response = await apiClient.post<MarkAllReadResponse>(
    "/notifications/read-all",
  );
  return response.data;
}
