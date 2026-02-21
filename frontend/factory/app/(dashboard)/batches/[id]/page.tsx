"use client";

import Link from "next/link";
import { useBatch, useBatchStatus, useRetryBatch, useBatchAntifraudEvents } from "@/hooks/useBatches";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { DataIntegrityIndicator } from "@/components/ui/DataIntegrityIndicator";

export default function BatchDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const { id } = params;

  const { data: batch, isLoading } = useBatch(id);
  const { data: status } = useBatchStatus(id, !!batch);
  const retryMutation = useRetryBatch();
  const { data: antifraudEvents = [] } = useBatchAntifraudEvents(id, !!batch);

  if (isLoading || !batch) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <Link
            href="/batches"
            className="text-sm text-graphite-500 hover:text-graphite-900 dark:text-graphite-400 dark:hover:text-white"
          >
            ← Voltar
          </Link>
          <h2 className="mt-2 text-xl font-semibold text-graphite-900 dark:text-white">
            Lote {batch.id.slice(0, 8)}...
          </h2>
        </div>
        <Badge
          variant={
            batch.status === "completed"
              ? "success"
              : ["failed", "anchor_failed"].includes(batch.status)
              ? "alert"
              : "default"
          }
        >
          {batch.status}
        </Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <h3 className="font-medium text-graphite-900 dark:text-white">Certificação e Validação</h3>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-graphite-500">Código de Validação</p>
              <p className="mt-1 font-mono text-sm text-graphite-800 break-all dark:text-graphite-200">
                {batch.blockchain_tx || status?.blockchain_tx || "—"}
              </p>
            </div>
            <div>
              <p className="text-sm text-graphite-500">Chave de Integridade</p>
              <p className="mt-1 font-mono text-sm text-graphite-800 break-all dark:text-graphite-200">
                {batch.merkle_root || status?.merkle_root || "—"}
              </p>
            </div>
            <div className="mt-4">
              <DataIntegrityIndicator
                status={batch.status === "completed" ? "verified" : ["failed", "anchor_failed"].includes(batch.status) ? "degraded" : "pending"}
                merkleRoot={batch.merkle_root ?? status?.merkle_root ?? undefined}
                blockchainTx={batch.blockchain_tx ?? status?.blockchain_tx ?? undefined}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="font-medium text-graphite-900 dark:text-white">Detalhes do Lote</h3>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-graphite-500 dark:text-graphite-400">Produtos</p>
              <p className="mt-1 text-graphite-900 dark:text-white">{batch.product_count}</p>
            </div>
            <div>
              <p className="text-sm text-graphite-500 dark:text-graphite-400">Criado em</p>
              <p className="mt-1 text-graphite-700 dark:text-graphite-300">
                {new Date(batch.created_at).toLocaleString("pt-BR")}
              </p>
            </div>
            {batch.anchored_at && (
              <div>
                <p className="text-sm text-graphite-500 dark:text-graphite-400">Registrado em</p>
                <p className="mt-1 text-graphite-700 dark:text-graphite-300">
                  {new Date(batch.anchored_at).toLocaleString("pt-BR")}
                </p>
              </div>
            )}
            {batch.error && (
              <div>
                <p className="text-sm text-graphite-500 dark:text-graphite-400">Erro</p>
                <p className="mt-1 text-alert">{batch.error}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {["failed", "anchor_failed"].includes(batch.status) && (
        <Card>
          <CardContent className="pt-6">
            <button
              onClick={() => retryMutation.mutate(id)}
              disabled={retryMutation.isPending}
              className="rounded-lg bg-primary-600 px-6 py-2 text-sm font-medium text-white hover:bg-primary-500 disabled:opacity-50"
            >
              {retryMutation.isPending ? "Processando..." : "Tentar novamente"}
            </button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <h3 className="font-medium text-graphite-900 dark:text-white">Linha do tempo do lote</h3>
        </CardHeader>
        <CardContent>
          <div className="relative space-y-6">
            <TimelineItem
              date={batch.created_at}
              label="Lote criado"
              status="completed"
            />
            {batch.processing_completed_at && (
              <TimelineItem
                date={batch.processing_completed_at}
                label="Processamento concluído"
                status="completed"
              />
            )}
            {batch.anchored_at && (
              <TimelineItem
                date={batch.anchored_at}
                label="Registro confirmado"
                status="completed"
              />
            )}
            {batch.error && (
              <TimelineItem
                date={new Date().toISOString()}
                label="Erro registrado"
                status="error"
                detail={batch.error}
              />
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <h3 className="font-medium text-graphite-900 dark:text-white">Eventos antifraude</h3>
        </CardHeader>
        <CardContent>
          {antifraudEvents.length === 0 ? (
            <p className="text-sm text-graphite-500 dark:text-graphite-400">
              Nenhum evento antifraude registrado para este lote.
            </p>
          ) : (
            <div className="space-y-3">
              {antifraudEvents.map((ev) => (
                <div
                  key={ev.id}
                  className={`flex items-start gap-4 rounded-lg border px-4 py-3 ${
                    ev.severity === "high"
                      ? "border-amber-200 bg-amber-50/50 dark:border-amber-800 dark:bg-amber-900/10"
                      : ev.severity === "medium"
                      ? "border-graphite-200 dark:border-graphite-700"
                      : "border-graphite-100 dark:border-graphite-800"
                  }`}
                >
                  <span className="text-xs text-graphite-500 dark:text-graphite-400">
                    {new Date(ev.timestamp).toLocaleString("pt-BR")}
                  </span>
                  <span className="font-mono text-sm text-graphite-800 dark:text-graphite-200">
                    {ev.type}
                  </span>
                  {ev.details && Object.keys(ev.details).length > 0 && (
                    <pre className="text-xs text-graphite-600 dark:text-graphite-400 overflow-x-auto">
                      {JSON.stringify(ev.details)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function TimelineItem({
  date,
  label,
  status,
  detail,
}: {
  date: string;
  label: string;
  status: "completed" | "error" | "pending";
  detail?: string;
}) {
  const dotColor = status === "completed" ? "bg-success" : status === "error" ? "bg-alert" : "bg-graphite-400";
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className={`h-3 w-3 rounded-full ${dotColor}`} />
        <div className="mt-1 h-full w-px bg-graphite-200 dark:bg-graphite-700" />
      </div>
      <div className="flex-1 pb-6">
        <p className="text-sm font-medium text-graphite-800 dark:text-graphite-200">{label}</p>
        <p className="text-xs text-graphite-500 dark:text-graphite-400">
          {new Date(date).toLocaleString("pt-BR")}
        </p>
        {detail && <p className="mt-1 text-xs text-alert">{detail}</p>}
      </div>
    </div>
  );
}
