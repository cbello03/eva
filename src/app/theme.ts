import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // Azul principal
    },
    secondary: {
      main: '#dc004e', // Color secundario
    },
    background: {
      default: '#f4f6f8',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});