import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "LiDAR Point Cloud Visualizer",
  description: "Visualizador en tiempo real de nubes de puntos LiDAR. Herramienta para visualización y análisis de datos capturados por sensores LiDAR.",
  keywords: ["LiDAR", "Point Cloud", "3D Visualization", "USAC", "Facultad de Ingeniería"],
  authors: [{ name: "USAC - Facultad de Ingeniería" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
