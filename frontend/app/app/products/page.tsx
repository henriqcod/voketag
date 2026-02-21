"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type ProductItem = {
  id: string;
  name?: string;
  category?: string;
  serial_number?: string;
  token?: string;
  verification_url?: string;
  created_at?: string;
  batch_id?: string;
};

export default function ProductsPage() {
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const res = await fetch("/api/products?limit=50");
        const data = await res.json();
        if (cancelled) return;
        if (Array.isArray(data.products)) setProducts(data.products);
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
        <h1 style={{ fontSize: "2rem", fontWeight: "bold" }}>Produtos</h1>
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
            Configure FACTORY_API_URL e FACTORY_JWT no .env.local para exibir produtos.
          </span>
        </div>
      )}

      {loading ? (
        <p style={{ color: "#666" }}>Carregando produtos...</p>
      ) : products.length === 0 ? (
        <p style={{ color: "#666" }}>Nenhum produto encontrado.</p>
      ) : (
        <div
          style={{
            display: "grid",
            gap: "1rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          }}
        >
          {products.map((p) => (
            <div key={p.id} style={cardStyle}>
              <h3 style={{ fontSize: "1.125rem", fontWeight: "600", marginBottom: "0.5rem" }}>
                {p.name || `Produto ${p.id.slice(0, 8)}…`}
              </h3>
              <p style={{ color: "#666", marginBottom: "0.5rem" }}>
                {p.category ? `Categoria: ${p.category}` : "—"}
                {p.serial_number ? ` • S/N: ${p.serial_number}` : ""}
              </p>
              <p style={{ fontSize: "0.75rem", color: "#999" }}>
                Criado em:{" "}
                {p.created_at ? new Date(p.created_at).toLocaleString("pt-BR") : "—"}
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
