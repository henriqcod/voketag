"use client";

import dynamic from "next/dynamic";
import { Suspense } from "react";

// HIGH SECURITY FIX: Lazy load ScanForm to reduce initial bundle size
// This improves Time to Interactive (TTI) by deferring non-critical JS
const ScanForm = dynamic(
  () => import("@/components/ScanForm").then((mod) => ({ default: mod.ScanForm })),
  {
    loading: () => (
      <div className="max-w-md mx-auto p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
        </div>
      </div>
    ),
    ssr: false, // Client-side only (uses hooks and state)
  }
);

export default function ScanPage() {
  return (
    <main className="container mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Escanear Tag</h1>
      <p className="text-gray-600 mb-8">
        Digite o ID da tag NFC para verificar a autenticidade do produto.
      </p>
      <Suspense
        fallback={
          <div className="text-center text-gray-500">Carregando formulário...</div>
        }
      >
        <ScanForm />
      </Suspense>
    </main>
  );
}
