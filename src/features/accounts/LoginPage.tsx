import { Container, Paper, Typography, Box } from '@mui/material';
import { LoginForm } from './LoginForm';

const LoginPage = () => {
  return (
    <Container maxWidth="xs">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Paper elevation={6} sx={{ p: 4, width: '100%', borderRadius: 3 }}>
          <Typography variant="h5" align="center" sx={{ fontWeight: 'bold', mb: 2 }}>
            Iniciar Sesión en EVA
          </Typography>
          <LoginForm />
        </Paper>
      </Box>
    </Container>
  );
};

export default LoginPage; // <-- Esto es vital para que el Router lo encuentre