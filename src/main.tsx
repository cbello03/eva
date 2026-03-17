import React from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider } from '@tanstack/react-router'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query' // 1. Importamos esto
import { router } from './router'
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material'

// 2. Creamos el cliente de Query
const queryClient = new QueryClient()

const theme = createTheme({
  palette: {
    primary: { main: '#2e7d32' }, // El verde de EVA
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}> {/* 3. Envolvemos la app */}
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <RouterProvider router={router} />
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)