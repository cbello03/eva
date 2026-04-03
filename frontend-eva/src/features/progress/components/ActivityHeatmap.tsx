import React from 'react';
import { Box, Typography, Tooltip, Paper } from '@mui/material';
import { DailyActivity } from '../api';

interface Props {
  data: DailyActivity[];
}

// Colores estilo GitHub (verde)
const getColorForLevel = (level: number) => {
  switch (level) {
    case 1: return '#9be9a8';
    case 2: return '#40c463';
    case 3: return '#30a14e';
    case 4: return '#216e39';
    default: return '#ebedf0'; // Gris (sin actividad)
  }
};

export function ActivityHeatmap({ data }: Props) {
  if (!data?.length) return null;

  return (
    <Paper sx={{ p: 3, mb: 4 }}>
      <Typography variant="h6" gutterBottom>Actividad Reciente</Typography>
      
      {/* Usamos CSS Grid para dibujar los cuadritos */}
      <Box 
        sx={{ 
          display: 'grid', 
          // Ajustamos las columnas dependiendo de cuántos días mostremos (ej. 30 días = 10 cols x 3 rows)
          gridTemplateColumns: 'repeat(auto-fill, minmax(15px, 1fr))', 
          gap: '4px',
          maxWidth: 600
        }}
      >
        {data.map((day, index) => (
          <Tooltip 
            key={index} 
            title={`${day.date}: ${day.activity_count} acciones`}
            arrow
          >
            <Box
              sx={{
                width: 15,
                height: 15,
                backgroundColor: getColorForLevel(day.level),
                borderRadius: '2px',
                cursor: 'pointer',
                '&:hover': {
                  opacity: 0.8,
                  border: '1px solid #000'
                }
              }}
            />
          </Tooltip>
        ))}
      </Box>
    </Paper>
  );
}