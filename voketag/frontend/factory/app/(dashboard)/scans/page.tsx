"use client";

import { useState } from "react";
import Link from "next/link";
import { useScans } from "@/hooks/useScans";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";

const RISK_VARIANTS = {
  low: "success" as const,
  medium: "warning" as const,
  high: "alert" as const,
};

export default function ScansPage() {
  const [filters, setFilters] = useState({
    batch_id: "",
    country: "",
    risk_status: "",
    date_from: "",
    date_to: "",
  });

  const apiFilters = {
    ...(filters.batch_id && { batch_id: filters.batch_id }),
    ...(filters.country && { country: filters.country }),
    ...(filters.risk_status && { risk_status: filters.risk_status as "low" | "medium" | "high" }),
    ...(filters.date_from && { date_from: filters.date_from }),
    ...(filters.date_to && { date_to: filters.date_to }),
    limit: 50,
  };

  const { data, isLoading } = useScans(Object.keys(apiFilters).length ? apiFilters : undefined, {
    refetchInterval: 5000,
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const activity = data?.activity_by_minute ?? [];

  const clearFilters = () =>
    setFilters({
      batch_id: "",
      country: "",
      risk_status: "",
      date_from: "",
      date_to: "",
    });

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-graphite-900 dark:text-white">
            Acompanhamento de Scans
          </h2>
          <p className="mt-1 text-sm text-graphite-500 dark:text-graphite-400">
            Scans em tempo real — atualização a cada 5s
          </p>
        </div>
        <div className="rounded-lg border border-graphite-200 bg-white px-4 py-2 shadow dark:border-graphite-700 dark:bg-graphite-900">
          <p className="text-sm text-graphite-500 dark:text-graphite-400">Total de scans</p>
          <p className="text-xl font-bold text-graphite-900 dark:text-white">{total}</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <h3 className="font-medium text-graphite-900 dark:text-white">Filtros</h3>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div>
              <label className="block text-xs text-graphite-500">Lote</label>
              <input
                type="text"
                value={filters.batch_id}
                onChange={(e) => setFilters((f) => ({ ...f, batch_id: e.target.value }))}
                placeholder="batch_id"
                className="mt-1 rounded-lg border border-graphite-300 bg-white px-3 py-2 text-sm dark:border-graphite-700 dark:bg-graphite-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-xs text-graphite-500">País</label>
              <input
                type="text"
                value={filters.country}
                onChange={(e) => setFilters((f) => ({ ...f, country: e.target.value }))}
                placeholder="BR"
                className="mt-1 rounded-lg border border-graphite-300 bg-white px-3 py-2 text-sm dark:border-graphite-700 dark:bg-graphite-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-xs text-graphite-500">Risco</label>
              <select
                value={filters.risk_status}
                onChange={(e) => setFilters((f) => ({ ...f, risk_status: e.target.value }))}
                className="mt-1 rounded-lg border border-graphite-300 bg-white px-3 py-2 text-sm dark:border-graphite-700 dark:bg-graphite-900 dark:text-white"
              >
                <option value="">Todos</option>
                <option value="low">Baixo</option>
                <option value="medium">Médio</option>
                <option value="high">Alto</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-graphite-500">Data de</label>
              <input
                type="date"
                value={filters.date_from}
                onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value }))}
                className="mt-1 rounded-lg border border-graphite-300 bg-white px-3 py-2 text-sm dark:border-graphite-700 dark:bg-graphite-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-xs text-graphite-500">Data até</label>
              <input
                type="date"
                value={filters.date_to}
                onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value }))}
                className="mt-1 rounded-lg border border-graphite-300 bg-white px-3 py-2 text-sm dark:border-graphite-700 dark:bg-graphite-900 dark:text-white"
              />
            </div>
            <div className="flex items-end">
              <button
                type="button"
                onClick={clearFilters}
                className="rounded-lg border border-graphite-300 px-3 py-2 text-sm text-graphite-600 hover:bg-graphite-50 dark:border-graphite-600 dark:text-graphite-400 dark:hover:bg-graphite-800"
              >
                Limpar
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {activity.length > 0 && (
        <Card>
          <CardHeader>
            <h3 className="font-medium text-graphite-900 dark:text-white">
              Atividade por minuto
            </h3>
          </CardHeader>
          <CardContent>
            <div className="flex h-32 items-end gap-0.5">
              {activity.map((a, i) => (
                <div
                  key={i}
                  className="flex-1 rounded-t bg-primary-500/70 transition-all hover:bg-primary-500"
                  style={{ height: `${Math.max(2, (a.count / 25) * 100)}%` }}
                  title={`Min ${a.minute}: ${a.count}`}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-graphite-500 dark:text-graphite-400">Risco Baixo</p>
            <p className="text-2xl font-bold text-success">
              {items.filter((s) => s.risk_status === "low").length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-graphite-500 dark:text-graphite-400">Risco Médio</p>
            <p className="text-2xl font-bold text-warning">
              {items.filter((s) => s.risk_status === "medium").length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-graphite-500 dark:text-graphite-400">
              Risco Alto / Duplicata
            </p>
            <p className="text-2xl font-bold text-alert">
              {items.filter((s) => s.risk_status === "high" || s.is_duplicate).length}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h3 className="font-medium text-graphite-900 dark:text-white">
            Últimos scans (tempo real)
          </h3>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : items.length === 0 ? (
            <EmptyState
              title="Nenhum scan registrado"
              description="Os scans aparecerão aqui assim que forem realizados."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-graphite-200 text-left text-sm text-graphite-500 dark:border-graphite-700 dark:text-graphite-400">
                    <th className="pb-3 font-medium">Serial</th>
                    <th className="pb-3 font-medium">Horário</th>
                    <th className="pb-3 font-medium">País</th>
                    <th className="pb-3 font-medium">Dispositivo</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((s) => (
                    <tr
                      key={s.id}
                      className="border-b border-graphite-200 transition-colors hover:bg-graphite-50 dark:border-graphite-800 dark:hover:bg-graphite-800/50"
                    >
                      <td className="py-4 font-mono text-sm text-graphite-800 dark:text-graphite-200">
                        {s.serial_number}
                      </td>
                      <td className="py-4 text-sm text-graphite-700 dark:text-graphite-300">
                        {new Date(s.scanned_at).toLocaleTimeString("pt-BR")}
                      </td>
                      <td className="py-4 text-sm text-graphite-700 dark:text-graphite-300">
                        {s.country ?? "—"}
                      </td>
                      <td className="py-4 text-sm text-graphite-700 dark:text-graphite-300">
                        {s.device ?? "—"}
                      </td>
                      <td className="py-4">
                        <div className="flex gap-1">
                          <Badge variant={RISK_VARIANTS[s.risk_status] ?? "default"}>
                            {s.risk_status}
                          </Badge>
                          {s.is_duplicate && (
                            <Badge variant="alert">Duplicata</Badge>
                          )}
                        </div>
                      </td>
                      <td className="py-4">
                        <Link
                          href={`/scans/${s.id}`}
                          className="text-sm text-primary-600 hover:underline dark:text-primary-400"
                        >
                          Detalhes
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
