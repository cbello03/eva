"use client";

import { useState } from "react";
import {
  Box,
  TextField,
  Button,
  Typography,
  Slider,
} from "@mui/material";
import type { RubricCriterion } from "../api";

interface ReviewFormProps {
  rubric: RubricCriterion[];
  onSubmit: (data: { scores: Record<string, number>; feedback: string }) => void;
  isPending?: boolean;
}

export default function ReviewForm({ rubric, onSubmit, isPending }: ReviewFormProps) {
  const [scores, setScores] = useState<Record<string, number>>(() =>
    Object.fromEntries(rubric.map((c) => [c.name, 0])),
  );
  const [feedback, setFeedback] = useState("");

  const handleScoreChange = (name: string, value: number) => {
    setScores((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!feedback.trim()) return;
    onSubmit({ scores, feedback: feedback.trim() });
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      {rubric.map((criterion) => (
        <Box key={criterion.name}>
          <Typography variant="subtitle2" gutterBottom>
            {criterion.name} (0–{criterion.max_score})
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {criterion.description}
          </Typography>
          <Slider
            value={scores[criterion.name] ?? 0}
            onChange={(_, v) => handleScoreChange(criterion.name, v as number)}
            min={0}
            max={criterion.max_score}
            step={1}
            marks
            valueLabelDisplay="auto"
          />
        </Box>
      ))}

      <TextField
        label="Feedback"
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        required
        multiline
        rows={4}
        fullWidth
      />

      <Button
        type="submit"
        variant="contained"
        disabled={isPending || !feedback.trim()}
        sx={{ alignSelf: "flex-end" }}
      >
        {isPending ? "Submitting…" : "Submit Review"}
      </Button>
    </Box>
  );
}
