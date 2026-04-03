import React from 'react';
import { createFileRoute, Link } from '@tanstack/react-router';
import { Box, Typography, Card, CardContent, Button, Grid } from '@mui/material';
import { useProjects } from '../../features/projects/hooks';

export const Route = createFileRoute('/projects/')({
  component: ProjectsList,
});

function ProjectsList() {
  const { data: projects } = useProjects();
  
  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>Proyectos Disponibles</Typography>
      <Grid container spacing={3}>
        {projects?.map(p => (
          <Grid size={{ xs: 12, sm: 6 }} key={p.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{p.title}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  {p.description}
                </Typography>
                <Button variant="contained" component={Link} to={`/projects/${p.id}`}>
                  Ver Entregable
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}