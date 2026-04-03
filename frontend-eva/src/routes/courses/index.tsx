import React from 'react';
import { createFileRoute, Link } from '@tanstack/react-router';
import { Typography, Grid, Card, CardContent, Button, Box, CircularProgress, Chip, Skeleton } from '@mui/material';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { useCourses } from '../../features/courses/hooks';
import AutoStoriesIcon from '@mui/icons-material/AutoStories';

export const Route = createFileRoute('/courses/')({
  component: CourseList,
});

function CourseList() {
  const { t } = useTranslation();
  const { data: courses, isLoading, error } = useCourses();

  // ... (Skeleton loading keeps original code thanks to precise replacement bounds)

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" sx={{ mb: 4, visibility: 'hidden' }}>Loading</Typography>
        <Grid container spacing={3}>
          {[1, 2, 3, 4].map(n => (
            <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={n}>
              <Card sx={{ bgcolor: '#1e293b', height: 350, display: 'flex', flexDirection: 'column' }}>
                <Skeleton variant="rectangular" height={140} sx={{ m: 1.5, borderRadius: 4, bgcolor: 'rgba(255,255,255,0.05)' }} />
                <CardContent sx={{ flexGrow: 1 }}>
                  <Skeleton variant="text" sx={{ fontSize: '1.5rem', mb: 1, bgcolor: 'rgba(255,255,255,0.05)' }} />
                  <Skeleton variant="text" sx={{ fontSize: '1rem', mb: 1, bgcolor: 'rgba(255,255,255,0.05)' }} />
                  <Skeleton variant="text" width="60%" sx={{ mb: 3, bgcolor: 'rgba(255,255,255,0.05)' }} />
                  <Skeleton variant="rounded" height={40} sx={{ borderRadius: 8, bgcolor: 'rgba(255,255,255,0.05)' }} />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }
  if (error) return <Typography color="error">Error loading courses.</Typography>;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 800 }}>{t('course_catalog')}</Typography>
        <Button variant="outlined" sx={{ borderRadius: 8, borderColor: 'rgba(255,255,255,0.2)', color: 'white' }}>
          {t('filter_categories')}
        </Button>
      </Box>

      <Grid container spacing={3}>
        {courses?.map((course) => (
          <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }} key={course.id}>
            <Card sx={{ 
              bgcolor: '#1e293b', 
              height: '100%', 
              display: 'flex', 
              flexDirection: 'column',
              transition: 'transform 0.3s ease',
              '&:hover': {
                transform: 'translateY(-6px)',
                boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.4)'
              }
            }}>
              <Box sx={{
                height: 140, margin: 1.5, borderRadius: 4,
                background: 'linear-gradient(135deg, #1e3a8a 0%, #312e81 100%)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                position: 'relative'
              }}>
                <AutoStoriesIcon sx={{ fontSize: 60, color: 'rgba(255,255,255,0.8)' }} />
                <Chip label="NUEVO" size="small" sx={{ position: 'absolute', top: 12, right: 12, bgcolor: '#ec4899', color: 'white', fontWeight: 'bold' }} />
              </Box>

              <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', pb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 1, lineHeight: 1.2 }}>
                  {course.title}
                </Typography>
                <Typography variant="body2" sx={{ color: '#94a3b8', mb: 3, flexGrow: 1 }}>
                  {course.description || 'Sumérgete en este curso integral y abre tu potencial hoy mismo.'}
                </Typography>
                
                <Button 
                  fullWidth 
                  variant="contained" 
                  component={Link} 
                  to={`/courses/${course.id}`}
                  sx={{
                    background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
                    borderRadius: 8,
                    fontWeight: 600
                  }}
                >
                  Ver Detalles
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}