"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Box, TextField, IconButton, Typography, CircularProgress } from "@mui/material";
import { Send as SendIcon } from "@mui/icons-material";
import { useAuthStore } from "@/features/auth/store";
import { WebSocketManager } from "@/lib/websocket";
import type { ChatMessage as ChatMessageType } from "../api";
import ChatMessage from "./ChatMessage";

interface ChatRoomProps {
  courseId: number;
}

export default function ChatRoom({ courseId }: ChatRoomProps) {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<string>("disconnected");
  const wsRef = useRef<WebSocketManager | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { accessToken, isAuthenticated } = useAuthStore();

  const currentUserId = useAuthStore((s) => s.user?.id);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    if (!isAuthenticated || !accessToken || courseId <= 0) return;

    const ws = new WebSocketManager(
      `/ws/chat/${courseId}/`,
      () => useAuthStore.getState().accessToken,
    );

    ws.onStatusChange(setStatus);

    ws.onMessage((data) => {
      const msg = data as {
        type?: string;
        message?: ChatMessageType;
        messages?: ChatMessageType[];
      };

      if (msg.type === "history" && msg.messages) {
        setMessages(msg.messages);
      } else if (msg.type === "message" && msg.message) {
        setMessages((prev) => [...prev, msg.message!]);
      }
    });

    ws.connect();
    wsRef.current = ws;

    return () => {
      ws.disconnect();
      wsRef.current = null;
    };
  }, [isAuthenticated, accessToken, courseId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !wsRef.current) return;
    wsRef.current.send({ type: "message", content: input.trim() });
    setInput("");
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "70vh" }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
        <Typography variant="subtitle2" color="text.secondary">
          Chat
        </Typography>
        <Typography variant="caption" color={status === "connected" ? "success.main" : "text.disabled"}>
          {status}
        </Typography>
      </Box>

      <Box
        sx={{
          flex: 1,
          overflow: "auto",
          border: 1,
          borderColor: "divider",
          borderRadius: 1,
          p: 2,
        }}
      >
        {status === "connecting" && (
          <Box sx={{ textAlign: "center", py: 4 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        {messages.map((msg) => (
          <ChatMessage
            key={msg.id}
            message={msg}
            isOwn={msg.author.id === currentUserId}
          />
        ))}
        <div ref={messagesEndRef} />
      </Box>

      <Box component="form" onSubmit={handleSend} sx={{ display: "flex", gap: 1, mt: 1 }}>
        <TextField
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Escribe un mensaje…"
          size="small"
          fullWidth
          disabled={status !== "connected"}
        />
        <IconButton
          type="submit"
          color="primary"
          disabled={!input.trim() || status !== "connected"}
        >
          <SendIcon />
        </IconButton>
      </Box>
    </Box>
  );
}
