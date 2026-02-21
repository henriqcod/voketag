"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { getDashboard, getSystemStatusExtended, type SystemStatusExtended } from "@/lib/api-client";

function StatCard({
  title,
  value,
  color,
}: {
  title: string;
  value: number | string;
  color: string;
}) {
  return (
    <Card>
      <p className="mb-1 text-xs text-[#94a3b8]">{title}</p>
      <p className="text-2xl font-bold" style={{ color }}>
        {value}
      </p>
    </Card>
  );
}

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (h >= 24) return `${Math.floor(h / 24)}d ${h % 24}h`;
  return `${h}h ${m}m`;
}

export default function DashboardPage() {
  const [dashboard, setDashboard] = useState<Record<string, unknown> | null>(null);
  const [extended, setExtended] = useState<SystemStatusExtended | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getDashboard(30), getSystemStatusExtended()])
      .then(([d, e]) => {
        setDashboard(d);
        setExtended(e);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Erro"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-[#94a3b8]">Carregando...</p>
      </div>
    );
  }

  const m24 = extended?.metrics_24h ?? {};

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-[#f8fafc]">Dashboard</h1>

      {error && (
        <div className="mb-6 rounded-lg border border-red-800 bg-red-900/30 p-4 text-red-300">
          {error}
        </div>
      )}

      {/* 24h metrics */}
      <h2 className="mb-3 text-sm font-medium text-[#94a3b8]">Últimas 24h</h2>
      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <StatCard title="Scans 24h" value={(m24.total_scans as number) ?? 0} color="#a855f7" />
        <StatCard title="Batches 24h" value={(m24.total_batches as number) ?? 0} color="#f59e0b" />
        <StatCard title="Anchors 24h" value={(m24.total_anchors as number) ?? 0} color="#06b6d4" />
        <StatCard title="Produtos 24h" value={(m24.total_products as number) ?? 0} color="#22c55e" />
      </div>

      {/* 30 days */}
      <h2 className="mb-3 text-sm font-medium text-[#94a3b8]">Últimos 30 dias</h2>
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard title="Usuários" value={(dashboard?.total_users as number) ?? 0} color="#3b82f6" />
        <StatCard title="Produtos" value={(dashboard?.total_products as number) ?? 0} color="#22c55e" />
        <StatCard title="Scans" value={(dashboard?.total_scans as number) ?? 0} color="#a855f7" />
        <StatCard title="Batches" value={(dashboard?.total_batches as number) ?? 0} color="#f59e0b" />
        <StatCard title="Anchors" value={(dashboard?.total_anchors as number) ?? 0} color="#06b6d4" />
      </div>

      {/* Infrastructure */}
      <Card className="mb-6">
        <h2 className="mb-4 text-lg font-semibold">Infraestrutura</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-xs text-[#94a3b8]">Uptime</p>
            <p className="text-lg font-semibold text-[#f8fafc]">
              {extended ? formatUptime(extended.uptime_seconds) : "-"}
            </p>
          </div>
          <div>
            <p className="text-xs text-[#94a3b8]">Redis</p>
            <p className={`text-lg font-semibold ${extended?.redis_status === "ok" ? "text-emerald-400" : "text-red-400"}`}>
              {extended?.redis_status ?? "-"}
            </p>
          </div>
          <div>
            <p className="text-xs text-[#94a3b8]">PostgreSQL</p>
            <p className={`text-lg font-semibold ${extended?.postgres_status === "ok" ? "text-emerald-400" : "text-red-400"}`}>
              {extended?.postgres_status ?? "-"}
            </p>
          </div>
          <div>
            <p className="text-xs text-[#94a3b8]">Latência média API</p>
            <p className="text-lg font-semibold text-[#f8fafc]">
              {extended?.api_latency_avg_ms != null ? `${extended.api_latency_avg_ms} ms` : "-"}
            </p>
          </div>
          <div>
            <p className="text-xs text-[#94a3b8]">CPU</p>
            <p className="text-lg font-semibold text-[#f8fafc]">
              {extended ? `${extended.cpu_percent}%` : "-"}
            </p>
          </div>
          <div>
            <p className="text-xs text-[#94a3b8]">Memória</p>
            <p className="text-lg font-semibold text-[#f8fafc]">
              {extended ? `${extended.memory_percent}% (${extended.memory_used_mb}/${extended.memory_total_mb} MB)` : "-"}
            </p>
          </div>
        </div>
      </Card>

      {/* Services */}
      <Card>
        <h2 className="mb-4 text-lg font-semibold">Status dos serviços</h2>
        <div className="flex flex-wrap gap-3">
          {extended?.services?.map((s) => (
            <span
              key={s.service}
              className={`rounded-lg px-3 py-2 text-sm ${
                s.status === "ok"
                  ? "bg-emerald-900/50 text-emerald-300"
                  : "bg-red-900/50 text-red-300"
              }`}
            >
              {s.service}: {s.status}
              {s.latency_ms != null ? ` (${s.latency_ms}ms)` : ""}
            </span>
          ))}
        </div>
      </Card>
    </div>
  );
}
