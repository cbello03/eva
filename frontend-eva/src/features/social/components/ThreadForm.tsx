"use client";

import { useState } from "react";
import { Box, TextField, Button } from "@mui/material";

interface ThreadFormProps {
  onSubmit: (data: { title: string; body: string }) => void;
  isPending?: boolean;
}

export default function ThreadForm({ onSubmit, isPending }: ThreadFormProps) {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !body.trim()) return;
    onSubmit({ title: title.trim(), body: body.trim() });
    setTitle("");
    setBody("");
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <TextField
        label="Thread title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        required
        size="small"
        fullWidth
      />
      <TextField
        label="Body"
        value={body}
        onChange={(e) => setBody(e.target.value)}
        required
        multiline
        rows={4}
        size="small"
        fullWidth
      />
      <Button
        type="submit"
        variant="contained"
        disabled={isPending || !title.trim() || !body.trim()}
        sx={{ alignSelf: "flex-end" }}
      >
        {isPending ? "Posting…" : "Create Thread"}
      </Button>
    </Box>
  );
}
