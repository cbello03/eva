import React from 'react';
import { createFileRoute, Link } from '@tanstack/react-router';
import { Typography, Button, Box, Container, Grid } from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { useTranslation } from 'react-i18next';

export const Route = createFileRoute('/')({
  component: Index,
});

function Index() {
  const { t } = useTranslation();

  return (
    <Box sx={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: 'radial-gradient(circle at top right, #1e293b 0%, #0f172a 100%)',
    }}>
      <Container maxWidth="lg" sx={{ pt: 12, pb: 10, flexGrow: 1, zIndex: 1, position: 'relative' }}>
        <Grid container spacing={8} alignItems="center">
          <Grid size={{ xs: 12, md: 6 }}>
            <Box sx={{
              display: 'inline-block', mb: 3, px: 2, py: 0.5, borderRadius: 10,
              bgcolor: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.3)',
              color: '#818cf8', fontWeight: 600, fontSize: '0.875rem'
            }}>
              {t('landing_news')}
            </Box>
            
            <Typography variant="h1" sx={{ color: '#f8fafc', fontWeight: 800, mb: 3, fontSize: { xs: '3rem', md: '4rem' }, lineHeight: 1.1 }}>
              {t('landing_title')} <span style={{ background: 'linear-gradient(90deg, #6366f1 0%, #ec4899 100%)', WebkitBackgroundClip: 'text', color: 'transparent' }}>{t('landing_title_hl')}</span>
            </Typography>
            
            <Typography variant="h6" sx={{ color: '#94a3b8', mb: 5, fontWeight: 400, maxWidth: 480, lineHeight: 1.6 }}>
              {t('landing_desc')}
            </Typography>
            
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Button
                variant="contained" size="large" component={Link} to="/register"
                sx={{
                  py: 1.5, px: 4, borderRadius: 8, fontSize: '1.1rem', fontWeight: 700, textTransform: 'none',
                  background: 'linear-gradient(90deg, #6366f1 0%, #ec4899 100%)',
                  boxShadow: '0 8px 16px rgba(236,72,153,0.3)'
                }}
              >
                {t('learn_more')}
              </Button>
              <Button
                variant="outlined" size="large" component={Link} to="/login"
                startIcon={<PlayArrowIcon />}
                sx={{
                  py: 1.5, px: 4, borderRadius: 8, fontSize: '1.1rem', fontWeight: 700, textTransform: 'none',
                  borderColor: 'rgba(255,255,255,0.2)', color: 'white',
                  '&:hover': { borderColor: 'white', bgcolor: 'rgba(255,255,255,0.05)' }
                }}
              >
                {t('login_btn')}
              </Button>
            </Box>
          </Grid>
          
          <Grid size={{ xs: 12, md: 6 }}>
            <Box sx={{ position: 'relative' }}>
              <Box sx={{
                position: 'absolute', top: -50, right: -50, width: 300, height: 300,
                background: 'radial-gradient(circle, rgba(236,72,153,0.2) 0%, transparent 70%)',
                filter: 'blur(40px)', zIndex: 0
              }} />
              <Box sx={{
                position: 'absolute', bottom: -50, left: -50, width: 300, height: 300,
                background: 'radial-gradient(circle, rgba(99,102,241,0.2) 0%, transparent 70%)',
                filter: 'blur(40px)', zIndex: 0
              }} />
              
              <Box sx={{
                position: 'relative', zIndex: 2, borderRadius: 6, overflow: 'hidden',
                border: '1px solid rgba(255,255,255,0.1)',
                boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
                bgcolor: '#1e293b', p: 1
              }}>
                <img src="https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&q=80&w=800&h=600" alt="EVA Dashboard Preview" style={{ width: '100%', borderRadius: 16, display: 'block', opacity: 0.8 }} />
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}