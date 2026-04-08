"use client";

import {
  Box,
  Typography,
  Paper,
  Divider,
  IconButton,
  Chip,
  Tooltip,
} from "@mui/material";
import {
  ThumbUp as ThumbUpIcon,
  ThumbUpOutlined as ThumbUpOutlinedIcon,
  Flag as FlagIcon,
} from "@mui/icons-material";
import type { ThreadDetail as ThreadDetailType, ForumReply } from "../api";

interface ThreadDetailProps {
  thread: ThreadDetailType;
  onUpvote: (replyId: number) => void;
  onFlag?: (postId: number) => void;
}

function ReplyItem({
  reply,
  onUpvote,
  onFlag,
}: {
  reply: ForumReply;
  onUpvote: (replyId: number) => void;
  onFlag?: (postId: number) => void;
}) {
  return (
    <Box sx={{ py: 2 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
        <Typography variant="subtitle2">
          {reply.author.display_name}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {new Date(reply.created_at).toLocaleString()}
        </Typography>
      </Box>
      <Typography variant="body2" sx={{ mb: 1 }}>
        {reply.body}
      </Typography>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <IconButton size="small" onClick={() => onUpvote(reply.id)}>
          {reply.has_upvoted ? (
            <ThumbUpIcon fontSize="small" color="primary" />
          ) : (
            <ThumbUpOutlinedIcon fontSize="small" />
          )}
        </IconButton>
        <Typography variant="caption">{reply.upvote_count}</Typography>
        {onFlag && (
          <Tooltip title="Reportar publicación">
            <IconButton size="small" onClick={() => onFlag(reply.id)}>
              <FlagIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </Box>
    </Box>
  );
}

export default function ThreadDetail({
  thread,
  onUpvote,
  onFlag,
}: ThreadDetailProps) {
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        {thread.title}
      </Typography>
      <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
        <Chip
          label={thread.author.display_name}
          size="small"
          variant="outlined"
        />
        <Typography variant="caption" color="text.secondary" sx={{ alignSelf: "center" }}>
          {new Date(thread.created_at).toLocaleString()}
        </Typography>
      </Box>
      <Typography variant="body1" sx={{ mb: 3 }}>
        {thread.body}
      </Typography>

      <Divider />

      <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>
        Respuestas ({thread.replies.length})
      </Typography>

      {thread.replies.length === 0 ? (
        <Typography variant="body2" color="text.secondary">
          Aún no hay respuestas.
        </Typography>
      ) : (
        thread.replies.map((reply) => (
          <Box key={reply.id}>
            <ReplyItem reply={reply} onUpvote={onUpvote} onFlag={onFlag} />
            <Divider />
          </Box>
        ))
      )}
    </Paper>
  );
}
