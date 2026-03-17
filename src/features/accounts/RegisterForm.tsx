import { useState } from 'react';
import { TextField, Button, Typography, Paper, Box, MenuItem } from '@mui/material';
import { Link } from '@tanstack/react-router';

// Aquí también, el 'export' es la clave
export const RegisterForm = () => {
  const [role, setRole] = useState('student');

  return (
    <Paper elevation={3} sx={{ p: 4, borderRadius: 3, maxWidth: 450, width: '100%' }}>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 'bold', textAlign: 'center' }}>
        Crear cuenta en EVA
      </Typography>

      <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField label="Nombre Completo" fullWidth required />
        <TextField label="Correo Electrónico" type="email" fullWidth required />
        <TextField label="Contraseña" type="password" fullWidth required />
        
        <TextField select label="¿Quién eres?" value={role} onChange={(e) => setRole(e.target.value)} fullWidth>
          <MenuItem value="student">Estudiante</MenuItem>
          <MenuItem value="teacher">Profesor</MenuItem>
        </TextField>

        <Button type="submit" variant="contained" sx={{ mt: 2, backgroundColor: '#2e7d32' }}>
          Registrarme
        </Button>
      </Box>

      <Typography variant="body2" sx={{ mt: 2, textAlign: 'center' }}>
        ¿Ya tienes cuenta? <Link to="/login" style={{ color: '#2e7d32', fontWeight: 'bold' }}>Inicia sesión</Link>
      </Typography>
    </Paper>
  );
};