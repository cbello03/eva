"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Grid,
} from "@mui/material";
import { useAuthStore } from "@/features/auth/store";
import { WebSocketManager } from "@/lib/websocket";
import { useCollabGroup, useSubmitGroupWork } from "../hooks";
import GroupMembers from "./GroupMembers";
import GroupSubmitForm from "./GroupSubmitForm";

interface CollabWorkspaceProps {
  exerciseId: number;
  groupId: number;
}

export default function CollabWorkspace({
  exerciseId,
  groupId,
}: CollabWorkspaceProps) {
  const { data: group, isLoading, error } = useCollabGroup(groupId);
  const submitMutation = useSubmitGroupWork(groupId);
  const [wsStatus, setWsStatus] = useState<string>("disconnected");
  const [updates, setUpdates] = useState<string[]>([]);
  const wsRef = useRef<WebSocketManager | null>(null);
  const { accessToken, isAuthenticated } = useAuthStore();

  const handleWsMessage = useCallback((data: unknown) => {
    const msg = data as { type?: string; content?: string };
    if (msg.type === "workspace_update" && msg.content) {
      setUpdates((prev) => [...prev.slice(-49), msg.content!]);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated || !accessToken || groupId <= 0) return;

    const ws = new WebSocketManager(
      `/ws/collab/${exerciseId}/${groupId}/`,
      () => useAuthStore.getState().accessToken,
    );

    ws.onStatusChange(setWsStatus);
    ws.onMessage(handleWsMessage);
    ws.connect();
    wsRef.current = ws;

    return () => {
      ws.disconnect();
      wsRef.current = null;
    };
  }, [isAuthenticated, accessToken, exerciseId, groupId, handleWsMessage]);

  if (isLoading) {
    return (
      <Box sx={{ textAlign: "center", py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !group) {
    return <Alert severity="error">Failed to load group workspace.</Alert>;
  }

  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 12, md: 4 }}>
        <GroupMembers members={group.members} />
        <Typography variant="caption" color={wsStatus === "connected" ? "success.main" : "text.disabled"} sx={{ mt: 1, display: "block" }}>
          Workspace: {wsStatus}
        </Typography>
      </Grid>

      <Grid size={{ xs: 12, md: 8 }}>
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Workspace Activity
          </Typography>
          <Box
            sx={{
              maxHeight: 200,
              overflow: "auto",
              bgcolor: "grey.50",
              borderRadius: 1,
              p: 1,
            }}
          >
            {updates.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No activity yet. Collaborate with your group!
              </Typography>
            ) : (
              updates.map((update, i) => (
                <Typography key={i} variant="body2" sx={{ mb: 0.5 }}>
                  {update}
                </Typography>
              ))
            )}
          </Box>
        </Paper>

        <GroupSubmitForm
          onSubmit={(data) => submitMutation.mutate(data)}
          isPending={submitMutation.isPending}
          isSuccess={submitMutation.isSuccess}
        />
      </Grid>
    </Grid>
  );
}
