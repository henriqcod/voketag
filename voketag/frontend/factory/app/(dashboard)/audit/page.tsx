"use client";

import { useState } from "react";
import { useAuditLogs } from "@/hooks/useAudit";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";

const CRITICAL_ACTIONS = ["login_failed", "batch_failed", "anchor_failed", "unauthorized"];

function downloadCsv(items: { action: string; actor: string; ip: string; timestamp: string }[], filename: string) {
  const headers = ["Timestamp", "Ação", "Usuário", "IP"];
  const rows = items.map((log) => [
    new Date(log.timestamp).toLocaleString("pt-BR"),
    log.action,
    log.actor,
    log.ip,
  ]);
  const csv = [headers, ...rows].map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

export default function AuditPage() {
  const [filters, setFilters] = useState({
    action: "",
    actor: "",
    date_from: "",
    date_to: "",
  });

  const apiFilters = {
    ...(filters.action && { action: filters.action }),
    ...(filters.actor && { actor: filters.actor }),
    ...(filters.date_from && { date_from: filters.date_from }),
    ...(filters.date_to && { date_to: filters.date_to }),
    limit: 100,
  };

  const { data, isLoading } = useAuditLogs(
    Object.keys(apiFilters).length ? apiFilters : { limit: 100 }
  );

  const items = data?.items ?? [];

  const clearFilters = () =>
    setFilters({ action: "", actor: "", date_from: "", date_to: "" });

  const handleExport = () => {
    downloadCsv(items, `audit_${new Date().toISOString().slice(0, 10)}.csv`);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <Card>
        <CardHeader>
          <h3 className="font-medium text-graphite-900 dark:text-white">
            Histórico de Auditoria
          </h3>
          <p className="mt-1 text-sm text-graphite-500 dark:text-graphite-400">
            Governança e conformidade — ações rastreáveis
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-end gap-4">
            <div>
              <label className="block text-xs text-graphite-500">Ação</label>
              <input
                type="text"
                value={filters.action}
                onChange={(e) => setFilters((f) => ({ ...f, action: e.target.value }))}
                placeholder="ex: upload_csv"
                className="mt-1 rounded-lg border border-graphite-300 bg-white px-3 py-2 text-sm dark:border-graphite-700 dark:bg-graphite-900 dark:text-white"
              />
            </div>
            <div>
              <label className="block text-xs text-graphite-500">Usuário</label>
              <input
                type="text"
                value={filters.actor}
                onChange={(e) => setFilters((f) => ({ ...f, actor: e.target.value }))}
                placeholder="ex: admin@voketag.com"
                className="mt-1 rounded-lg border border-graphite-300 bg-white px-3 py-2 text-sm dark:border-graphite-700 dark:bg-graphite-900 dark:text-white"
              />
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
            <button
              type="button"
              onClick={clearFilters}
              className="rounded-lg border border-graphite-300 px-3 py-2 text-sm hover:bg-graphite-50 dark:border-graphite-600 dark:hover:bg-graphite-800"
            >
              Limpar
            </button>
            <button
              type="button"
              onClick={handleExport}
              disabled={items.length === 0}
              className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-500 disabled:opacity-50"
            >
              Exportar CSV
            </button>
          </div>

          {isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : items.length === 0 ? (
            <EmptyState
              title="Nenhum registro de auditoria"
              description="Os eventos aparecerão aqui conforme as ações forem realizadas."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-graphite-200 text-left text-sm text-graphite-500 dark:border-graphite-700 dark:text-graphite-400">
                    <th className="pb-3 font-medium">Timestamp</th>
                    <th className="pb-3 font-medium">Ação</th>
                    <th className="pb-3 font-medium">Usuário</th>
                    <th className="pb-3 font-medium">IP</th>
                    <th className="pb-3 font-medium">Resultado</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((log) => {
                    const isCritical = CRITICAL_ACTIONS.some((a) =>
                      (log.action ?? "").toLowerCase().includes(a)
                    );
                    return (
                      <tr
                        key={log.id}
                        className={`border-b border-graphite-200 transition-colors dark:border-graphite-800 ${
                          isCritical
                            ? "bg-amber-50/50 dark:bg-amber-900/10"
                            : "hover:bg-graphite-50 dark:hover:bg-graphite-800/50"
                        }`}
                      >
                        <td className="py-4 text-sm text-graphite-600 dark:text-graphite-400">
                          {new Date(log.timestamp).toLocaleString("pt-BR")}
                        </td>
                        <td className="py-4">
                          <span className="font-mono text-sm text-graphite-800 dark:text-graphite-200">
                            {log.action}
                          </span>
                          {isCritical && (
                            <Badge variant="alert" className="ml-2">
                              Crítico
                            </Badge>
                          )}
                        </td>
                        <td className="py-4 text-sm text-graphite-700 dark:text-graphite-300">
                          {log.actor}
                        </td>
                        <td className="py-4 font-mono text-sm text-graphite-500 dark:text-graphite-400">
                          {log.ip}
                        </td>
                        <td className="py-4">
                          <Badge variant={isCritical ? "alert" : "success"}>
                            {isCritical ? "Falha" : "OK"}
                          </Badge>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
