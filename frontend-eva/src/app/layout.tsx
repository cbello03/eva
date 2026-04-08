import type { Metadata } from "next";
import { Suspense } from "react";
import { Providers } from "@/lib/providers";
import NavigationBar from "@/components/NavigationBar";
import "./globals.css";

export const metadata: Metadata = {
  title: "EVA — Learning Platform",
  description: "Entorno Virtual de Enseñanza-Aprendizaje",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <NavigationBar />
          <Suspense
            fallback={
              <div style={{ display: "flex", justifyContent: "center", padding: "4rem" }}>
                Loading…
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
