"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function ConditionalNav() {
  const pathname = usePathname();
  if (pathname === "/scan") return null;
  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-6">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <Link href="/" className="text-xl font-bold text-blue-600">
              VokeTag
            </Link>
            <div className="hidden md:flex space-x-6">
              <Link href="/scan" className="text-gray-600 hover:text-gray-900 transition-colors">
                Escanear
              </Link>
              <Link href="/products" className="text-gray-600 hover:text-gray-900 transition-colors">
                Produtos
              </Link>
              <Link href="/batches" className="text-gray-600 hover:text-gray-900 transition-colors">
                Lotes
              </Link>
              <Link href="/dashboard" className="text-gray-600 hover:text-gray-900 transition-colors">
                Dashboard
              </Link>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">Ambiente: Desenvolvimento</span>
          </div>
        </div>
      </div>
    </nav>
  );
}
