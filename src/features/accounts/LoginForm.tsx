import { useState } from 'react';
import { TextField, Button, Box } from '@mui/material';
import { useAuthStore } from '../../store/auth-store';
import { useNavigate } from '@tanstack/react-router'; // Importamos el navegador

export const LoginForm = () => {
  const [email, setEmail] = useState('');
  const setAuth = useAuthStore((state) => state.setAuth);
  const navigate = useNavigate(); // Inicializamos la función para saltar de página

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // 1. Guardamos la sesión en Zustand
    setAuth(
      { id: '1', email, full_name: 'Usuario Prueba', role: 'student' },
      'token-fake-123'
    );
    
    // 2. ¡SALTO AUTOMÁTICO! Nos vamos al Dashboard
    navigate({ to: '/dashboard' });
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
      <TextField
        margin="normal"
        fullWidth
        label="Correo Electrónico"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        autoFocus
      />
      <TextField
        margin="normal"
        fullWidth
        label="Contraseña"
        type="password"
      />
      <Button
        type="submit"
        fullWidth
        variant="contained"
        sx={{ mt: 3, backgroundColor: '#2e7d32', fontWeight: 'bold' }}
      >
        Ingresar
      </Button>
    </Box>
  );
};