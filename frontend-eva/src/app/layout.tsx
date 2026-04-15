import type { Metadata } from "next";
import { Suspense } from "react";
import { Providers } from "@/lib/providers";
import NavigationBar from "@/components/NavigationBar";
import "./globals.css";

export const metadata: Metadata = {
  title: "EVA — Plataforma de Aprendizaje",
  description: "Entorno Virtual de Enseñanza-Aprendizaje",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body suppressHydrationWarning>
        <Providers>
          <NavigationBar />
          <Suspense
            fallback={
              <div style={{ display: "flex", justifyContent: "center", padding: "4rem" }}>
                Cargando…
              </div>
            }
          >
            {children}
          </Suspense>
        </Providers>
      </body>
    </html>
  );
}
