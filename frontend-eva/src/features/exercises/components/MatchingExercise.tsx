"use client";

import { useMemo, useState } from "react";
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Typography,
} from "@mui/material";
import type { MatchingConfig } from "../types";

interface MatchingExerciseProps {
  questionText: string;
  config: MatchingConfig;
  disabled: boolean;
  onSubmit: (answer: Record<string, unknown>) => void;
}

export default function MatchingExercise({
  questionText,
  config,
  disabled,
  onSubmit,
}: MatchingExerciseProps) {
  const [matches, setMatches] = useState<Record<string, string>>({});

  // Shuffle right-side options so they aren't in the same order as left
  const rightOptions = useMemo(
    () => [...config.pairs.map((p) => p.right)].sort(() => Math.random() - 0.5),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [config.pairs.map((p) => p.right).join(",")],
  );

  const handleChange = (left: string, right: string) => {
    setMatches((prev) => ({ ...prev, [left]: right }));
  };

  const allMatched = config.pairs.every((p) => matches[p.left]);

  const handleSubmit = () => {
    if (!allMatched) return;
    const pairs = config.pairs.map((p) => ({
      left: p.left,
      right: matches[p.left],
    }));
    onSubmit({ pairs });
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        {questionText}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Match each item on the left with the correct item on the right.
      </Typography>
      <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {config.pairs.map((pair) => (
          <Box
            key={pair.left}
            sx={{ display: "flex", alignItems: "center", gap: 2 }}
          >
            <Typography
              variant="body1"
              sx={{ minWidth: 120, fontWeight: 500 }}
            >
              {pair.left}
            </Typography>
            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel>Select match</InputLabel>
              <Select
                value={matches[pair.left] ?? ""}
                label="Select match"
                onChange={(e) => handleChange(pair.left, e.target.value)}
                disabled={disabled}
              >
                {rightOptions.map((opt) => (
                  <MenuItem key={opt} value={opt}>
                    {opt}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        ))}
      </Box>
      <Box sx={{ mt: 2 }}>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={disabled || !allMatched}
        >
          Submit Answer
        </Button>
      </Box>
    </Paper>
  );
}
