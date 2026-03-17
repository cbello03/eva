import type { ReactNode } from "react";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import evaTheme from "./theme";

/**
 * Top-level provider wrapper for the EVA application.
 *
 * Wraps children with:
 * - MUI ThemeProvider (custom EVA theme)
 * - CssBaseline (normalize browser defaults)
 *
 * Note: TanStack Query provider is already set up in
 * `src/integrations/tanstack-query/root-provider.tsx` and
 * composed in `__root.tsx`. This provider is meant to be
 * nested inside or alongside that existing setup.
 */
export default function EvaProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider theme={evaTheme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
}
