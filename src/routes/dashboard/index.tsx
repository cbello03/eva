import React from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { Typography, Grid, Card, CardContent, Box, Button, LinearProgress, Avatar } from '@mui/material';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

export const Route = createFileRoute('/dashboard/')({
  component: Dashboard,
});

function Dashboard() {
  const courses = [
    {
      title: 'Introducción a Data Science con Python',
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
            <Typography variant="h6">Mis Cursos</Typography>
            <Button size="small" sx={{ color: '#6366f1' }}>Ver todos</Button>
          </Box>

          <Grid container spacing={3}>
            {courses.map((course, idx) => (
              <Grid size={{ xs: 12, sm: 6 }} key={idx}>
                <Card sx={{ bgcolor: '#1e293b', height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Box sx={{
                    height: 120,
                    margin: 2,
                    borderRadius: 3,
                    background: `linear-gradient(135deg, ${course.color1} 0%, ${course.color2} 100%)`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}>
                    <Typography variant="h3" sx={{ color: 'white', opacity: 0.8 }}>
                      {course.iconType === 'python' ? '🐍' : '✒️'}
                    </Typography>
                  </Box>
                  <CardContent sx={{ flexGrow: 1, pt: 0, display: 'flex', flexDirection: 'column' }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2, minHeight: 48 }}>
                      {course.title}
                    </Typography>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 3 }}>
                      {/* Fake Circular Progress for presentation */}
                      <Box sx={{
                        width: 60, height: 60, borderRadius: '50%',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        border: '4px solid #334155', borderTopColor: '#ec4899', borderRightColor: '#ec4899'
                      }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{course.progress}%</Typography>
                      </Box>
                    </Box>

                    <Button variant="contained" fullWidth sx={{
                      background: 'linear-gradient(90deg, #6366f1, #ec4899)',
                      color: 'white',
                      py: 1,
                      borderRadius: 10
                    }}>
                      Continuar
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* Progress Section */}
          <Card sx={{ mt: 4, bgcolor: '#1e293b', p: 3 }}>
            <Typography variant="h6" sx={{ mb: 3 }}>Progreso de Aprendizaje</Typography>
            <Typography variant="body2" sx={{ mb: 1, color: '#94a3b8' }}>Avance lineal</Typography>
            <LinearProgress variant="determinate" value={70} sx={{
              height: 10, borderRadius: 5, mb: 4,
              backgroundColor: '#334155',
              '& .MuiLinearProgress-bar': {
                background: 'linear-gradient(90deg, #6366f1, #ec4899)'
              }
            }} />
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
               <Typography variant="body2" sx={{ color: '#94a3b8' }}>Actividad</Typography>
               <Typography variant="body2" sx={{ color: '#94a3b8' }}>Gráficos</Typography>
            </Box>
            <Box sx={{ mt: 2, height: 100, display: 'flex', alignItems: 'flex-end', gap: 1 }}>
               {[40, 60, 30, 80, 50, 90, 40, 70, 60, 80, 50, 40].map((val, i) => (
                 <Box key={i} sx={{
                   flexGrow: 1,
                   bgcolor: i % 3 === 0 ? '#ec4899' : '#6366f1',
                   height: `${val}%`,
                   borderRadius: '4px 4px 0 0',
                   opacity: 0.8
                 }} />
               ))}
            </Box>
          </Card>
        </Grid>

        {/* Sidebar gamification */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ bgcolor: '#1e293b', mb: 4 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3 }}>Gamificación y Logros</Typography>
              <Typography variant="body2" sx={{ color: '#94a3b8', mb: 2 }}>Insignias recientes</Typography>
              <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
                 <Box sx={{ textAlign: 'center' }}>
                   <Avatar sx={{ width: 64, height: 64, bgcolor: 'rgba(99,102,241,0.2)', mb: 1, color: '#6366f1' }}><EmojiEventsIcon fontSize="large" /></Avatar>
                   <Typography variant="caption">Maestro de Quiz</Typography>
                 </Box>
                 <Box sx={{ textAlign: 'center' }}>
                   <Avatar sx={{ width: 64, height: 64, bgcolor: 'rgba(236,72,153,0.2)', mb: 1, color: '#ec4899' }}><CheckCircleIcon fontSize="large" /></Avatar>
                   <Typography variant="caption">Completador</Typography>
                 </Box>
              </Box>

              <Typography variant="body2" sx={{ color: '#94a3b8', mb: 2 }}>Próximos Desafíos</Typography>
              <Box sx={{ display: 'flex', gap: 2 }}>
                 <Avatar sx={{ width: 64, height: 64, bgcolor: 'rgba(255,255,255,0.05)', border: '1px dashed rgba(255,255,255,0.2)', color: 'gray' }}><EmojiEventsIcon /></Avatar>
                 <Avatar sx={{ width: 64, height: 64, bgcolor: 'rgba(255,255,255,0.05)', border: '1px dashed rgba(255,255,255,0.2)', color: 'gray' }}><EmojiEventsIcon /></Avatar>
              </Box>
            </CardContent>
          </Card>

          <Card sx={{ bgcolor: '#1e293b' }}>
             <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>Clasificación</Typography>
                {[
                  { name: 'Alex Thompson', score: 395, img: 'https://i.pravatar.cc/150?img=11', isUser: true },
                  { name: 'Maranida', score: 200, img: 'https://i.pravatar.cc/150?img=5' },
                  { name: 'Vlexk', score: 180, img: 'https://i.pravatar.cc/150?img=3' }
                ].map((user, i) => (
                  <Box key={i} sx={{ display: 'flex', alignItems: 'center', mb: 2, p: 1, borderRadius: 2, bgcolor: user.isUser ? 'rgba(255,255,255,0.05)' : 'transparent' }}>
                    <Typography sx={{ width: 24, color: '#94a3b8' }}>{i + 1}</Typography>
                    <Avatar src={user.img} sx={{ width: 32, height: 32, mr: 2 }} />
                    <Typography sx={{ flexGrow: 1, fontWeight: user.isUser ? 600 : 400 }}>{user.name}</Typography>
                    <Typography sx={{ color: '#ec4899', fontWeight: 600 }}>{user.score}</Typography>
                  </Box>
                ))}
             </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}