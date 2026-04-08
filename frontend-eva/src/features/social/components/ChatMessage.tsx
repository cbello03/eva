"use client";

import { Box, Typography } from "@mui/material";
import type { ChatMessage as ChatMessageType } from "../api";

interface ChatMessageProps {
  message: ChatMessageType;
  isOwn: boolean;
}

export default function ChatMessage({ message, isOwn }: ChatMessageProps) {
  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: isOwn ? "flex-end" : "flex-start",
        mb: 1,
      }}
    >
      <Box
        sx={{
          maxWidth: "70%",
          px: 2,
          py: 1,
          borderRadius: 2,
          bgcolor: isOwn ? "primary.main" : "grey.100",
          color: isOwn ? "primary.contrastText" : "text.primary",
        }}
      >
        {!isOwn && (
          <Typography variant="caption" sx={{ fontWeight: 600 }}>
            {message.author.display_name}
          </Typography>
        )}
        <Typography variant="body2">{message.content}</Typography>
        <Typography
          variant="caption"
          sx={{ opacity: 0.7, display: "block", textAlign: "right" }}
        >
          {new Date(message.sent_at).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </Typography>
      </Box>
    </Box>
  );
}
