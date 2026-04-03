import React, { Suspense } from 'react';
import { Outlet, createRootRoute } from '@tanstack/react-router';
import { Box, CircularProgress } from '@mui/material';
import { Layout } from '../components/Layout';

import { useAuthStore } from '../features/auth/store';

export const Route = createRootRoute({
  component: function RootComponent() {
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
    
    return (
      <Suspense fallback={<Box display="flex" justifyContent="center" alignItems="center" height="100vh"><CircularProgress /></Box>}>
        {isAuthenticated ? <Layout /> : <Outlet />}
      </Suspense>
    );
  },
});