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

  const normalizeMessage = (message: unknown): ChatMessageType | null => {
    if (!message || typeof message !== "object") return null;
    const raw = message as {
      id?: number;
      course_id?: number;
      author_id?: number;
      author_display_name?: string;
      content?: string;
      sent_at?: string;
    };
    if (
      typeof raw.id !== "number" ||
      typeof raw.course_id !== "number" ||
      typeof raw.author_id !== "number" ||
      typeof raw.author_display_name !== "string" ||
      typeof raw.content !== "string" ||
      typeof raw.sent_at !== "string"
    ) {
      return null;
    }
    return {
      id: raw.id,
      course_id: raw.course_id,
      author: {
        id: raw.author_id,
        display_name: raw.author_display_name,
      },
      content: raw.content,
      sent_at: raw.sent_at,
    };
  };

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
        setMessages(msg.messages.map(normalizeMessage).filter((m): m is ChatMessageType => Boolean(m)));
      } else if (msg.type === "message" && msg.message) {
        const normalized = normalizeMessage(msg.message);
        if (!normalized) return;
        setMessages((prev) => [...prev, normalized]);
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
