"use client";

import { useState } from "react";
import { Box, TextField, Button } from "@mui/material";

interface ReplyFormProps {
  onSubmit: (data: { body: string }) => void;
  isPending?: boolean;
}

export default function ReplyForm({ onSubmit, isPending }: ReplyFormProps) {
  const [body, setBody] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!body.trim()) return;
    onSubmit({ body: body.trim() });
    setBody("");
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: "flex", gap: 2, mt: 2 }}>
      <TextField
        label="Escribe una respuesta…"
        value={body}
        onChange={(e) => setBody(e.target.value)}
        required
        multiline
        rows={2}
        size="small"
        fullWidth
      />
      <Button
        type="submit"
        variant="contained"
        disabled={isPending || !body.trim()}
        sx={{ alignSelf: "flex-end" }}
      >
        {isPending ? "Enviando…" : "Responder"}
      </Button>
    </Box>
  );
}
