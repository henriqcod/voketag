import { Inter } from "next/font/google";
import { ConditionalNav } from "@/components/ConditionalNav";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata = {
  title: "VokeTag - Autenticação de Produtos",
  description: "Sistema de autenticação de produtos com tecnologia NFC",
  manifest: "/manifest.json",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR" className={inter.variable}>
      <body className="bg-gray-50 min-h-screen font-sans">
        <ConditionalNav />
        <div className="min-h-screen">
          {children}
        </div>
      </body>
    </html>
  );
}
