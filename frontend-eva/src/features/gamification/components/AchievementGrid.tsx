import React from 'react';
import { Grid, Card, CardContent, Typography, Box, Avatar, LinearProgress } from '@mui/material';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import LockIcon from '@mui/icons-material/Lock';
import StarsIcon from '@mui/icons-material/Stars';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { Achievement } from '../api';

interface Props {
  achievements: Achievement[];
}

export function AchievementGrid({ achievements }: Props) {
  const { t } = useTranslation();

  if (!achievements?.length) {
    return (
      <Box sx={{ py: 6, textAlign: 'center', bgcolor: 'rgba(15,23,42,0.4)', borderRadius: 4, border: '1px dashed rgba(255,255,255,0.1)' }}>
        <EmojiEventsIcon sx={{ fontSize: 60, color: 'rgba(255,255,255,0.2)', mb: 2 }} />
        <Typography color="text.secondary" sx={{ fontWeight: 500 }}>
          {t('no_achievements')}
        </Typography>
      </Box>
    );
  }

  return (
    <Grid container spacing={3}>
      {achievements.map((achievement, index) => (
        <Grid size={{ xs: 12, sm: 6, md: 4 }} key={achievement.id}>
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }} 
            animate={{ opacity: 1, scale: 1 }} 
            transition={{ duration: 0.4, delay: index * 0.1 }}
            whileHover={{ y: -5, scale: 1.02 }}
          >
            <Card sx={{ 
              height: '100%', 
              bgcolor: achievement.is_unlocked ? 'rgba(30,41,59,0.8)' : 'rgba(30,41,59,0.4)',
              backdropFilter: 'blur(10px)',
              borderRadius: 4,
              border: achievement.is_unlocked ? '1px solid rgba(250,204,21,0.3)' : '1px solid rgba(255,255,255,0.05)',
              boxShadow: achievement.is_unlocked ? '0 10px 30px -10px rgba(250,204,21,0.15)' : 'none',
              position: 'relative',
              overflow: 'hidden'
            }}>
              {/* Background Glow */}
              {achievement.is_unlocked && (
                <Box sx={{
                  position: 'absolute', top: -50, right: -50, width: 100, height: 100,
                  background: 'radial-gradient(circle, rgba(250,204,21,0.15) 0%, transparent 70%)',
                  borderRadius: '50%'
                }} />
              )}
              
              <CardContent sx={{ display: 'flex', flexDirection: 'column', height: '100%', p: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <Avatar sx={{ 
                    width: 56, height: 56,
                    background: achievement.is_unlocked ? 'linear-gradient(135deg, #fbbf24 0%, #d97706 100%)' : 'rgba(255,255,255,0.05)',
                    color: achievement.is_unlocked ? '#fff' : 'rgba(255,255,255,0.2)',
                    boxShadow: achievement.is_unlocked ? '0 8px 16px rgba(251,191,36,0.3)' : 'none',
                    border: achievement.is_unlocked ? 'none' : '1px dashed rgba(255,255,255,0.2)'
                  }}>
                    {achievement.is_unlocked ? <StarsIcon fontSize="large" /> : <LockIcon />}
                  </Avatar>
                  <Box sx={{ ml: 'auto' }}>
                    {achievement.is_unlocked && (
                      <Box sx={{ px: 1.5, py: 0.5, bgcolor: 'rgba(251,191,36,0.1)', color: '#fbbf24', borderRadius: 8, fontSize: '0.75rem', fontWeight: 700 }}>
                        +50 XP
                      </Box>
                    )}
                  </Box>
                </Box>
                
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" sx={{ color: achievement.is_unlocked ? '#fff' : '#cbd5e1', fontWeight: 700, mb: 0.5 }}>
                    {achievement.name}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#94a3b8', lineHeight: 1.6 }}>
                    {achievement.description}
                  </Typography>
                </Box>
                
                <Box sx={{ mt: 3 }}>
                  {achievement.is_unlocked ? (
                    <Typography variant="caption" sx={{ color: '#fbbf24', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <EmojiEventsIcon fontSize="small" /> {t('unlocked_on')} {new Date(achievement.unlocked_at!).toLocaleDateString()}
                    </Typography>
                  ) : (
                    <Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 600 }}>{t('locked')}</Typography>
                        <Typography variant="caption" sx={{ color: '#64748b' }}>0 / 100%</Typography>
                      </Box>
                      <LinearProgress variant="determinate" value={0} sx={{ height: 6, borderRadius: 3, bgcolor: 'rgba(255,255,255,0.05)' }} />
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
      ))}
    </Grid>
  );
}