import React from 'react';
import { createFileRoute, Link } from '@tanstack/react-router';
import { Typography, Button, Box } from '@mui/material';

export const Route = createFileRoute('/')({
  component: Index,
});

function Index() {
  return (
    <Box textAlign="center" mt={8}>
      <Typography variant="h3" gutterBottom>
        Bienvenido a EVA
      </Typography>
      <Typography variant="h6" color="textSecondary" paragraph>
        Entorno Virtual de Enseñanza-Aprendizaje.
      </Typography>
      <Button variant="contained" size="large" component={Link} to="/login">
        Comenzar a Aprender
      </Button>
    </Box>
  );
}