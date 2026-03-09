import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Shipment Tracker - Charcoal Intelligence',
  description:
    'Real-time charcoal shipment tracking with 3D globe visualization, risk zone monitoring, and alert management.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        {/*
          Preconnect to Mapbox tile servers for faster globe loading.
          The Mapbox GL CSS is imported via globals.css.
        */}
        <link rel="preconnect" href="https://api.mapbox.com" />
        <link rel="preconnect" href="https://events.mapbox.com" />
      </head>
      <body className="h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 antialiased">
        {children}
      </body>
    </html>
  );
}
