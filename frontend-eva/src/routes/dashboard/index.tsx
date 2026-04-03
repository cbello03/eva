import React from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { Typography, Grid, Card, CardContent, Box, Button, LinearProgress, Avatar } from '@mui/material';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';

export const Route = createFileRoute('/dashboard/')({
  component: Dashboard,
});

function Dashboard() {
  const { t } = useTranslation();

  const courses = [
    {
      title: 'Introducción a Data Science con Python', // Needs i18n ideally, but hardcoded courses usually come from API
      progress: 85,
      iconType: 'python',
      color1: '#002244',
      color2: '#003366'
    },
    {
      title: 'Diseño UI/UX Avanzado',
      progress: 60,
      iconType: 'design',
      color1: '#4A148C',
      color2: '#6A1B9A'
    }
  ];

  return (
    <Box>
      <Grid container spacing={4}>
        {/* Main Area */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">{t('my_courses')}</Typography>
            <Button size="small" sx={{ color: '#6366f1' }}>{t('view_all')}</Button>
          </Box>

          <Grid container spacing={3}>
            {courses.map((course, idx) => (
              <Grid size={{ xs: 12, sm: 6 }} key={idx}>
                <motion.div whileHover={{ y: -5 }} transition={{ duration: 0.2 }}>
                  <Card sx={{ bgcolor: '#1e293b', height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 4, boxShadow: '0 10px 25px -5px rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.05)' }}>
                    <Box sx={{
                      height: 120,
                      margin: 2,
                      borderRadius: 3,
                      background: `linear-gradient(135deg, ${course.color1} 0%, ${course.color2} 100%)`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      position: 'relative', overflow: 'hidden'
                    }}>
                      <Typography variant="h3" sx={{ color: 'white', opacity: 0.9, zIndex: 1 }}>
                        {course.iconType === 'python' ? '🐍' : '✒️'}
                      </Typography>
                    </Box>
                    <CardContent sx={{ flexGrow: 1, pt: 0, display: 'flex', flexDirection: 'column' }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2, minHeight: 48, color: 'white' }}>
                        {course.title}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 3 }}>
                        <Box sx={{
                          width: 60, height: 60, borderRadius: '50%',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          border: '4px solid #334155', borderTopColor: '#ec4899', borderRightColor: '#ec4899'
                        }}>
                          <Typography variant="subtitle2" sx={{ fontWeight: 700, color: 'white' }}>{course.progress}%</Typography>
                        </Box>
                      </Box>

                      <Button variant="contained" fullWidth sx={{
                        background: 'linear-gradient(90deg, #6366f1, #ec4899)',
                        color: 'white',
                        py: 1,
                        borderRadius: 10,
                        fontWeight: 600,
                        textTransform: 'none',
                        boxShadow: '0 8px 16px rgba(236,72,153,0.25)'
                      }}>
                        {t('continue')}
                      </Button>
                    </CardContent>
                  </Card>
                </motion.div>
              </Grid>
            ))}
          </Grid>

          {/* Progress Section */}
          <Card sx={{ mt: 4, bgcolor: '#1e293b', p: 3, borderRadius: 4, border: '1px solid rgba(255,255,255,0.05)' }}>
            <Typography variant="h6" sx={{ mb: 3, color: 'white' }}>{t('learning_progress')}</Typography>
            <Typography variant="body2" sx={{ mb: 1, color: '#94a3b8' }}>{t('linear_progress')}</Typography>
            <LinearProgress variant="determinate" value={70} sx={{
              height: 10, borderRadius: 5, mb: 4,
              backgroundColor: '#334155',
              '& .MuiLinearProgress-bar': {
                background: 'linear-gradient(90deg, #6366f1, #ec4899)',
                borderRadius: 5
              }
            }} />
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
               <Typography variant="body2" sx={{ color: '#94a3b8' }}>{t('activity')}</Typography>
               <Typography variant="body2" sx={{ color: '#94a3b8' }}>{t('graphs')}</Typography>
            </Box>
            <Box sx={{ mt: 2, height: 100, display: 'flex', alignItems: 'flex-end', gap: 1 }}>
               {[40, 60, 30, 80, 50, 90, 40, 70, 60, 80, 50, 40].map((val, i) => (
                 <Box key={i} sx={{
                   flexGrow: 1,
                   bgcolor: i % 3 === 0 ? '#ec4899' : '#6366f1',
                   height: `${val}%`,
                   borderRadius: '4px 4px 0 0',
                   opacity: 0.8,
                   transition: 'height 1s ease'
                 }} />
               ))}
            </Box>
          </Card>
        </Grid>

        {/* Sidebar gamification */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ bgcolor: '#1e293b', mb: 4, borderRadius: 4, border: '1px solid rgba(255,255,255,0.05)' }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3, color: 'white' }}>{t('gamification_achievements')}</Typography>
              <Typography variant="body2" sx={{ color: '#94a3b8', mb: 2 }}>{t('recent_badges')}</Typography>
              <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
                 <Box sx={{ textAlign: 'center' }}>
                   <Avatar sx={{ width: 64, height: 64, bgcolor: 'rgba(99,102,241,0.2)', mb: 1, color: '#6366f1', mx: 'auto' }}>
                     <EmojiEventsIcon fontSize="large" />
                   </Avatar>
                   <Typography variant="caption" sx={{ color: 'white' }}>Maestro de Quiz</Typography>
                 </Box>
                 <Box sx={{ textAlign: 'center' }}>
                   <Avatar sx={{ width: 64, height: 64, bgcolor: 'rgba(236,72,153,0.2)', mb: 1, color: '#ec4899', mx: 'auto' }}>
                     <CheckCircleIcon fontSize="large" />
                   </Avatar>
                   <Typography variant="caption" sx={{ color: 'white' }}>Completador</Typography>
                 </Box>
              </Box>

              <Typography variant="body2" sx={{ color: '#94a3b8', mb: 2 }}>{t('upcoming_challenges')}</Typography>
              <Box sx={{ display: 'flex', gap: 2 }}>
                 <Avatar sx={{ width: 64, height: 64, bgcolor: 'rgba(255,255,255,0.05)', border: '1px dashed rgba(255,255,255,0.2)', color: 'gray' }}><EmojiEventsIcon /></Avatar>
                 <Avatar sx={{ width: 64, height: 64, bgcolor: 'rgba(255,255,255,0.05)', border: '1px dashed rgba(255,255,255,0.2)', color: 'gray' }}><EmojiEventsIcon /></Avatar>
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ bgcolor: '#1e293b', borderRadius: 4, border: '1px solid rgba(255,255,255,0.05)' }}>
             <CardContent>
                <Typography variant="h6" sx={{ mb: 3, color: 'white' }}>{t('leaderboard')}</Typography>
                {[
                  { name: 'Alex Thompson', score: 395, img: 'https://i.pravatar.cc/150?img=11', isUser: true },
                  { name: 'Maranida', score: 200, img: 'https://i.pravatar.cc/150?img=5' },
                  { name: 'Vlexk', score: 180, img: 'https://i.pravatar.cc/150?img=3' }
                ].map((user, i) => (
                  <Box key={i} sx={{ display: 'flex', alignItems: 'center', mb: 2, p: 1.5, borderRadius: 3, bgcolor: user.isUser ? 'rgba(99,102,241,0.1)' : 'transparent', border: user.isUser ? '1px solid rgba(99,102,241,0.2)' : 'none' }}>
                    <Typography sx={{ width: 24, color: '#94a3b8', fontWeight: 600 }}>{i + 1}</Typography>
                    <Avatar src={user.img} sx={{ width: 36, height: 36, mr: 2 }} />
                    <Typography sx={{ flexGrow: 1, fontWeight: user.isUser ? 600 : 400, color: 'white' }}>{user.name}</Typography>
                    <Typography sx={{ color: '#ec4899', fontWeight: 700 }}>{user.score}</Typography>
                  </Box>
                ))}
             </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}