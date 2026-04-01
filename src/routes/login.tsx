import { createFileRoute, useNavigate, Link } from '@tanstack/react-router';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { TextField, Button, Box, Typography, Container, Alert, Card, Avatar } from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
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
    defaultValues: {
      email: 'demo@eva.com',
      password: 'demo_password123'
    }
  });

  const onSubmit = (data: LoginData) => {
    loginMutation.mutate(data, {
      onSuccess: () => navigate({ to: '/dashboard' }),
    });
  };

  return (
    <Box sx={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'radial-gradient(circle at top right, #1e293b 0%, #0f172a 100%)',
      p: 2
    }}>
      <Card sx={{
        maxWidth: 400, width: '100%', p: 4, borderRadius: 4,
        background: 'rgba(30, 41, 59, 0.7)', backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
      }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 4 }}>
          <Avatar sx={{ m: 1, bgcolor: '#ec4899', width: 56, height: 56 }}>
            <LockOutlinedIcon fontSize="large" sx={{ color: 'white' }} />
          </Avatar>
          <Typography component="h1" variant="h4" sx={{ fontWeight: 800, mt: 1, color: '#f8fafc' }}>
            Bienvenido de nuevo
          </Typography>
          <Typography variant="body2" sx={{ color: '#94a3b8', mt: 1 }}>
            Inicia sesión para acceder a Eva Learning
          </Typography>
        </Box>

        {loginMutation.isError && (
          <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
            Credenciales inválidas o error de conexión.
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit(onSubmit)}>
          <TextField
            margin="normal"
            fullWidth
            label="Correo Electrónico"
            autoComplete="email"
            {...register('email')}
            error={!!errors.email}
            helperText={errors.email?.message}
            sx={{ mb: 2 }}
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
            sx={{ mb: 4 }}
          />
          
          <Button
            type="submit"
            fullWidth
            variant="contained"
            disabled={loginMutation.isPending}
            sx={{
              py: 1.5,
              fontWeight: 700,
              fontSize: '1rem',
              backgroundImage: 'linear-gradient(90deg, #6366f1 0%, #ec4899 100%)',
              border: 0,
              boxShadow: '0 8px 16px rgba(236,72,153,0.3)',
              '&:hover': {
                boxShadow: '0 12px 20px rgba(236,72,153,0.5)',
              }
            }}
          >
            {loginMutation.isPending ? 'Autenticando...' : 'Entrar'}
          </Button>

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Link to="/register" style={{ textDecoration: 'none', color: '#818cf8', fontWeight: 600 }}>
              {"¿No tienes una cuenta? Regístrate"}
            </Link>
          </Box>
        </Box>
      </Card>
    </Box>
  );
}