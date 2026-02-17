"use client";

import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <Link href="/" className="text-xl font-bold text-gray-900">
              VokeTag
            </Link>
            <nav className="flex space-x-4">
              <Link
                href="/scan"
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                Escanear
              </Link>
              {user && (
                <>
                  <Link
                    href="/dashboard"
                    className="text-gray-600 hover:text-gray-900 transition-colors"
                  >
                    Dashboard
                  </Link>
                  <Link
                    href="/products"
                    className="text-gray-600 hover:text-gray-900 transition-colors"
                  >
                    Produtos
                  </Link>
                  <Link
                    href="/batches"
                    className="text-gray-600 hover:text-gray-900 transition-colors"
                  >
                    Lotes
                  </Link>
                </>
              )}
            </nav>
          </div>
          <div>
            {user ? (
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-600">{user.email}</span>
                <button
                  onClick={logout}
                  className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
                >
                  Sair
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                Entrar
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
