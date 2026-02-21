import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VokeTag Admin",
  description: "VokeTag Admin GOD MODE",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className="bg-[#0f172a] text-[#f8fafc] antialiased">
        {children}
      </body>
    </html>
  );
}
