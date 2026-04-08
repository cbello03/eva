"use client";

import {
  List,
  Box,
  Button,
  Typography,
  Divider,
  CircularProgress,
} from "@mui/material";
import {
  useNotifications,
  useMarkRead,
  useMarkAllRead,
} from "@/features/notifications/hooks";
import NotificationItem from "@/features/notifications/components/NotificationItem";

export default function NotificationList() {
  const { data, isLoading, hasNextPage, fetchNextPage, isFetchingNextPage } =
    useNotifications();
  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();

  const notifications = data?.pages.flatMap((page) => page.results) ?? [];

  const handleRead = (id: number) => {
    markRead.mutate(id);
  };

  const handleMarkAllRead = () => {
    markAllRead.mutate();
  };

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", p: 3 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (notifications.length === 0) {
    return (
      <Box sx={{ p: 3, textAlign: "center" }}>
        <Typography variant="body2" color="text.secondary">
          Aún no hay notificaciones
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          px: 2,
          py: 1,
        }}
      >
        <Typography variant="subtitle2">Notificaciones</Typography>
        <Button
          size="small"
          onClick={handleMarkAllRead}
          disabled={markAllRead.isPending}
        >
          Marcar todo como leído
        </Button>
      </Box>
      <Divider />
      <List disablePadding sx={{ maxHeight: 400, overflow: "auto" }}>
        {notifications.map((notification) => (
          <NotificationItem
            key={notification.id}
            notification={notification}
            onRead={handleRead}
          />
        ))}
        {hasNextPage && (
          <Box sx={{ display: "flex", justifyContent: "center", py: 1 }}>
            <Button
              size="small"
              onClick={() => fetchNextPage()}
              disabled={isFetchingNextPage}
            >
              {isFetchingNextPage ? "Cargando..." : "Cargar más"}
            </Button>
          </Box>
        )}
      </List>
    </Box>
  );
}
