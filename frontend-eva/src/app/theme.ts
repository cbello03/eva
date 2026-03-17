import { createTheme } from "@mui/material/styles";

/**
 * EVA platform custom MUI theme.
 * Colors are derived from the existing CSS custom properties
 * to keep visual consistency with the Tailwind-based styles.
 */
const evaTheme = createTheme({
  palette: {
    primary: {
      main: "#328f97", // --lagoon-deep
      light: "#4fb8b2", // --lagoon
      dark: "#173a40", // --sea-ink
      contrastText: "#ffffff",
    },
    secondary: {
      main: "#2f6a4a", // --palm
      light: "#6ec89a",
      dark: "#1a4a30",
      contrastText: "#ffffff",
    },
    background: {
      default: "#e7f3ec", // --bg-base
      paper: "#f3faf5", // --foam
    },
    text: {
      primary: "#173a40", // --sea-ink
      secondary: "#416166", // --sea-ink-soft
    },
  },
  typography: {
    fontFamily: '"Manrope", ui-sans-serif, system-ui, sans-serif',
    h1: { fontFamily: '"Fraunces", Georgia, serif' },
    h2: { fontFamily: '"Fraunces", Georgia, serif' },
    h3: { fontFamily: '"Fraunces", Georgia, serif' },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: 600,
        },
      },
    },
    MuiCssBaseline: {
      styleOverrides: {
        // Let the existing global CSS handle base styles
        body: { margin: 0 },
      },
    },
  },
});

export default evaTheme;
