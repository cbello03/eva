import React, { useState } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, ToggleButtonGroup, ToggleButton, Box, CircularProgress, Typography } from '@mui/material';
import { useLeaderboard } from '../hooks';

export function LeaderboardTable() {
  const [period, setPeriod] = useState<'weekly' | 'alltime'>('alltime');
  const { data, isLoading, error } = useLeaderboard(period);

  const handlePeriodChange = (_: React.MouseEvent<HTMLElement>, newPeriod: 'weekly' | 'alltime' | null) => {
    if (newPeriod !== null) setPeriod(newPeriod);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <ToggleButtonGroup
          value={period}
          exclusive
          onChange={handlePeriodChange}
          size="small"
        >
          <ToggleButton value="weekly">Semanal</ToggleButton>
          <ToggleButton value="alltime">Histórico</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {isLoading ? (
        <Box display="flex" justifyContent="center" p={3}><CircularProgress /></Box>
      ) : error ? (
        <Typography color="error">Error al cargar la tabla de clasificación.</Typography>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead sx={{ bgcolor: 'primary.main' }}>
              <TableRow>
                <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Rango</TableCell>
                <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>Estudiante</TableCell>
                <TableCell align="right" sx={{ color: 'white', fontWeight: 'bold' }}>XP</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {/* Asumimos que el backend envía la lista en data.entries */}
              {data?.entries?.map((entry: any, index: number) => (
                <TableRow 
                  key={entry.user_id} 
                  sx={{ 
                    '&:last-child td, &:last-child th': { border: 0 },
                    // Resaltar sutilmente al usuario actual si viene marcado en la data
                    bgcolor: entry.is_current_user ? '#e3f2fd' : 'inherit' 
                  }}
                >
                  <TableCell component="th" scope="row">
                    <Typography variant="h6" color={index < 3 ? 'secondary' : 'text.primary'}>
                      #{entry.rank || index + 1}
                    </Typography>
                  </TableCell>
                  <TableCell>{entry.display_name}</TableCell>
                  <TableCell align="right">
                    <Typography fontWeight="bold">{entry.xp}</Typography>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}