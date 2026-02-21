"use client";

import { useState } from "react";
import { useDashboardMetrics } from "@/hooks/useDashboard";
import { useLayout } from "@/lib/layout-context";
import { useEffect } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { GeoHeatMap } from "@/components/ui/GeoHeatMap";

type GeoPeriod = "1d" | "7d" | "30d";

export default function DashboardPage() {
  const [geoPeriod, setGeoPeriod] = useState<GeoPeriod>("1d");

  const { data, isLoading, error } = useDashboardMetrics();

  const { setHeader } = useLayout();
  useEffect(() => {
    if (data?.system_status) {
      setHeader({ status: data.system_status });
    }
  }, [data?.system_status, setHeader]);

  if (error) {
    return (
      <div className="rounded-lg border border-alert/30 bg-alert/10 p-6 text-alert">
        Erro ao carregar métricas. Verifique a conexão.
      </div>
    );
  }

  const metrics = data ?? {
    total_batches: 0,
    pending_batches: 0,
    error_batches: 0,
    total_qr_generated: 0,
    scans_last_24h: 0,
    scans_7d: 0,
    scans_30d: 0,
    risk_rate: 0,
    blockchain_sla: 0,
    system_status: "offline" as const,
    scans_by_hour: [],
    scans_by_minute: [],
    geo_distribution: [],
    last_anchorages: [],
    active_alerts: [],
    blockchain_status: "offline" as const,
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-semibold text-graphite-900 dark:text-white">Dashboard Executivo</h2>
        <p className="mt-1 text-sm text-graphite-500 dark:text-graphite-400">
          KPIs institucionais e visão do sistema
        </p>
      </div>

      {metrics.active_alerts.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-900/20">
          <p className="text-sm font-medium text-amber-800 dark:text-amber-200">Alertas ativos</p>
          {metrics.active_alerts.map((a) => (
            <p key={a.id} className="mt-1 text-sm text-amber-700 dark:text-amber-300">{a.message}</p>
          ))}
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8">
        {isLoading ? (
          Array.from({ length: 8 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <Skeleton className="mb-2 h-8 w-20" />
                <Skeleton className="h-4 w-full" />
              </CardContent>
            </Card>
          ))
        ) : (
          <>
            <MetricCard label="Lotes ancorados" value={metrics.total_batches} />
            <MetricCard label="Lotes pendentes" value={metrics.pending_batches} variant="warning" />
            <MetricCard label="QR Codes" value={metrics.total_qr_generated.toLocaleString("pt-BR")} />
            <MetricCard label="Scans 24h" value={metrics.scans_last_24h.toLocaleString("pt-BR")} />
            <MetricCard label="Scans 7d" value={metrics.scans_7d.toLocaleString("pt-BR")} />
            <MetricCard label="Scans 30d" value={metrics.scans_30d.toLocaleString("pt-BR")} />
            <MetricCard label="Taxa risco" value={`${metrics.risk_rate}%`} variant={metrics.risk_rate > 10 ? "alert" : undefined} />
            <MetricCard
              label="SLA de Validação"
              value={`${metrics.blockchain_sla}%`}
              subtext={metrics.system_status}
            />
          </>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <h3 className="font-medium text-graphite-900 dark:text-white">Scans por hora</h3>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-48 w-full" />
            ) : (
              <div className="flex h-48 items-end gap-1">
                {metrics.scans_by_hour.slice(0, 24).map((item, i) => (
                  <div
                    key={i}
                    className="flex-1 rounded-t bg-primary-600/60 transition-all hover:bg-primary-500"
                    style={{ height: `${Math.max(4, (item.count / 130) * 100)}%` }}
                    title={`${item.hour}: ${item.count} scans`}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="font-medium text-graphite-900 dark:text-white">Distribuição geográfica</h3>
            <p className="mt-1 text-xs text-graphite-500 dark:text-graphite-400">
              Pins de calor por região (dados agregados)
            </p>
          </CardHeader>
          <CardContent>
            <GeoHeatMap
              countryData={metrics.geo_distribution}
              period={geoPeriod}
              onPeriodChange={setGeoPeriod}
              isLoading={isLoading}
            />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <h3 className="font-medium text-graphite-900 dark:text-white">Últimos registros</h3>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-48 w-full" />
            ) : metrics.last_anchorages.length === 0 ? (
              <p className="py-8 text-center text-sm text-graphite-500 dark:text-graphite-400">Nenhum registro recente</p>
            ) : (
              <div className="space-y-3">
                {metrics.last_anchorages.map((a) => (
                  <div
                    key={a.batch_id}
                    className="flex items-center justify-between rounded-lg border border-graphite-200 p-3 dark:border-graphite-800"
                  >
                    <div>
                      <p className="font-mono text-sm text-graphite-800 dark:text-graphite-200">
                        {a.batch_id.slice(0, 8)}...
                      </p>
                      <p className="text-xs text-graphite-500 dark:text-graphite-400">
                        {a.product_count} produtos
                      </p>
                    </div>
                    <Badge
                      variant={
                        a.status === "completed"
                          ? "success"
                          : a.status === "failed"
                          ? "alert"
                          : "default"
                      }
                    >
                      {a.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="font-medium text-graphite-900 dark:text-white">Status do sistema</h3>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <span
                className={`h-3 w-3 rounded-full ${
                  metrics.system_status === "online"
                    ? "bg-success"
                    : metrics.system_status === "degraded"
                    ? "bg-amber-500"
                    : "bg-alert"
                } ${metrics.system_status === "online" ? "animate-pulse" : ""}`}
              />
              <span className="text-graphite-700 dark:text-graphite-300">
                {metrics.system_status === "online"
                  ? "Online"
                  : metrics.system_status === "degraded"
                  ? "Degradado"
                  : "Offline"}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  subtext,
  variant,
}: {
  label: string;
  value: React.ReactNode;
  subtext?: string;
  variant?: "alert" | "warning";
}) {
  const color =
    variant === "alert"
      ? "text-alert"
      : variant === "warning"
      ? "text-amber-600 dark:text-amber-400"
      : "text-graphite-900 dark:text-white";
  return (
    <Card>
      <CardContent className="pt-6">
        <p className="text-sm text-graphite-500 dark:text-graphite-400">{label}</p>
        <p className={`mt-1 text-2xl font-bold ${color}`}>{value}</p>
        {subtext && <p className="mt-1 text-xs text-graphite-500 dark:text-graphite-400">{subtext}</p>}
      </CardContent>
    </Card>
  );
}
