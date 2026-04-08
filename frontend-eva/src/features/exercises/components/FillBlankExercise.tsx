"use client";

import { useState } from "react";
import { Box, Button, Paper, TextField, Typography } from "@mui/material";

interface FillBlankExerciseProps {
  questionText: string;
  disabled: boolean;
  onSubmit: (answer: Record<string, unknown>) => void;
}

export default function FillBlankExercise({
  questionText,
  disabled,
  onSubmit,
}: FillBlankExerciseProps) {
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
        Fill in the blank:
      </Typography>
      <TextField
        fullWidth
        size="small"
        placeholder="Type your answer…"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={disabled}
        onKeyDown={(e) => {
          if (e.key === "Enter") handleSubmit();
        }}
        sx={{ mb: 2 }}
      />
      <Button
        variant="contained"
        onClick={handleSubmit}
        disabled={disabled || !value.trim()}
      >
        Submit Answer
      </Button>
    </Paper>
  );
}
