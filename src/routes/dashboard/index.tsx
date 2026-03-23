import React from 'react';
import { createFileRoute, Link } from '@tanstack/react-router';
import { Typography, Grid, Card, CardContent, Box, CircularProgress, Button } from '@mui/material';
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment';
import StarIcon from '@mui/icons-material/Star';
import EmojiEventsIcon from '@mui/icons-material/EmojiEvents';
import { useGamificationProfile } from '../../features/gamification/hooks';
import { useUser } from '../../features/auth/hooks';

export const Route = createFileRoute('/dashboard/')({
  component: Dashboard,
});

function Dashboard() {
  const { data: user } = useUser();
  const { data: profile, isLoading } = useGamificationProfile();

  if (isLoading) return <Box display="flex" justifyContent="center" mt={5}><CircularProgress /></Box>;

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        ¡Hola, {user?.display_name || 'Estudiante'}!
      </Typography>
      
      {/* Panel de Estadísticas (Gamificación) */}
      <Grid container spacing={3} sx={{ mb: 6 }}>
        {/* Tarjeta de Nivel */}
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: '#e3f2fd', textAlign: 'center', py: 2 }}>
            <CardContent>
              <StarIcon sx={{ fontSize: 50, color: '#1976d2' }} />
              <Typography variant="h5" sx={{ mt: 1 }}>Nivel {profile?.current_level || 1}</Typography>
              <Typography color="text.secondary">Sigue aprendiendo para subir</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Tarjeta de XP */}
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: '#fff8e1', textAlign: 'center', py: 2 }}>
            <CardContent>
              <EmojiEventsIcon sx={{ fontSize: 50, color: '#ffa000' }} />
              <Typography variant="h5" sx={{ mt: 1 }}>{profile?.total_xp || 0} XP</Typography>
              <Typography color="text.secondary">Experiencia total</Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Tarjeta de Racha */}
        <Grid item xs={12} sm={4}>
          <Card sx={{ bgcolor: '#ffebee', textAlign: 'center', py: 2 }}>
            <CardContent>
              <LocalFireDepartmentIcon sx={{ fontSize: 50, color: '#d32f2f' }} />
              <Typography variant="h5" sx={{ mt: 1 }}>{profile?.current_streak || 0} Días</Typography>
              <Typography color="text.secondary">Racha de estudio (Máx: {profile?.longest_streak || 0})</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Accesos rápidos */}
      <Typography variant="h5" gutterBottom>Tus atajos</Typography>
      <Grid container spacing={2}>
        <Grid item>
          <Button variant="contained" component={Link} to="/courses" size="large">
            Explorar Catálogo de Cursos
          </Button>
        </Grid>
        <Grid item>
          <Button variant="outlined" component={Link} to="/profile" size="large">
            Ver mis Logros
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
}