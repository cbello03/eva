"use client";

import { ListItemButton, ListItemText, Typography, Box } from "@mui/material";
import type { Notification } from "@/features/notifications/api";

interface NotificationItemProps {
  notification: Notification;
  onRead: (id: number) => void;
}

function formatRelativeTime(dateStr: string): string {
  const now = Date.now();
  const diff = now - new Date(dateStr).getTime();
  const seconds = Math.floor(diff / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function NotificationItem({
  notification,
  onRead,
}: NotificationItemProps) {
  const handleClick = () => {
    if (!notification.is_read) {
      onRead(notification.id);
    }
  };

  return (
    <ListItemButton
      onClick={handleClick}
      sx={{
        bgcolor: notification.is_read ? "transparent" : "action.hover",
        "&:hover": { bgcolor: "action.selected" },
      }}
    >
      <ListItemText
        primary={
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <Typography
              variant="body2"
              noWrap
              sx={{ flex: 1, mr: 1, fontWeight: notification.is_read ? 400 : 600 }}
            >
              {notification.title}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ flexShrink: 0 }}>
              {formatRelativeTime(notification.created_at)}
            </Typography>
          </Box>
        }
        secondary={
          <Typography variant="body2" color="text.secondary" noWrap>
            {notification.body}
          </Typography>
        }
      />
    </ListItemButton>
  );
}
