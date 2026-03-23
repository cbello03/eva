import { createFileRoute, useNavigate, Link } from '@tanstack/react-router'; // <-- Importamos Link
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { TextField, Button, Box, Typography, Container, Alert, Grid } from '@mui/material'; // <-- Importamos Grid
import { loginSchema, LoginData } from '../features/auth/api';
import { useLogin } from '../features/auth/hooks';

export const Route = createFileRoute('/login')({
  component: Login,
});

function Login() {
  const loginMutation = useLogin();
  const navigate = useNavigate();
  
  const { register, handleSubmit, formState: { errors } } = useForm<LoginData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = (data: LoginData) => {
    loginMutation.mutate(data, {
      onSuccess: () => navigate({ to: '/dashboard' }),
    });
  };

  return (
    <Container maxWidth="xs">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Typography component="h1" variant="h5">
          Iniciar Sesión en EVA
        </Typography>
        
        {loginMutation.isError && (
          <Alert severity="error" sx={{ mt: 2, width: '100%' }}>
            Credenciales inválidas o error de conexión.
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ mt: 1 }}>
          <TextField
            margin="normal"
            fullWidth
            label="Correo Electrónico"
            autoComplete="email"
            {...register('email')}
            error={!!errors.email}
            helperText={errors.email?.message}
          />
          <TextField
            margin="normal"
            fullWidth
            label="Contraseña"
            type="password"
            autoComplete="current-password"
            {...register('password')}
            error={!!errors.password}
            helperText={errors.password?.message}
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={loginMutation.isPending}
          >
            {loginMutation.isPending ? 'Cargando...' : 'Entrar'}
          </Button>
          
          {/* Aquí agregamos el enlace hacia el Registro */}
          <Grid container justifyContent="flex-end">
            <Grid item>
              <Link to="/register" style={{ textDecoration: 'none', color: '#1976d2' }}>
                {"¿No tienes una cuenta? Regístrate"}
              </Link>
            </Grid>
          </Grid>

        </Box>
      </Box>
    </Container>
  );
}