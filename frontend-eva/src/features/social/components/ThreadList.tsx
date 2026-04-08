"use client";

import Link from "next/link";
import {
  List,
  ListItemButton,
  ListItemText,
  Typography,
  Chip,
  Box,
  Button,
  CircularProgress,
} from "@mui/material";
import { Forum as ForumIcon } from "@mui/icons-material";
import type { ForumThread } from "../api";

interface ThreadListProps {
  threads: ForumThread[];
  courseId: number;
  hasNextPage?: boolean;
  onLoadMore?: () => void;
  isLoadingMore?: boolean;
}

export default function ThreadList({
  threads,
  courseId,
  hasNextPage,
  onLoadMore,
  isLoadingMore,
}: ThreadListProps) {
  if (threads.length === 0) {
    return (
      <Box sx={{ textAlign: "center", py: 4 }}>
        <ForumIcon sx={{ fontSize: 48, color: "text.disabled", mb: 1 }} />
        <Typography color="text.secondary">
          No threads yet. Start a discussion!
        </Typography>
      </Box>
    );
  }

  return (
    <>
      <List disablePadding>
        {threads.map((thread) => (
          <ListItemButton
            key={thread.id}
            component={Link}
            href={`/courses/${courseId}/forum?thread=${thread.id}`}
            sx={{ borderBottom: 1, borderColor: "divider" }}
          >
            <ListItemText
              primary={thread.title}
              secondary={`by ${thread.author.display_name} · ${new Date(thread.last_activity_at).toLocaleDateString()}`}
            />
            <Chip label={`${thread.reply_count} replies`} size="small" variant="outlined" />
          </ListItemButton>
        ))}
      </List>
      {hasNextPage && (
        <Box sx={{ textAlign: "center", py: 2 }}>
          <Button onClick={onLoadMore} disabled={isLoadingMore}>
            {isLoadingMore ? <CircularProgress size={20} /> : "Load more"}
          </Button>
        </Box>
      )}
    </>
  );
}
