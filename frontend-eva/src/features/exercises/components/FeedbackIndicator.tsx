"use client";

import { Alert, Collapse, Typography } from "@mui/material";
import {
  CheckCircle as CorrectIcon,
  Cancel as IncorrectIcon,
} from "@mui/icons-material";
import type { AnswerResult } from "../types";

interface FeedbackIndicatorProps {
  result: AnswerResult | null;
  visible: boolean;
}

export default function FeedbackIndicator({
  result,
  visible,
}: FeedbackIndicatorProps) {
  if (!result) return null;

  return (
    <Collapse in={visible}>
      <Alert
        severity={result.is_correct ? "success" : "error"}
        icon={result.is_correct ? <CorrectIcon /> : <IncorrectIcon />}
        sx={{ mt: 2, mb: 1 }}
      >
        <Typography variant="body2" sx={{ fontWeight: 600 }}>
          {result.is_correct ? "Correct!" : "Incorrect"}
        </Typography>
        {result.feedback && (
          <Typography variant="body2">{result.feedback}</Typography>
        )}
      </Alert>
    </Collapse>
  );
}
