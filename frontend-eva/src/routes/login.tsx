import { createFileRoute, useNavigate, Link, Navigate } from '@tanstack/react-router';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { TextField, Button, Box, Typography, Alert, Avatar } from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { loginSchema, LoginData } from '../features/auth/api';
import { useLogin } from '../features/auth/hooks';
import { useAuthStore } from '../features/auth/store';

export const Route = createFileRoute('/login')({
  component: Login,
});

function Login() {
  const loginMutation = useLogin();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  
  const { register, handleSubmit, formState: { errors } } = useForm<LoginData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = (data: LoginData) => {
    loginMutation.mutate(data, {
      onSuccess: () => navigate({ to: '/dashboard' }),
    });
  };

  if (isAuthenticated) {
    return <Navigate to="/dashboard" />;
  }

  return (
    <Box sx={{
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      position: 'relative',
      overflow: 'hidden',
      backgroundColor: '#0f172a',
      p: 2
    }}>
      {/* Animated Background Elements */}
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        style={{
          position: 'absolute',
          top: '-10%',
          left: '-10%',
          width: '50vw',
          height: '50vw',
          background: 'radial-gradient(circle, rgba(99,102,241,0.4) 0%, rgba(15,23,42,0) 70%)',
          borderRadius: '50%',
          zIndex: 0
        }}
      />
      
      <motion.div
        animate={{
          scale: [1, 1.5, 1],
          opacity: [0.2, 0.4, 0.2],
        }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 1 }}
        style={{
          position: 'absolute',
          bottom: '-20%',
          right: '-10%',
          width: '60vw',
          height: '60vw',
          background: 'radial-gradient(circle, rgba(236,72,153,0.3) 0%, rgba(15,23,42,0) 70%)',
          borderRadius: '50%',
          zIndex: 0
        }}
      />

      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        style={{ zIndex: 1, width: '100%', maxWidth: '420px' }}
      >
        <Box sx={{
          width: '100%', 
          p: { xs: 3, sm: 5 }, 
          borderRadius: 6,
          background: 'rgba(30, 41, 59, 0.6)', 
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255,255,255,0.08)',
          boxShadow: '0 30px 60px -12px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255,255,255,0.1)'
        }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 4 }}>
            <motion.div whileHover={{ scale: 1.1, rotate: 5 }} whileTap={{ scale: 0.9 }}>
              <Avatar sx={{ 
                m: 1, 
                background: 'linear-gradient(135deg, #6366f1 0%, #ec4899 100%)',
                width: 64, 
                height: 64,
                boxShadow: '0 8px 16px rgba(236,72,153,0.4)',
                mb: 2
              }}>
                <LockOutlinedIcon fontSize="large" sx={{ color: 'white' }} />
              </Avatar>
            </motion.div>
            
            <Typography component="h1" variant="h4" sx={{ fontWeight: 800, mt: 1, color: '#f8fafc', textAlign: 'center' }}>
              {t('login_title')}
            </Typography>
            <Typography variant="body1" sx={{ color: '#94a3b8', mt: 1, textAlign: 'center' }}>
              {t('login_subtitle')}
            </Typography>
          </Box>

          {loginMutation.isError && (
            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}>
              <Alert severity="error" sx={{ 
                mb: 3, 
                borderRadius: 2, 
                background: 'rgba(239,68,68,0.1)', 
                color: '#fca5a5',
                border: '1px solid rgba(239,68,68,0.3)',
                '& .MuiAlert-icon': { color: '#fca5a5' }
              }}>
                {t('login_invalid')}
              </Alert>
            </motion.div>
          )}

          <Box component="form" onSubmit={handleSubmit(onSubmit)}>
            <TextField
              margin="normal"
              fullWidth
              label={t('login_email')}
              autoComplete="email"
              {...register('email')}
              error={!!errors.email}
              helperText={errors.email?.message}
              variant="outlined"
              sx={{ 
                mb: 2,
                '& .MuiOutlinedInput-root': {
                  color: 'white',
                  background: 'rgba(15,23,42,0.4)',
                  borderRadius: 3,
                  '& fieldset': { borderColor: 'rgba(255,255,255,0.1)' },
                  '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.2)' },
                  '&.Mui-focused fieldset': { borderColor: '#818cf8', borderWidth: '2px' },
                },
                '& .MuiInputLabel-root': { color: '#94a3b8' },
                '& .MuiInputLabel-root.Mui-focused': { color: '#818cf8' },
              }}
            />
            <TextField
              margin="normal"
              fullWidth
              label={t('login_password')}
              type="password"
              autoComplete="current-password"
              {...register('password')}
              error={!!errors.password}
              helperText={errors.password?.message}
              sx={{ 
                mb: 4,
                '& .MuiOutlinedInput-root': {
                  color: 'white',
                  background: 'rgba(15,23,42,0.4)',
                  borderRadius: 3,
                  '& fieldset': { borderColor: 'rgba(255,255,255,0.1)' },
                  '&:hover fieldset': { borderColor: 'rgba(255,255,255,0.2)' },
                  '&.Mui-focused fieldset': { borderColor: '#818cf8', borderWidth: '2px' },
                },
                '& .MuiInputLabel-root': { color: '#94a3b8' },
                '& .MuiInputLabel-root.Mui-focused': { color: '#818cf8' },
              }}
            />
            
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={loginMutation.isPending}
                sx={{
                  py: 1.8,
                  borderRadius: 3,
                  fontWeight: 700,
                  fontSize: '1rem',
                  textTransform: 'none',
                  background: 'linear-gradient(135deg, #4f46e5 0%, #d946ef 100%)',
                  border: 0,
                  color: 'white',
                  boxShadow: '0 8px 20px -4px rgba(217,70,239,0.5)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #4338ca 0%, #c026d3 100%)',
                    boxShadow: '0 12px 25px -4px rgba(217,70,239,0.6)',
                  },
                  '&:disabled': {
                    background: 'rgba(255,255,255,0.1)',
                    color: 'rgba(255,255,255,0.3)',
                    boxShadow: 'none'
                  }
                }}
              >
                {loginMutation.isPending ? t('login_btn_pending') : t('login_btn')}
              </Button>
            </motion.div>

            <Box sx={{ mt: 4, textAlign: 'center' }}>
              <Link to="/register" style={{ textDecoration: 'none', color: '#a5b4fc', fontWeight: 600, fontSize: '0.95rem' }}>
                <motion.span whileHover={{ color: '#fff', textShadow: '0 0 8px rgba(255,255,255,0.4)' }} style={{ display: 'inline-block', transition: '0.2s' }}>
                  {t('login_no_account')}
                </motion.span>
              </Link>
            </Box>
          </Box>
        </Box>
      </motion.div>
    </Box>
  );
}