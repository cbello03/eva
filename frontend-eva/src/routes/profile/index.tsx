import React from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { Typography, Box, Card, Grid, Skeleton } from '@mui/material';
import { AchievementGrid } from '../../features/gamification/components/AchievementGrid';
import { LeaderboardTable } from '../../features/gamification/components/LeaderboardTable';
import { useAchievements, useGamificationProfile } from '../../features/gamification/hooks';
import { useUser } from '../../features/auth/hooks';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import StarIcon from '@mui/icons-material/Star';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';

export const Route = createFileRoute('/profile/')({
  component: Profile,
});

function Profile() {
  const { t } = useTranslation();
  const { data: user } = useUser();
  const { data: profile } = useGamificationProfile();
  const { data: achievements, isLoading: loadingAchievements } = useAchievements();

  return (
    <Box sx={{ pb: 6 }}>
      {/* Header Card */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        <Card sx={{ 
          p: { xs: 4, md: 6 }, mb: 5, borderRadius: 6, 
          background: 'linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(236,72,153,0.15) 100%)',
          border: '1px solid rgba(255,255,255,0.08)',
          boxShadow: '0 20px 40px -10px rgba(0,0,0,0.4)',
          position: 'relative', overflow: 'hidden'
        }}>
          {/* Animated background blobs */}
          <Box sx={{ position: 'absolute', top: '-20%', left: '-5%', width: '30%', height: '150%', background: 'radial-gradient(ellipse, rgba(99,102,241,0.2) 0%, transparent 60%)', transform: 'rotate(30deg)', zIndex: 0 }} />
          <Box sx={{ position: 'absolute', bottom: '-20%', right: '-5%', width: '30%', height: '150%', background: 'radial-gradient(ellipse, rgba(236,72,153,0.2) 0%, transparent 60%)', transform: 'rotate(-30deg)', zIndex: 0 }} />

          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', position: 'relative', zIndex: 1 }}>
            <motion.div whileHover={{ scale: 1.05 }} transition={{ type: "spring", stiffness: 300 }}>
              <Box sx={{ 
                width: 120, height: 120, borderRadius: '50%', 
                background: 'linear-gradient(135deg, #6366f1, #ec4899)', 
                display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 3, 
                boxShadow: '0 10px 30px rgba(236,72,153,0.5)',
                border: '4px solid rgba(255,255,255,0.1)'
              }}>
                 <Typography variant="h2" sx={{ color: 'white', fontWeight: 800 }}>{user?.display_name?.charAt(0) || 'U'}</Typography>
              </Box>
            </motion.div>
            <Typography variant="h3" sx={{ fontWeight: 800, mb: 1, color: 'white' }}>{user?.display_name}</Typography>
            <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 2, bgcolor: 'rgba(15,23,42,0.4)', px: 3, py: 1, borderRadius: 8, border: '1px solid rgba(255,255,255,0.05)' }}>
              <Typography variant="h6" sx={{ color: '#818cf8', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 1 }}>
                <StarIcon /> {t('level')} {profile?.current_level || 1}
              </Typography>
              <Typography variant="h6" sx={{ color: '#94a3b8' }}>•</Typography>
              <Typography variant="h6" sx={{ color: '#f472b6', fontWeight: 700 }}>
                {profile?.total_xp || 0} {t('total_xp')}
              </Typography>
            </Box>
          </Box>
        </Card>
      </motion.div>

      <Grid container spacing={4}>
        <Grid size={{ xs: 12, md: 7 }}>
          <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.1 }} style={{ height: '100%' }}>
            <Card sx={{ p: 4, bgcolor: '#1e293b', height: '100%', borderRadius: 5, border: '1px solid rgba(255,255,255,0.05)' }}>
              <Typography variant="h5" sx={{ fontWeight: 800, mb: 1, display: 'flex', alignItems: 'center', gap: 1.5, color: 'white' }}>
                <EmojiEventsIcon sx={{ color: '#fbbf24', fontSize: 32 }} /> {t('profile_achievements_title')}
              </Typography>
              <Typography variant="body1" sx={{ color: '#94a3b8', mb: 5 }}>
                {t('profile_achievements_desc')}
              </Typography>
              
              {loadingAchievements ? (
                 <Grid container spacing={3}>
                   {[1, 2, 3].map(i => (
                     <Grid size={{ xs: 12, sm: 6, md: 4 }} key={i}>
                       <Skeleton variant="rectangular" height={220} sx={{ borderRadius: 4, bgcolor: 'rgba(255,255,255,0.05)' }} />
                     </Grid>
                   ))}
                 </Grid>
              ) : (
                <AchievementGrid achievements={achievements || []} />
              )}
            </Card>
          </motion.div>
        </Grid>
        
        <Grid size={{ xs: 12, md: 5 }}>
          <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.2 }} style={{ height: '100%' }}>
            <Card sx={{ p: 4, bgcolor: '#1e293b', height: '100%', borderRadius: 5, border: '1px solid rgba(255,255,255,0.05)' }}>
              <Typography variant="h5" sx={{ fontWeight: 800, mb: 1, color: 'white' }}>
                {t('leaderboard')}
              </Typography>
              <Typography variant="body1" sx={{ color: '#94a3b8', mb: 4 }}>
                ¡Compite con otros estudiantes por el primer lugar!
              </Typography>
              
              <Box sx={{ bgcolor: 'rgba(15,23,42,0.4)', p: 2, borderRadius: 4, border: '1px solid rgba(255,255,255,0.02)' }}>
                <LeaderboardTable />
              </Box>
            </Card>
          </motion.div>
        </Grid>
      </Grid>
    </Box>
  );
}