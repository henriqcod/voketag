"use client";

import { useCallback, useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { getSystemStatus, getSystemConfig, getPrometheusMetrics } from "@/lib/api-client";

export default function MonitoringPage() {
  const [status, setStatus] = useState<{ services?: { service: string; url?: string; status: string }[] } | null>(null);
  const [config, setConfig] = useState<Record<string, unknown> | null>(null);
  const [metrics, setMetrics] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metricsExpanded, setMetricsExpanded] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [s, c] = await Promise.all([getSystemStatus(), getSystemConfig()]);
      setStatus(s);
      setConfig(c);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function loadMetrics() {
    try {
      const m = await getPrometheusMetrics();
      setMetrics(m);
      setMetricsExpanded(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar métricas");
    }
  }

  const prometheusUrl = (config?.prometheus_url as string) || "http://127.0.0.1:8082/metrics";
  const grafanaUrl = (config?.grafana_url as string) || "http://localhost:3000";

  if (loading) {
    return (
      <div className="flex min-h-[200px] items-center justify-center py-12">
        <p className="text-[#94a3b8]">Carregando...</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-[#f8fafc]">Monitoramento</h1>

      {error && (
        <div className="mb-6 rounded-lg border border-red-800 bg-red-900/30 p-4 text-red-300">
          {error}
        </div>
      )}

      <div className="mb-6 flex flex-wrap gap-3">
        <a
          href={prometheusUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-lg border border-[#334155] bg-[#1e293b] px-4 py-2 text-sm text-[#f8fafc] hover:bg-[#334155]"
        >
          Prometheus
        </a>
        <a
          href={grafanaUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 rounded-lg border border-[#334155] bg-[#1e293b] px-4 py-2 text-sm text-[#f8fafc] hover:bg-[#334155]"
        >
          Grafana
        </a>
        <Button variant="secondary" size="sm" onClick={loadMetrics}>
          {metricsExpanded ? "Recarregar métricas" : "Exibir métricas Prometheus"}
        </Button>
      </div>

      <Card className="mb-6">
        <h2 className="mb-4 text-lg font-semibold">Status dos Serviços</h2>
        <div className="space-y-3">
          {status?.services?.map((s) => (
            <div
              key={s.service}
              className="flex items-center justify-between rounded-lg border border-[#334155] bg-[#0f172a] px-4 py-3"
            >
              <span className="font-medium capitalize">{s.service}</span>
              <div className="flex items-center gap-3">
                {s.url && (
                  <span className="text-xs text-[#94a3b8]">{s.url}</span>
                )}
                <Badge
                  variant={
                    s.status === "ok"
                      ? "success"
                      : s.status.startsWith("error") || s.status.startsWith("unreachable")
                      ? "error"
                      : "warning"
                  }
                >
                  {s.status}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {metricsExpanded && metrics && (
        <Card className="mb-6">
          <h2 className="mb-4 text-lg font-semibold">Métricas Prometheus</h2>
          <pre className="max-h-[400px] overflow-auto rounded-lg bg-[#0f172a] p-4 text-xs text-[#94a3b8]">
            {metrics}
          </pre>
        </Card>
      )}

      <Card>
        <h2 className="mb-4 text-lg font-semibold">Configuração do Sistema</h2>
        <pre className="overflow-auto rounded-lg bg-[#0f172a] p-4 text-sm text-[#94a3b8]">
          {JSON.stringify(config, null, 2)}
        </pre>
      </Card>
    </div>
  );
}
