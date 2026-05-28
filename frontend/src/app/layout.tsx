import type { Metadata } from 'next';
import { Roboto } from 'next/font/google';
import './globals.css';
import Sidebar from '@/components/layout/Sidebar';

const roboto = Roboto({
  subsets: ['latin'],
  weight: ['300', '400', '500', '700', '900'],
  variable: '--font-roboto',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'ProMundial — Análisis IA Mundial 2026',
  description: 'Panel de análisis inteligente del Mundial FIFA 2026 con predicciones AI, seguimiento de resultados y estadísticas en tiempo real.',
  icons: {
    icon: '/logo.png',
    apple: '/logo.png',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" className="dark">
      <body className={`${roboto.variable} font-sans antialiased`}>
        <Sidebar />
        <main className="lg:ml-64 min-h-screen relative z-10">
          <div className="p-4 sm:p-6 lg:p-8 pt-16 lg:pt-8">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}
