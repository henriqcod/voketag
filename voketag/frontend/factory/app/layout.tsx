import type { Metadata } from "next";
import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "VokeTag Factory Portal",
  description: "Portal da Fábrica Premium — Registro e validação industrial",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){var t=localStorage.getItem('voketag_theme');if(t==='dark')document.documentElement.classList.add('dark');else if(t!=='light')document.documentElement.classList.remove('dark');})()`,
          }}
        />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
