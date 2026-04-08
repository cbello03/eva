"use client";

import { useState } from "react";
import { Box, TextField, Button, Alert } from "@mui/material";

interface GroupSubmitFormProps {
  onSubmit: (data: { submitted_answer: Record<string, unknown> }) => void;
  isPending?: boolean;
  isSuccess?: boolean;
}

export default function GroupSubmitForm({
  onSubmit,
  isPending,
  isSuccess,
}: GroupSubmitFormProps) {
  const [answer, setAnswer] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim()) return;
    onSubmit({ submitted_answer: { text: answer.trim() } });
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {isSuccess && (
        <Alert severity="success">Group work submitted!</Alert>
      )}
      <TextField
        label="Group answer"
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        required
        multiline
        rows={4}
        fullWidth
      />
      <Button
        type="submit"
        variant="contained"
        disabled={isPending || !answer.trim()}
        sx={{ alignSelf: "flex-end" }}
      >
        {isPending ? "Submitting…" : "Submit Group Work"}
      </Button>
    </Box>
  );
}
