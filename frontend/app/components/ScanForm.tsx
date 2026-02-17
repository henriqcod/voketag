"use client";

import { useState } from "react";
import { useScan } from "@/hooks/useScan";
import { isValidUUID, sanitizeHTML } from "@/lib/sanitize";

export function ScanForm() {
  const [tagId, setTagId] = useState("");
  const [validationError, setValidationError] = useState("");
  const { scanTag, loading, error, result } = useScan();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // HIGH SECURITY FIX: Comprehensive input validation
    const trimmed = tagId.trim();
    
    // Reset validation error
    setValidationError("");
    
    // Validation 1: Required field
    if (!trimmed) {
      setValidationError("Tag ID é obrigatório");
      return;
    }
    
    // Validation 2: Length check (UUID is 36 chars with dashes)
    if (trimmed.length !== 36) {
      setValidationError("Tag ID deve ter 36 caracteres (formato UUID)");
      return;
    }
    
    // Validation 3: UUID format
    if (!isValidUUID(trimmed)) {
      setValidationError("Tag ID deve ser um UUID válido (ex: 123e4567-e89b-12d3-a456-426614174000)");
      return;
    }
    
    // Validation 4: Sanitize to prevent XSS
    const sanitized = sanitizeHTML(trimmed);
    if (sanitized !== trimmed) {
      setValidationError("Tag ID contém caracteres inválidos");
      return;
    }
    
    // All validations passed, proceed with scan
    await scanTag(sanitized);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setTagId(value);
    
    // Clear validation error on input change
    if (validationError) {
      setValidationError("");
    }
  };

  return (
    <div className="max-w-md mx-auto p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="tagId" className="block text-sm font-medium text-gray-700 mb-1">
            Tag ID (UUID)
          </label>
          <input
            id="tagId"
            type="text"
            value={tagId}
            onChange={handleInputChange}
            placeholder="123e4567-e89b-12d3-a456-426614174000"
            pattern="[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
            maxLength={36}
            className={`w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              validationError ? "border-red-500" : "border-gray-300"
            }`}
            disabled={loading}
            aria-invalid={!!validationError}
            aria-describedby={validationError ? "tagId-error" : undefined}
          />
          {validationError && (
            <p id="tagId-error" className="mt-1 text-sm text-red-600" role="alert">
              {validationError}
            </p>
          )}
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
