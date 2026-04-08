"use client";

import { useEffect, useRef, useCallback } from "react";
import {
  useQuery,
  useMutation,
  useQueryClient,
  useInfiniteQuery,
} from "@tanstack/react-query";
import { useAuthStore } from "@/features/auth/store";
import { WebSocketManager } from "@/lib/websocket";
import * as notificationsApi from "@/features/notifications/api";
import type {
  Notification,
  PaginatedNotifications,
} from "@/features/notifications/api";

// ── Query keys ───────────────────────────────────────────────────────

export const notificationKeys = {
  all: ["notifications"] as const,
  list: () => [...notificationKeys.all, "list"] as const,
  unreadCount: () => [...notificationKeys.all, "unread-count"] as const,
};

// ── useNotifications: paginated notification list ────────────────────

export function useNotifications(limit = 20) {
  return useInfiniteQuery({
    queryKey: notificationKeys.list(),
    queryFn: ({ pageParam = 0 }) =>
      notificationsApi.getNotifications(pageParam, limit),
    initialPageParam: 0,
    getNextPageParam: (lastPage: PaginatedNotifications) =>
      lastPage.next_offset ?? undefined,
  });
}

// ── useUnreadCount: unread notification count ────────────────────────

export function useUnreadCount() {
  return useQuery({
    queryKey: notificationKeys.unreadCount(),
    queryFn: notificationsApi.getUnreadCount,
    refetchInterval: 60_000, // poll every 60s as fallback
  });
}

// ── useMarkRead: mark a single notification as read ──────────────────

export function useMarkRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: notificationsApi.markRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.list() });
      queryClient.invalidateQueries({
        queryKey: notificationKeys.unreadCount(),
      });
    },
  });
}

// ── useMarkAllRead: mark all notifications as read ───────────────────

export function useMarkAllRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationKeys.list() });
      queryClient.invalidateQueries({
        queryKey: notificationKeys.unreadCount(),
      });
    },
  });
}

// ── useNotificationSocket: real-time WebSocket delivery ──────────────

export function useNotificationSocket() {
  const queryClient = useQueryClient();
  const { accessToken, isAuthenticated } = useAuthStore();
  const wsRef = useRef<WebSocketManager | null>(null);

  const handleMessage = useCallback(
    (data: unknown) => {
      const msg = data as { type?: string; notification?: Notification };
      if (msg.type !== "notification" || !msg.notification) return;

      // Prepend the new notification to the cached list
      queryClient.setQueryData<{
        pages: PaginatedNotifications[];
        pageParams: number[];
      }>(notificationKeys.list(), (old) => {
        if (!old) return old;
        const firstPage = old.pages[0];
        if (!firstPage) return old;
        return {
          ...old,
          pages: [
            {
              ...firstPage,
              count: firstPage.count + 1,
              results: [msg.notification!, ...firstPage.results],
            },
            ...old.pages.slice(1),
          ],
        };
      });

      // Increment unread count
      queryClient.setQueryData<{ count: number }>(
        notificationKeys.unreadCount(),
        (old) => ({ count: (old?.count ?? 0) + 1 }),
      );
    },
    [queryClient],
  );

  useEffect(() => {
    if (!isAuthenticated || !accessToken) {
      wsRef.current?.disconnect();
      wsRef.current = null;
      return;
    }

    const ws = new WebSocketManager(
      "/ws/notifications/",
      () => useAuthStore.getState().accessToken,
    );

    ws.onMessage(handleMessage);
    ws.connect();
    wsRef.current = ws;

    return () => {
      ws.disconnect();
      wsRef.current = null;
    };
  }, [isAuthenticated, accessToken, handleMessage]);
}
