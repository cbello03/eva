"use client";

import { Box, Typography, Chip } from "@mui/material";
import WhatshotIcon from "@mui/icons-material/Whatshot";

interface StreakDisplayProps {
  currentStreak: number;
  longestStreak: number;
}

export default function StreakDisplay({
  currentStreak,
  longestStreak,
}: StreakDisplayProps) {
  const isActive = currentStreak > 0;

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
      <Chip
        icon={<WhatshotIcon />}
        label={`${currentStreak} day${currentStreak !== 1 ? "s" : ""}`}
        color={isActive ? "warning" : "default"}
        variant={isActive ? "filled" : "outlined"}
        aria-label={`Current streak: ${currentStreak} days`}
      />
      <Typography variant="caption" color="text.secondary">
        Best: {longestStreak} day{longestStreak !== 1 ? "s" : ""}
      </Typography>
    </Box>
  );
}
