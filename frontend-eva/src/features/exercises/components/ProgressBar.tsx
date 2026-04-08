"use client";

import { Box, LinearProgress, Typography } from "@mui/material";

interface ProgressBarProps {
  current: number;
  total: number;
}

export default function ProgressBar({ current, total }: ProgressBarProps) {
  const percentage = total > 0 ? (current / total) * 100 : 0;

  return (
    <Box sx={{ width: "100%", mb: 3 }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          Progress
        </Typography>
        <Typography variant="caption" sx={{ fontWeight: 600 }}>
          {current}/{total}
        </Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={Math.min(percentage, 100)}
        sx={{ borderRadius: 4, height: 10 }}
      />
    </Box>
  );
}
