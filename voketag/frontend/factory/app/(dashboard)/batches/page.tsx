"use client";

import { useState } from "react";
import Link from "next/link";
import { useToast } from "@/lib/toast-context";
import { useBatchesList, useRetryBatch } from "@/hooks/useBatches";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/EmptyState";

const STATUS_VARIANTS: Record<string, "success" | "alert" | "warning" | "default"> = {
  completed: "success",
  failed: "alert",
  anchor_failed: "alert",
  pending: "warning",
  processing: "warning",
  anchoring: "warning",
};

function getBatchRisk(status: string): "low" | "medium" | "high" {
  if (["completed"].includes(status)) return "low";
  if (["pending", "processing", "anchoring"].includes(status)) return "medium";
  return "high";
}

export default function BatchesPage() {
  const [page, setPage] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [riskFilter, setRiskFilter] = useState<string>("");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");
  const [search, setSearch] = useState("");
  const limit = 10;
  const { success: toastSuccess } = useToast();

  const listParams = {
    skip: page * limit,
    limit,
    ...(statusFilter && { status: statusFilter }),
    ...(riskFilter && { risk: riskFilter }),
    ...(dateFrom && { date_from: dateFrom }),
    ...(dateTo && { date_to: dateTo }),
    ...(search && { search }),
  };

  const { data: batches = [], isLoading } = useBatchesList(listParams);
  const retryMutation = useRetryBatch({ onSuccess: () => toastSuccess("Retentativa iniciada.") });

  const exportTable = () => {
    const headers = ["ID", "Status", "Produtos", "Criado"];
    const rows = batches.map((b) => [
      b.id,
      b.status,
      String(b.product_count),
      new Date(b.created_at).toLocaleDateString("pt-BR"),
    ]);
    const csv = [headers.join(","), ...rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(","))].join("\n");
    const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `lotes_export_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    toastSuccess("Tabela exportada.");
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap gap-2">
              <input
                type="text"
                placeholder="Buscar por ID..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="rounded-lg border border-graphite-300 bg-white px-3 py-2 text-sm text-graphite-900 placeholder-graphite-400 dark:border-graphite-700 dark:bg-graphite-900 dark:text-white dark:placeholder-graphite-500"
              />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="rounded-lg border border-graphite-300 bg-white px-3 py-2 text-sm text-graphite-900 dark:border-graphite-700 dark:bg-graphite-900 dark:text-white"
              >
                <option value="">Todos os status</option>
                <option value="completed">Completo</option>
                <option value="pending">Pendente</option>
                <option value="processing">Processando</option>
                <option value="failed">Falhou</option>
                <option value="anchor_failed">Falha no registro</option>
              </select>
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="rounded-lg border border-graphite-300 bg-white px-3 py-2 text-sm text-graphite-900 dark:border-graphite-700 dark:bg-graphite-900 dark:text-white"
              >
                <option value="">Todos os riscos</option>
                <option value="low">Risco baixo</option>
                <option value="medium">Risco médio</option>
                <option value="high">Risco alto</option>
              </select>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="rounded-lg border border-graphite-300 bg-white px-3 py-2 text-sm dark:border-graphite-700 dark:bg-graphite-900 dark:text-white"
                placeholder="Data inicial"
              />
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="rounded-lg border border-graphite-300 bg-white px-3 py-2 text-sm dark:border-graphite-700 dark:bg-graphite-900 dark:text-white"
                placeholder="Data final"
              />
              <button
                type="button"
                onClick={exportTable}
                disabled={batches.length === 0}
                className="rounded-lg border border-graphite-300 bg-white px-3 py-2 text-sm font-medium text-graphite-700 hover:bg-graphite-50 disabled:opacity-50 dark:border-graphite-600 dark:bg-graphite-900 dark:text-graphite-300 dark:hover:bg-graphite-800"
              >
                Exportar
              </button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : batches.length === 0 ? (
            <EmptyState
              title="Nenhum lote encontrado"
              description="Crie um lote em Registro de Lotes ou ajuste os filtros."
              action={<Link href="/batches/anchor" className="text-primary-600 hover:underline">Ir para Registro de Lotes</Link>}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-graphite-200 text-left text-sm text-graphite-500 dark:border-graphite-700 dark:text-graphite-400">
                    <th className="pb-3 font-medium">ID</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Produtos</th>
                    <th className="pb-3 font-medium">Criado</th>
                    <th className="pb-3 font-medium">Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {batches.map((b) => (
                    <tr
                      key={b.id}
                      className="border-b border-graphite-200 transition-colors hover:bg-graphite-50 dark:border-graphite-800 dark:hover:bg-graphite-800/50"
                    >
                      <td className="py-4">
                        <Link
                          href={`/batches/${b.id}`}
                          className="font-mono text-sm text-primary-600 hover:underline dark:text-primary-400"
                        >
                          {b.id.slice(0, 8)}...
                        </Link>
                      </td>
                      <td className="py-4">
                        <Badge variant={STATUS_VARIANTS[b.status] ?? "default"}>
                          {b.status}
                        </Badge>
                      </td>
                      <td className="py-4 text-sm text-graphite-700 dark:text-graphite-300">
                        {b.product_count}
                      </td>
                      <td className="py-4 text-sm text-graphite-500 dark:text-graphite-400">
                        {new Date(b.created_at).toLocaleDateString("pt-BR")}
                      </td>
                      <td className="py-4">
                        <div className="flex gap-2">
                          <Link
                            href={`/batches/${b.id}`}
                            className="text-sm text-primary-600 hover:underline dark:text-primary-400"
                          >
                            Detalhes
                          </Link>
                          {["failed", "anchor_failed"].includes(b.status) && (
                            <button
                              onClick={() => retryMutation.mutate(b.id)}
                              disabled={retryMutation.isPending}
                              className="text-sm text-amber-600 hover:underline disabled:opacity-50 dark:text-amber-400"
                            >
                              Tentar novamente
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {batches.length >= limit && (
            <div className="mt-4 flex justify-between">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="rounded border border-graphite-300 px-4 py-2 text-sm text-graphite-700 disabled:opacity-50 dark:border-graphite-600 dark:text-graphite-300"
              >
                Anterior
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                className="rounded border border-graphite-300 px-4 py-2 text-sm text-graphite-700 dark:border-graphite-600 dark:text-graphite-300"
              >
                Próximo
              </button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
