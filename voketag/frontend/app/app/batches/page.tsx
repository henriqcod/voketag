"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type BatchItem = {
  id: string;
  product_count: number;
  status: string;
  created_at: string;
  blockchain_tx?: string;
  merkle_root?: string;
};

export default function BatchesPage() {
  const [batches, setBatches] = useState<BatchItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const res = await fetch("/api/batches?limit=50");
        const data = await res.json();
        if (cancelled) return;
        if (Array.isArray(data.batches)) setBatches(data.batches);
        if (data.error) setError(data.error);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Erro ao carregar");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const statusLabel: Record<string, string> = {
    pending: "Pendente",
    processing: "Processando",
    anchoring: "Ancorando",
    completed: "Concluído",
    failed: "Falhou",
    anchor_failed: "Falha na âncora",
  };

  const cardStyle = {
    padding: "1.5rem",
    backgroundColor: "white",
    border: "1px solid #e5e7eb",
    borderRadius: "0.5rem",
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
  };

  return (
    <main style={{ maxWidth: "800px", margin: "0 auto", padding: "2rem" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "2rem",
        }}
      >
        <h1 style={{ fontSize: "2rem", fontWeight: "bold" }}>Lotes</h1>
      </div>

      {error && (
        <div
          style={{
            padding: "1rem",
            backgroundColor: "#fef2f2",
            border: "1px solid #fecaca",
            borderRadius: "0.375rem",
            marginBottom: "2rem",
            color: "#991b1b",
            fontSize: "0.875rem",
          }}
        >
          {error}
          <br />
          <span style={{ opacity: 0.9 }}>
            Configure FACTORY_API_URL e FACTORY_JWT no .env.local para exibir lotes.
          </span>
        </div>
      )}

      {loading ? (
        <p style={{ color: "#666" }}>Carregando lotes...</p>
      ) : batches.length === 0 ? (
        <p style={{ color: "#666" }}>Nenhum lote encontrado.</p>
      ) : (
        <div
          style={{
            display: "grid",
            gap: "1rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          }}
        >
          {batches.map((batch) => (
            <div key={batch.id} style={cardStyle}>
              <h3 style={{ fontSize: "1.125rem", fontWeight: "600", marginBottom: "0.5rem" }}>
                Lote {batch.id.slice(0, 8)}…
              </h3>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "0.5rem",
                }}
              >
                <span style={{ fontSize: "0.875rem", color: "#666" }}>Quantidade:</span>
                <span style={{ fontWeight: "500", color: "#2563eb" }}>{batch.product_count}</span>
              </div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "0.5rem",
                }}
              >
                <span style={{ fontSize: "0.875rem", color: "#666" }}>Status:</span>
                <span style={{ fontWeight: "500" }}>{statusLabel[batch.status] ?? batch.status}</span>
              </div>
              <p style={{ fontSize: "0.75rem", color: "#999" }}>
                Criado em:{" "}
                {batch.created_at
                  ? new Date(batch.created_at).toLocaleString("pt-BR")
                  : "—"}
              </p>
            </div>
          ))}
        </div>
      )}

      <p style={{ marginTop: "2rem", fontSize: "0.875rem", color: "#6b7280" }}>
        <Link href="/" style={{ color: "#2563eb" }}>
          ← Voltar ao início
        </Link>
      </p>
    </main>
  );
}
