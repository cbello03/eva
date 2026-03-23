import React from 'react';
import { Box, LinearProgress, Typography } from '@mui/material';

interface Props {
  currentIndex: number;
  total: number;
}

export function ProgressBar({ currentIndex, total }: Props) {
  // Calculamos el porcentaje, limitándolo a 100
  const progress = total > 0 ? Math.min((currentIndex / total) * 100, 100) : 0;

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', mb: 4 }}>
      <Box sx={{ width: '100%', mr: 2 }}>
        <LinearProgress variant="determinate" value={progress} sx={{ height: 10, borderRadius: 5 }} />
      </Box>
      <Box sx={{ minWidth: 35 }}>
        <Typography variant="body2" color="text.secondary">{`${Math.round(progress)}%`}</Typography>
      </Box>
    </Box>
  );
}