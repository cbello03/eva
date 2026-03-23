import { createFileRoute, useNavigate, Link } from '@tanstack/react-router'; // <-- Importamos Link
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { TextField, Button, Box, Typography, Container, Alert, Grid } from '@mui/material'; // <-- Importamos Grid
import { registerSchema, RegisterData } from '../features/auth/api';
import { useRegister } from '../features/auth/hooks';

export const Route = createFileRoute('/register')({
  component: Register,
});

function Register() {
  const registerMutation = useRegister();
  const navigate = useNavigate();
  
  const { register, handleSubmit, formState: { errors } } = useForm<RegisterData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = (data: RegisterData) => {
    registerMutation.mutate(data, {
      onSuccess: () => navigate({ to: '/login' }),
    });
  };

  return (
    <Container maxWidth="xs">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Typography component="h1" variant="h5">
          Crear cuenta en EVA
        </Typography>

        {registerMutation.isError && (
          <Alert severity="error" sx={{ mt: 2, width: '100%' }}>
            Error al registrar. El correo podría estar en uso.
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ mt: 1 }}>
          <TextField
            margin="normal"
            fullWidth
            label="Nombre a mostrar"
            {...register('display_name')}
            error={!!errors.display_name}
            helperText={errors.display_name?.message}
          />
          <TextField
            margin="normal"
            fullWidth
            label="Correo Electrónico"
            {...register('email')}
            error={!!errors.email}
            helperText={errors.email?.message}
          />
          <TextField
            margin="normal"
            fullWidth
            label="Contraseña"
            type="password"
            {...register('password')}
            error={!!errors.password}
            helperText={errors.password?.message}
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={registerMutation.isPending}
          >
            {registerMutation.isPending ? 'Registrando...' : 'Registrarse'}
          </Button>

          {/* Aquí agregamos el enlace hacia el Login */}
          <Grid container justifyContent="flex-end">
            <Grid item>
              <Link to="/login" style={{ textDecoration: 'none', color: '#1976d2' }}>
                {"¿Ya tienes una cuenta? Inicia sesión"}
              </Link>
            </Grid>
          </Grid>

        </Box>
      </Box>
    </Container>
  );
}