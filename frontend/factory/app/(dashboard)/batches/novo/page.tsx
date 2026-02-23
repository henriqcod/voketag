"use client";

import { BatchUploadForm } from "@/components/factory/BatchUploadForm";

export default function NovoLotePage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-graphite-900 dark:text-white">
          Novo Lote
        </h1>
        <p className="mt-1 text-sm text-graphite-500 dark:text-graphite-400">
          Registre um novo lote de produtos com UUIDs em CSV.
        </p>
      </div>
      <BatchUploadForm />
    </div>
  );
}
