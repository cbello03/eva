"use client";

import {
  Box,
  Typography,
  Paper,
  Chip,
  Divider,
} from "@mui/material";
import type { ProjectReview, RubricCriterion } from "../api";

interface ReviewListProps {
  reviews: ProjectReview[];
  rubric: RubricCriterion[];
}

export default function ReviewList({ reviews, rubric }: ReviewListProps) {
  if (reviews.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        Aún no hay evaluaciones.
      </Typography>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {reviews.map((review) => {
        const totalScore = Object.values(review.scores).reduce((a, b) => a + b, 0);
        const maxTotal = rubric.reduce((a, c) => a + c.max_score, 0);

        return (
          <Paper key={review.id} sx={{ p: 2 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
              <Typography variant="subtitle2">
                {review.reviewer_name}
              </Typography>
              <Box sx={{ display: "flex", gap: 1 }}>
                <Chip
                  label={review.review_type}
                  size="small"
                  color={review.review_type === "teacher" ? "primary" : "default"}
                  variant="outlined"
                />
                <Chip
                  label={`${totalScore}/${maxTotal}`}
                  size="small"
                  variant="outlined"
                />
              </Box>
            </Box>

            <Box sx={{ display: "flex", gap: 2, mb: 1, flexWrap: "wrap" }}>
              {rubric.map((criterion) => (
                <Typography key={criterion.name} variant="caption" color="text.secondary">
                  {criterion.name}: {review.scores[criterion.name] ?? 0}/{criterion.max_score}
                </Typography>
              ))}
            </Box>

            <Divider sx={{ my: 1 }} />

            <Typography variant="body2">{review.feedback}</Typography>
          </Paper>
        );
      })}
    </Box>
  );
}
