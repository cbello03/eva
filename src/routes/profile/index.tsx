import React from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { Container, Typography, Box, Divider, CircularProgress } from '@mui/material';
import { AchievementGrid } from '../../features/gamification/components/AchievementGrid';
import { LeaderboardTable } from '../../features/gamification/components/LeaderboardTable';
import { useAchievements, useGamificationProfile } from '../../features/gamification/hooks';
import { useUser } from '../../features/auth/hooks';

export const Route = createFileRoute('/profile/')({
  component: Profile,
});

function Profile() {
  const { data: user } = useUser();
  const { data: profile } = useGamificationProfile();
  const { data: achievements, isLoading: loadingAchievements } = useAchievements();

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 8 }}>
      {/* Cabecera del Perfil */}
      <Box sx={{ mb: 4, textAlign: 'center' }}>
        <Typography variant="h3" gutterBottom>Perfil de {user?.display_name}</Typography>
        <Typography variant="h6" color="primary">
          Nivel {profile?.current_level || 1} • {profile?.total_xp || 0} XP Total
        </Typography>
      </Box>

      <Divider sx={{ my: 4 }} />

      {/* Sección de Logros */}
      <Box sx={{ mb: 6 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          Mis Logros
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          Completa lecciones y mantén tu racha para desbloquear recompensas.
        </Typography>
        
        {loadingAchievements ? (
          <CircularProgress />
        ) : (
          <AchievementGrid achievements={achievements || []} />
        )}
      </Box>

      <Divider sx={{ my: 4 }} />

      {/* Sección de Competencia (Tabla de Clasificación) */}
      <Box>
        <Typography variant="h4" gutterBottom>
          Tabla de Clasificación
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          ¡Compite con otros estudiantes por el primer lugar!
        </Typography>
        
        <LeaderboardTable />
      </Box>
    </Container>
  );
}