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
        label={`${currentStreak} día${currentStreak !== 1 ? "s" : ""}`}
        color={isActive ? "warning" : "default"}
        variant={isActive ? "filled" : "outlined"}
        aria-label={`Racha actual: ${currentStreak} días`}
      />
      <Typography variant="caption" color="text.secondary">
        Mejor: {longestStreak} día{longestStreak !== 1 ? "s" : ""}
      </Typography>
    </Box>
  );
}
