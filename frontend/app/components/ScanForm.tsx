"use client";

import { useState } from "react";
import { useScan } from "@/hooks/useScan";

export function ScanForm() {
  const [tagId, setTagId] = useState("");
  const { scanTag, loading, error, result } = useScan();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!tagId.trim()) return;
    await scanTag(tagId);
  };

  return (
    <div className="max-w-md mx-auto p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="tagId" className="block text-sm font-medium text-gray-700 mb-1">
            Tag ID
          </label>
          <input
            id="tagId"
            type="text"
            value={tagId}
            onChange={(e) => setTagId(e.target.value)}
            placeholder="Digite o ID da tag"
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={loading}
          />
        </div>
        <button
          type="submit"
          disabled={loading || !tagId.trim()}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? "Escaneando..." : "Escanear"}
        </button>
      </form>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {result && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-md">
          <h3 className="text-lg font-semibold text-green-900 mb-2">Resultado</h3>
          <dl className="space-y-1 text-sm">
            <div>
              <dt className="inline font-medium">Válido:</dt>
              <dd className="inline ml-2">{result.valid ? "Sim" : "Não"}</dd>
            </div>
            <div>
              <dt className="inline font-medium">Produto:</dt>
              <dd className="inline ml-2">{result.product_id}</dd>
            </div>
            <div>
              <dt className="inline font-medium">Lote:</dt>
              <dd className="inline ml-2">{result.batch_id}</dd>
            </div>
            <div>
              <dt className="inline font-medium">Scans:</dt>
              <dd className="inline ml-2">{result.scan_count}</dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  );
}
