import { Inter } from 'next/font/google';

// Sprint 7-8: web pública SEO con silos de catálogo
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es-MX">
      <body className={Inter().className}>{children}</body>
    </html>
  );
}
