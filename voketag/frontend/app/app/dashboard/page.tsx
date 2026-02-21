"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type DashboardStats = {
  total_users?: number;
  total_products?: number;
  total_scans?: number;
  total_batches?: number;
  total_anchors?: number;
  batches_completed?: number;
  batches_failed?: number;
  batches_pending?: number;
};

type UserItem = {
  id: string;
  email: string;
  full_name?: string;
  role?: string;
  is_active?: boolean;
  created_at?: string;
};

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentUsers, setRecentUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const res = await fetch("/api/dashboard");
        const data = await res.json();
        if (cancelled) return;
        if (data.stats) setStats(data.stats);
        if (Array.isArray(data.recentUsers)) setRecentUsers(data.recentUsers);
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
      <h1 style={{ fontSize: "2rem", fontWeight: "bold", marginBottom: "2rem" }}>
        Dashboard Administrativo
      </h1>

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
            Configure ADMIN_API_URL e ADMIN_JWT no .env.local para exibir dados do Admin.
          </span>
        </div>
      )}

      <div
        style={{
          display: "grid",
          gap: "1.5rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          marginBottom: "2rem",
        }}
      >
        <div style={cardStyle}>
          <p style={{ fontSize: "0.875rem", color: "#666", marginBottom: "0.5rem" }}>
            Total de Usuários
          </p>
          <p style={{ fontSize: "2rem", fontWeight: "bold", color: "#2563eb" }}>
            {loading ? "—" : (stats?.total_users ?? 0)}
          </p>
        </div>
        <div style={cardStyle}>
          <p style={{ fontSize: "0.875rem", color: "#666", marginBottom: "0.5rem" }}>
            Total de Produtos
          </p>
          <p style={{ fontSize: "2rem", fontWeight: "bold", color: "#16a34a" }}>
            {loading ? "—" : (stats?.total_products ?? 0)}
          </p>
        </div>
        <div style={cardStyle}>
          <p style={{ fontSize: "0.875rem", color: "#666", marginBottom: "0.5rem" }}>
            Total de Scans
          </p>
          <p style={{ fontSize: "2rem", fontWeight: "bold", color: "#7c3aed" }}>
            {loading ? "—" : (stats?.total_scans ?? 0)}
          </p>
        </div>
        <div style={cardStyle}>
          <p style={{ fontSize: "0.875rem", color: "#666", marginBottom: "0.5rem" }}>
            Total de Lotes
          </p>
          <p style={{ fontSize: "2rem", fontWeight: "bold", color: "#ea580c" }}>
            {loading ? "—" : (stats?.total_batches ?? 0)}
          </p>
        </div>
      </div>

      <div
        style={{
          padding: "1.5rem",
          backgroundColor: "white",
          border: "1px solid #e5e7eb",
          borderRadius: "0.5rem",
          boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
        }}
      >
        <h2 style={{ fontSize: "1.25rem", fontWeight: "600", marginBottom: "1rem" }}>
          Usuários Recentes
        </h2>
        {loading ? (
          <p style={{ color: "#666" }}>Carregando...</p>
        ) : recentUsers.length === 0 ? (
          <p style={{ color: "#666" }}>Nenhum usuário encontrado no momento.</p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {recentUsers.map((u) => (
              <li
                key={u.id}
                style={{
                  padding: "0.5rem 0",
                  borderBottom: "1px solid #f3f4f6",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span>
                  <strong>{u.email}</strong>
                  {u.full_name && ` — ${u.full_name}`}
                </span>
                <span style={{ fontSize: "0.875rem", color: "#6b7280" }}>{u.role ?? "—"}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <p style={{ marginTop: "2rem", fontSize: "0.875rem", color: "#6b7280" }}>
        <Link href="/" style={{ color: "#2563eb" }}>
          ← Voltar ao início
        </Link>
      </p>
    </main>
  );
}
