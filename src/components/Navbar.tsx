import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link, useNavigate } from '@tanstack/react-router';

export const Navbar = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    // Aquí luego limpiaremos el estado de Zustand
    navigate({ to: '/login' });
  };

  return (
    <AppBar position="static" sx={{ backgroundColor: '#2e7d32', mb: 3 }}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
          EVA - Plataforma Educativa
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button color="inherit" component={Link} to="/dashboard">Dashboard</Button>
          <Button color="inherit" onClick={handleLogout}>Cerrar Sesión</Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};