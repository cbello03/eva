import React from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { Typography, Box, CircularProgress, Card, Grid, Skeleton } from '@mui/material';
import { AchievementGrid } from '../../features/gamification/components/AchievementGrid';
import { LeaderboardTable } from '../../features/gamification/components/LeaderboardTable';
import { useAchievements, useGamificationProfile } from '../../features/gamification/hooks';
import { useUser } from '../../features/auth/hooks';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import StarIcon from '@mui/icons-material/Star';

export const Route = createFileRoute('/profile/')({
  component: Profile,
});

function Profile() {
  const { data: user } = useUser();
  const { data: profile } = useGamificationProfile();
  const { data: achievements, isLoading: loadingAchievements } = useAchievements();

  return (
    <Box sx={{ pb: 6 }}>
      {/* Header Card */}
      <Card sx={{ 
        p: 5, mb: 4, borderRadius: 4, 
        background: 'linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(236,72,153,0.1) 100%)',
        border: '1px solid rgba(255,255,255,0.05)',
        display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center'
      }}>
        <Box sx={{ width: 100, height: 100, borderRadius: '50%', background: 'linear-gradient(135deg, #6366f1, #ec4899)', display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2, boxShadow: '0 0 30px rgba(236,72,153,0.4)' }}>
           <Typography variant="h3" sx={{ color: 'white', fontWeight: 800 }}>{user?.display_name?.charAt(0) || 'U'}</Typography>
        </Box>
        <Typography variant="h3" sx={{ fontWeight: 800, mb: 1 }}>{user?.display_name}</Typography>
        <Typography variant="h6" sx={{ color: '#ec4899', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
          <StarIcon /> Level {profile?.current_level || 1} • {profile?.total_xp || 0} XP Total
        </Typography>
      </Card>

      <Grid container spacing={4}>
        <Grid size={{ xs: 12, md: 7 }}>
          <Card sx={{ p: 3, bgcolor: '#1e293b', height: '100%' }}>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              <EmojiEventsIcon sx={{ color: '#ec4899' }} /> Mis Logros
            </Typography>
            <Typography variant="body2" sx={{ color: '#94a3b8', mb: 4 }}>
              Completa lecciones y mantén tu racha para desbloquear recompensas.
            </Typography>
            
            {loadingAchievements ? (
               <Skeleton variant="rectangular" height={150} sx={{ borderRadius: 2, bgcolor: 'rgba(255,255,255,0.05)' }} />
            ) : (
              <Box sx={{ bgcolor: 'rgba(255,255,255,0.02)', p: 2, borderRadius: 2 }}>
                <AchievementGrid achievements={achievements || []} />
              </Box>
            )}
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, md: 5 }}>
          <Card sx={{ p: 3, bgcolor: '#1e293b', height: '100%' }}>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
              Tabla de Clasificación
            </Typography>
            <Typography variant="body2" sx={{ color: '#94a3b8', mb: 4 }}>
              ¡Compite con otros estudiantes por el primer lugar!
            </Typography>
            
            <Box sx={{ bgcolor: 'rgba(255,255,255,0.02)', p: 1, borderRadius: 2 }}>
              <LeaderboardTable />
            </Box>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}