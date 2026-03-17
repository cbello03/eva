import { Container, Typography, Button, Paper, Box } from '@mui/material'
import { Link } from '@tanstack/react-router'
// 1. Importamos la "mochila" de Zustand
import { useAuthStore } from './store/auth-store' 

function App() {
  // 2. Extraemos el estado de autenticación y los datos del usuario
  const { isAuthenticated, user } = useAuthStore()

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Paper elevation={6} sx={{ p: 5, textAlign: 'center', borderRadius: 5 }}>
          <Typography variant="h3" sx={{ color: '#2e7d32', fontWeight: 'bold', mb: 2 }}>
            EVA
          </Typography>
          
          <Typography variant="h5" gutterBottom>
            Entorno Virtual de Aprendizaje
          </Typography>

          {/* 3. El texto cambiará automáticamente si el usuario está logueado */}
          <Typography variant="body1" sx={{ mb: 4 }}>
            {isAuthenticated 
              ? `Bienvenido, ${user?.full_name || 'Usuario'}` 
              : "¡El sistema de autenticación está listo!"}
          </Typography>

          {/* Este botón nos llevará a la ruta /login que crearemos luego */}
          <Button
            component={Link}
            to="/login"
            variant="contained"
            sx={{ backgroundColor: '#2e7d32' }}
          >
            {isAuthenticated ? "Ir al Dashboard" : "Ir al Login"}
          </Button>

          {/* 4. Mensaje de depuración para que SEPAS que funciona */}
          <Typography variant="caption" sx={{ display: 'block', mt: 3, color: 'gray' }}>
            Estado de Zustand: {isAuthenticated ? "Conectado ✅" : "Desconectado ❌"}
          </Typography>
        </Paper>
      </Box>
    </Container>
  )
}

export default App