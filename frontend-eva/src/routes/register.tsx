import { createFileRoute, useNavigate, Link } from '@tanstack/react-router';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { TextField, Button, Box, Typography, Alert, Card, Avatar } from '@mui/material';
import PersonAddOutlinedIcon from '@mui/icons-material/PersonAddOutlined';
import { registerSchema, RegisterData } from '../features/auth/api';
import { useRegister } from '../features/auth/hooks';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';

export const Route = createFileRoute('/register')({
  component: Register,
});

function Register() {
  const registerMutation = useRegister();
  const navigate = useNavigate();
  const { t } = useTranslation();
  
  const { register, handleSubmit, formState: { errors } } = useForm<RegisterData>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = (data: RegisterData) => {
    registerMutation.mutate(data, {
      onSuccess: () => navigate({ to: '/login' }),
    });
  };

  return (
    <Box sx={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'radial-gradient(circle at top left, #1e293b 0%, #0f172a 100%)',
      p: 2
    }}>
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        <Card sx={{
          maxWidth: 450, width: '100%', p: { xs: 3, sm: 5 }, borderRadius: 6,
          background: 'rgba(30, 41, 59, 0.7)', backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255,255,255,0.1)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
        }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
            <Avatar sx={{ m: 1, bgcolor: '#6366f1', width: 64, height: 64, boxShadow: '0 8px 16px rgba(99,102,241,0.3)' }}>
              <PersonAddOutlinedIcon fontSize="large" sx={{ color: 'white' }} />
            </Avatar>
            <Typography component="h1" variant="h4" sx={{ fontWeight: 800, mt: 1, color: '#f8fafc', textAlign: 'center' }}>
              {t('register_title')}
            </Typography>
            <Typography variant="body2" sx={{ color: '#94a3b8', mt: 1, textAlign: 'center' }}>
              {t('register_subtitle')}
            </Typography>
          </Box>

          {registerMutation.isError && (
            <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
              {t('register_error')}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit(onSubmit)}>
            <TextField
              margin="normal"
              fullWidth
              label={t('register_username')}
              {...register('display_name')}
              error={!!errors.display_name}
              helperText={errors.display_name?.message}
              sx={{ mb: 2, '& .MuiOutlinedInput-root': { color: 'white', '& fieldset': { borderColor: 'rgba(255,255,255,0.2)' } }, '& .MuiInputLabel-root': { color: '#94a3b8' } }}
            />
            <TextField
              margin="normal"
              fullWidth
              label={t('login_email')}
              autoComplete="email"
              {...register('email')}
              error={!!errors.email}
              helperText={errors.email?.message}
              sx={{ mb: 2, '& .MuiOutlinedInput-root': { color: 'white', '& fieldset': { borderColor: 'rgba(255,255,255,0.2)' } }, '& .MuiInputLabel-root': { color: '#94a3b8' } }}
            />
            <TextField
              margin="normal"
              fullWidth
              label={t('login_password')}
              type="password"
              autoComplete="new-password"
              {...register('password')}
              error={!!errors.password}
              helperText={errors.password?.message}
              sx={{ mb: 4, '& .MuiOutlinedInput-root': { color: 'white', '& fieldset': { borderColor: 'rgba(255,255,255,0.2)' } }, '& .MuiInputLabel-root': { color: '#94a3b8' } }}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={registerMutation.isPending}
              sx={{
                py: 1.5,
                fontWeight: 700,
                fontSize: '1rem',
                backgroundImage: 'linear-gradient(90deg, #6366f1 0%, #ec4899 100%)',
                border: 0,
                borderRadius: 3,
                textTransform: 'none',
                boxShadow: '0 8px 16px rgba(99,102,241,0.3)',
                '&:hover': {
                  boxShadow: '0 12px 20px rgba(99,102,241,0.5)',
                }
              }}
            >
              {registerMutation.isPending ? t('register_btn_pending') : t('register_btn')}
            </Button>

            <Box sx={{ mt: 3, textAlign: 'center' }}>
              <Link to="/login" style={{ textDecoration: 'none', color: '#818cf8', fontWeight: 600 }}>
                {t('register_has_account')}
              </Link>
            </Box>
          </Box>
        </Card>
      </motion.div>
    </Box>
  );
}