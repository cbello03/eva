"use client";

import { useState } from "react";
import {
  Box,
  Button,
  FormControlLabel,
  Paper,
  Radio,
  RadioGroup,
  Typography,
} from "@mui/material";
import type { MultipleChoiceConfig } from "../types";

interface MultipleChoiceExerciseProps {
  questionText: string;
  config: MultipleChoiceConfig;
  disabled: boolean;
  onSubmit: (answer: Record<string, unknown>) => void;
}

export default function MultipleChoiceExercise({
  questionText,
  config,
  disabled,
  onSubmit,
}: MultipleChoiceExerciseProps) {
  const [selected, setSelected] = useState<string>("");

  const handleSubmit = () => {
    if (selected === "") return;
    onSubmit({ selected_index: Number(selected) });
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        {questionText}
      </Typography>
      <RadioGroup
        value={selected}
        onChange={(e) => setSelected(e.target.value)}
      >
        {config.options.map((option, index) => (
          <FormControlLabel
            key={index}
            value={String(index)}
            control={<Radio />}
            label={option}
            disabled={disabled}
            sx={{ mb: 0.5 }}
          />
        ))}
      </RadioGroup>
      <Box sx={{ mt: 2 }}>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={disabled || selected === ""}
        >
          Submit Answer
        </Button>
      </Box>
    </Paper>
  );
}
