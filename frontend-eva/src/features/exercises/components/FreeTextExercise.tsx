"use client";

import { useState } from "react";
import { Box, Button, Paper, TextField, Typography } from "@mui/material";

interface FreeTextExerciseProps {
  questionText: string;
  disabled: boolean;
  onSubmit: (answer: Record<string, unknown>) => void;
}

export default function FreeTextExercise({
  questionText,
  disabled,
  onSubmit,
}: FreeTextExerciseProps) {
  const [value, setValue] = useState("");

  const handleSubmit = () => {
    if (!value.trim()) return;
    onSubmit({ text: value.trim() });
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        {questionText}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Write your answer below. This will be submitted for teacher review.
      </Typography>
      <TextField
        fullWidth
        multiline
        minRows={4}
        maxRows={10}
        placeholder="Type your answer…"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
        sx={{ mb: 2 }}
      />
      <Button
        variant="contained"
        onClick={handleSubmit}
        disabled={disabled || !value.trim()}
      >
        Submit for Review
      </Button>
    </Paper>
  );
}
