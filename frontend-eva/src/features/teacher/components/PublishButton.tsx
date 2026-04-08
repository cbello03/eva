"use client";

import { useState } from "react";
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Typography,
} from "@mui/material";
import PublishIcon from "@mui/icons-material/Publish";
import { apiClient } from "@/lib/api-client";
import type { AxiosError } from "axios";

interface PublishButtonProps {
  courseId: number;
  status: "draft" | "published";
  onPublished?: () => void;
}

export default function PublishButton({
  courseId,
  status,
  onPublished,
}: PublishButtonProps) {
  const [open, setOpen] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePublish = async () => {
    setPublishing(true);
    setError(null);
    try {
      await apiClient.post(`/courses/${courseId}/publish`);
      setOpen(false);
      onPublished?.();
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail?: string }>;
      setError(
        axiosErr.response?.data?.detail ??
          "Failed to publish course. Ensure all lessons have at least one exercise.",
      );
    } finally {
      setPublishing(false);
    }
  };

  if (status === "published") {
    return (
      <Button variant="outlined" disabled startIcon={<PublishIcon />}>
        Published
      </Button>
    );
  }

  return (
    <>
      <Button
        variant="contained"
        color="success"
        startIcon={<PublishIcon />}
        onClick={() => setOpen(true)}
      >
        Publish Course
      </Button>

      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Publish Course</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            Publishing will make this course visible to all students. Ensure
            every lesson has at least one exercise.
          </Typography>
          {error && <Alert severity="error">{error}</Alert>}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="success"
            onClick={handlePublish}
            disabled={publishing}
          >
            {publishing ? "Publishing…" : "Confirm Publish"}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
