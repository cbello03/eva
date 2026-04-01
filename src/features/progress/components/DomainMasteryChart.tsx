import React from 'react';
import { Box, Typography, LinearProgress, Paper } from '@mui/material';
import { DomainMastery } from '../api';

interface Props {
  domains: DomainMastery[];
}

export function DomainMasteryChart({ domains }: Props) {
  if (!domains?.length) return null;

  return (
    <Paper sx={{ p: 3, mb: 4 }}>
      <Typography variant="h6" gutterBottom>Dominio por Áreas</Typography>
      
      {domains.map((domain) => (
        <Box key={domain.id} sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="body2">{domain.domain_name}</Typography>
            <Typography variant="body2" color="text.secondary">
              {domain.mastery_percentage}%
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={domain.mastery_percentage} 
            sx={{ height: 8, borderRadius: 4 }}
            color={domain.mastery_percentage >= 80 ? 'success' : 'primary'}
          />
        </Box>
      ))}
    </Paper>
  );
}