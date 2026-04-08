"use client";

import { createTheme } from "@mui/material/styles";

declare module "@mui/material/styles" {
  interface Palette {
    streak: Palette["primary"];
    xp: Palette["primary"];
  }
  interface PaletteOptions {
    streak?: PaletteOptions["primary"];
    xp?: PaletteOptions["primary"];
  }
}

const theme = createTheme({
  palette: {
    primary: {
      main: "#6C5CE7",
      light: "#A29BFE",
      dark: "#4A3DB8",
      contrastText: "#FFFFFF",
    },
    secondary: {
      main: "#00B894",
      light: "#55EFC4",
      dark: "#00896E",
      contrastText: "#FFFFFF",
    },
    streak: {
      main: "#FF6B6B",
      light: "#FF8E8E",
      dark: "#E05555",
      contrastText: "#FFFFFF",
    },
    xp: {
      main: "#FDCB6E",
      light: "#FFEAA7",
      dark: "#E0B04E",
      contrastText: "#2D3436",
    },
    background: {
      default: "#FAFAFA",
      paper: "#FFFFFF",
    },
    text: {
      primary: "#2D3436",
      secondary: "#636E72",
    },
  },
  typography: {
    fontFamily: "'Manrope', sans-serif",
    h1: { fontFamily: "'Fraunces', serif", fontWeight: 700 },
    h2: { fontFamily: "'Fraunces', serif", fontWeight: 700 },
    h3: { fontFamily: "'Fraunces', serif", fontWeight: 600 },
    h4: { fontFamily: "'Fraunces', serif", fontWeight: 600 },
    h5: { fontFamily: "'Fraunces', serif", fontWeight: 500 },
    h6: { fontFamily: "'Fraunces', serif", fontWeight: 500 },
    button: { textTransform: "none", fontWeight: 600 },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: "8px 20px",
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
        },
      },
    },
  },
});

export default theme;
