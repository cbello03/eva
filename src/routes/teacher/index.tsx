import React from 'react';
import { createFileRoute, Link } from '@tanstack/react-router';
import { Box, Typography, Grid, Card, CardContent, CircularProgress, Button, LinearProgress, Divider } from '@mui/material';
import PeopleIcon from '@mui/icons-material/People';
import EditIcon from '@mui/icons-material/Edit';
import { useTeacherAnalytics, useTeacherCourses } from '../../features/teacher/hooks';

export const Route = createFileRoute('/teacher/')({
  component: TeacherDashboard,
});

function TeacherDashboard() {
  const { data: analytics, isLoading: loadingAnalytics } = useTeacherAnalytics();
  const { data: courses, isLoading: loadingCourses } = useTeacherCourses();

  if (loadingAnalytics || loadingCourses) {
    return <Box display="flex" justifyContent="center" mt={10}><CircularProgress /></Box>;
  }

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto', mt: 4 }}>
      <Typography variant="h3" gutterBottom>Panel del Profesor</Typography>
      <Typography variant="subtitle1" color="text.secondary" paragraph>
        Monitorea el progreso de tus estudiantes y administra tu contenido.
      </Typography>

      <Typography variant="h5" sx={{ mt: 4, mb: 2 }}>Rendimiento General</Typography>
      <Grid container spacing={3} sx={{ mb: 6 }}>
        {analytics?.map((stat) => (
          <Grid size={{ xs: 12, md: 6 }} key={stat.course_id}>
            <Card elevation={2}>
              <CardContent>
                <Typography variant="h6" color="primary" gutterBottom noWrap>
                  {stat.course_title}
                </Typography>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <PeopleIcon color="action" />
                  <Typography variant="body1">{stat.total_students} estudiantes inscritos</Typography>
                </Box>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Completación Promedio ({stat.average_completion}%)
                </Typography>
                <LinearProgress variant="determinate" value={stat.average_completion} sx={{ mb: 2, height: 8, borderRadius: 4 }} color="success" />

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Puntaje Promedio ({stat.average_score}/100)
                </Typography>
                <LinearProgress variant="determinate" value={stat.average_score} sx={{ height: 8, borderRadius: 4 }} />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Divider sx={{ my: 4 }} />

      <Typography variant="h5" sx={{ mb: 2 }}>Mis Cursos</Typography>
      <Grid container spacing={2}>
        {courses?.map((course) => (
          <Grid size={{ xs: 12, sm: 6, md: 4 }} key={course.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Typography variant="h6" gutterBottom>{course.title}</Typography>
                <Typography variant="body2" color="text.secondary">
                  Estado: {course.status === 'published' ? 'Publicado' : 'Borrador'}
                </Typography>
              </CardContent>
              <Box sx={{ p: 2, pt: 0 }}>
                <Button 
                  variant="outlined" 
                  fullWidth 
                  startIcon={<EditIcon />}
                  component={Link}
                  to={`/teacher/courses/${course.id}/builder`}
                >
                  Constructor de Curso
                </Button>
              </Box>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}