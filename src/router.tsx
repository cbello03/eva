import { createRootRoute, createRoute, createRouter, Outlet } from '@tanstack/react-router';
import { Box } from '@mui/material';

// 1. Importación de Componentes
import App from './App';
import LoginPage from './features/accounts/LoginPage'; 
import { StudentDashboard } from './features/courses/StudentDashboard';
import { Navbar } from './components/Navbar'; 

// 2. Configuración del "Molde" Principal
const rootRoute = createRootRoute({
  component: () => (
    <Box sx={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
      <Navbar />
      <Box sx={{ p: 3 }}>
        <Outlet /> 
      </Box>
    </Box>
  ),
});

// 3. Definición de las Rutas
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: App,
});

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: LoginPage, 
});

const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/dashboard',
  component: StudentDashboard,
});

// 4. Armado del Árbol de Rutas
const routeTree = rootRoute.addChildren([
  indexRoute,
  loginRoute,
  dashboardRoute,
]);

// 5. Creación del Router
export const router = createRouter({ routeTree });

// 6. Registro de Tipos
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}