import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { theme } from './theme';

// Configuración global del estado del servidor
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3, // 3 reintentos por consulta para fallos transitorios [cite: 893]
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: false, // Sin reintento automático en operaciones de escritura [cite: 894]
    },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        {/* CssBaseline normaliza los estilos en todos los navegadores */}
        <CssBaseline />
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );
}