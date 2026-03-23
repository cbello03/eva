import React, { Suspense } from 'react';
import { Outlet, createRootRoute, Link } from '@tanstack/react-router';
import { AppBar, Toolbar, Typography, Button, Box, CircularProgress, Container } from '@mui/material';
import { useAuthStore } from '../features/auth/store';

// Componente de Navbar integrado
const Navbar = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const logout = useAuthStore((state) => state.logout);

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          <Link to="/" style={{ color: 'white', textDecoration: 'none' }}>
            EVA Platform
          </Link>
        </Typography>
        <Box>
          {isAuthenticated ? (
            <>
              <Button color="inherit" component={Link} to="/dashboard">Dashboard</Button>
              <Button color="inherit" onClick={logout}>Salir</Button>
            </>
          ) : (
            <>
              <Button color="inherit" component={Link} to="/login">Entrar</Button>
              <Button color="inherit" component={Link} to="/register">Registrarse</Button>
            </>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export const Route = createRootRoute({
  component: () => (
    <>
      <Navbar />
      <Container sx={{ mt: 4 }}>
        {/* Suspense maneja los estados de carga de las rutas hijas */}
        <Suspense fallback={<Box display="flex" justifyContent="center"><CircularProgress /></Box>}>
          <Outlet />
        </Suspense>
      </Container>
    </>
  ),
});