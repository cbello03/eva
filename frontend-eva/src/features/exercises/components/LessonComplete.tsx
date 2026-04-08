"use client";

import { Box, Button, Paper, Typography } from "@mui/material";
import {
  EmojiEvents as TrophyIcon,
  ArrowBack as BackIcon,
} from "@mui/icons-material";
import Link from "next/link";

interface LessonCompleteProps {
  correctFirstAttempt: number;
  totalExercises: number;
  courseId: number;
}

export default function LessonComplete({
  correctFirstAttempt,
  totalExercises,
  courseId,
}: LessonCompleteProps) {
  const accuracy =
    totalExercises > 0
      ? Math.round((correctFirstAttempt / totalExercises) * 100)
      : 0;

  return (
    <Paper
      sx={{
        p: 4,
        textAlign: "center",
        maxWidth: 480,
        mx: "auto",
        mt: 4,
      }}
    >
      <TrophyIcon sx={{ fontSize: 64, color: "warning.main", mb: 2 }} />
      <Typography variant="h4" gutterBottom>
        Lesson Complete!
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        You answered {correctFirstAttempt} of {totalExercises} correctly on the
        first try ({accuracy}% accuracy).
      </Typography>
      <Box sx={{ display: "flex", justifyContent: "center", gap: 2 }}>
        <Button
          component={Link}
          href={`/courses/${courseId}`}
          variant="contained"
          startIcon={<BackIcon />}
        >
          Back to Course
        </Button>
      </Box>
    </Paper>
  );
}
