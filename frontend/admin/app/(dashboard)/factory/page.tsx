"use client";

import { useCallback, useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import {
  getDashboardBatches,
  listBatches,
  getBatchDetail,
  getBatchMerkleTree,
  retryBatch,
  listAnchors,
  retryAnchor,
  type Batch,
  type Anchor,
  type MerkleTreeResponse,
} from "@/lib/api-client";
import { MerkleTreeView } from "@/components/ui/MerkleTreeView";

const EXPLORER_URL = "https://etherscan.io/tx/";

export default function FactoryPage() {
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [totalBatches, setTotalBatches] = useState(0);
  const [anchors, setAnchors] = useState<Anchor[]>([]);
  const [totalAnchors, setTotalAnchors] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [detailBatch, setDetailBatch] = useState<Batch & { blockchain_task_id?: string; metadata?: unknown } | null>(null);
  const [confirmRetryBatch, setConfirmRetryBatch] = useState<Batch | null>(null);
  const [confirmRetryAnchor, setConfirmRetryAnchor] = useState<Anchor | null>(null);
  const [retryLoading, setRetryLoading] = useState(false);
  const [merkleTree, setMerkleTree] = useState<MerkleTreeResponse | null>(null);
  const [merkleLoading, setMerkleLoading] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [s, b, a] = await Promise.all([
        getDashboardBatches(30),
        listBatches({ skip: page * 50, limit: 50, status: statusFilter || undefined }),
        listAnchors({ skip: 0, limit: 20, status: statusFilter || undefined }),
      ]);
      setStats(s);
      setBatches(b.batches);
      setTotalBatches(b.total);
      setAnchors(a.anchors);
      setTotalAnchors(a.total);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setLoading(false);
    }
  }, [page, statusFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleRetryBatch() {
    if (!confirmRetryBatch) return;
    setRetryLoading(true);
    try {
      await retryBatch(confirmRetryBatch.id);
      setConfirmRetryBatch(null);
      loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao retentar");
    } finally {
      setRetryLoading(false);
    }
  }

  async function handleRetryAnchor() {
    if (!confirmRetryAnchor) return;
    setRetryLoading(true);
    try {
      await retryAnchor(confirmRetryAnchor.id);
      setConfirmRetryAnchor(null);
      loadData();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao retentar");
    } finally {
      setRetryLoading(false);
    }
  }

  async function openDetail(batch: Batch) {
    try {
      setMerkleTree(null);
      const d = await getBatchDetail(batch.id);
      setDetailBatch(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar");
    }
  }

  async function loadMerkleTree() {
    if (!detailBatch) return;
    setMerkleLoading(true);
    try {
      const data = await getBatchMerkleTree(detailBatch.id);
      setMerkleTree(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar árvore Merkle");
    } finally {
      setMerkleLoading(false);
    }
  }

  function statusColor(s: string) {
    if (s === "completed") return "text-emerald-400";
    if (s === "failed" || s === "anchor_failed") return "text-red-400";
    if (s === "anchoring" || s === "processing" || s === "pending") return "text-amber-400";
    return "text-[#94a3b8]";
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-[#94a3b8]">Carregando...</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-[#f8fafc]">Factory & Ancoragens</h1>

      {error && (
        <div className="mb-6 rounded-lg border border-red-800 bg-red-900/30 p-4 text-red-300">
          {error}
        </div>
      )}

      <div className="mb-8 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <p className="mb-1 text-xs text-[#94a3b8]">Total de Batches</p>
          <p className="text-2xl font-bold text-amber-400">
            {(stats?.total_batches as number) ?? 0}
          </p>
        </Card>
        <Card>
          <p className="mb-1 text-xs text-[#94a3b8]">Pendentes</p>
          <p className="text-2xl font-bold text-blue-400">
            {((stats?.by_status as Record<string, number>)?.["pending"] ?? 0) +
              ((stats?.by_status as Record<string, number>)?.["processing"] ?? 0) +
              ((stats?.by_status as Record<string, number>)?.["anchoring"] ?? 0)}
          </p>
        </Card>
        <Card>
          <p className="mb-1 text-xs text-[#94a3b8]">Concluídos</p>
          <p className="text-2xl font-bold text-emerald-400">
            {(stats?.by_status as Record<string, number>)?.["completed"] ?? 0}
          </p>
        </Card>
        <Card>
          <p className="mb-1 text-xs text-[#94a3b8]">Com Falha</p>
          <p className="text-2xl font-bold text-red-400">
            {((stats?.by_status as Record<string, number>)?.["failed"] ?? 0) +
              ((stats?.by_status as Record<string, number>)?.["anchor_failed"] ?? 0)}
          </p>
        </Card>
      </div>

      <Card className="mb-6">
        <h2 className="mb-4 text-lg font-semibold">Tabela de Lotes</h2>
        <div className="mb-4 flex gap-2">
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(0);
            }}
            className="rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-sm text-[#f8fafc]"
          >
            <option value="">Todos</option>
            <option value="pending">Pendente</option>
            <option value="processing">Processando</option>
            <option value="anchoring">Ancorando</option>
            <option value="completed">Concluído</option>
            <option value="failed">Falha</option>
            <option value="anchor_failed">Falha ancoragem</option>
          </select>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#334155] text-left text-[#94a3b8]">
                <th className="p-3">ID</th>
                <th className="p-3">Status</th>
                <th className="p-3">Produtos</th>
                <th className="p-3">Merkle Root</th>
                <th className="p-3">TX Blockchain</th>
                <th className="p-3">Criado</th>
                <th className="p-3"></th>
              </tr>
            </thead>
            <tbody>
              {batches.map((b) => (
                <tr key={b.id} className="border-b border-[#334155]/50">
                  <td className="p-3">
                    <button
                      onClick={() => openDetail(b)}
                      className="font-mono text-blue-400 hover:underline"
                    >
                      {b.id.slice(0, 8)}...
                    </button>
                  </td>
                  <td className="p-3">
                    <span className={statusColor(b.status)}>{b.status}</span>
                  </td>
                  <td className="p-3 text-[#94a3b8]">{b.product_count}</td>
                  <td className="p-3 font-mono text-xs text-[#94a3b8]">
                    {b.merkle_root ? `${b.merkle_root.slice(0, 12)}...` : "-"}
                  </td>
                  <td className="p-3">
                    {b.blockchain_tx ? (
                      <a
                        href={EXPLORER_URL + b.blockchain_tx}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:underline"
                      >
                        {b.blockchain_tx.slice(0, 10)}...
                      </a>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td className="p-3 text-[#94a3b8]">
                    {b.created_at ? new Date(b.created_at).toLocaleString("pt-BR") : "-"}
                  </td>
                  <td className="p-3">
                    {(b.status === "failed" || b.status === "anchor_failed") && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setConfirmRetryBatch(b)}
                      >
                        Retry
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {batches.length === 0 && (
          <p className="py-8 text-center text-[#94a3b8]">Nenhum lote encontrado.</p>
        )}
        <div className="mt-4 flex justify-between">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
          >
            Anterior
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setPage((p) => p + 1)}
            disabled={batches.length < 50}
          >
            Próxima
          </Button>
        </div>
      </Card>

      <Card>
        <h2 className="mb-4 text-lg font-semibold">Anchors</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#334155] text-left text-[#94a3b8]">
                <th className="p-3">ID</th>
                <th className="p-3">Batch</th>
                <th className="p-3">Status</th>
                <th className="p-3">TX</th>
                <th className="p-3">Block</th>
                <th className="p-3"></th>
              </tr>
            </thead>
            <tbody>
              {anchors.map((a) => (
                <tr key={a.id} className="border-b border-[#334155]/50">
                  <td className="p-3 font-mono text-[#94a3b8]">{a.id.slice(0, 8)}...</td>
                  <td className="p-3 font-mono text-[#94a3b8]">{a.batch_id.slice(0, 8)}...</td>
                  <td className="p-3">
                    <span className={statusColor(a.status)}>{a.status}</span>
                  </td>
                  <td className="p-3">
                    {a.transaction_id ? (
                      <a
                        href={EXPLORER_URL + a.transaction_id}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:underline"
                      >
                        {a.transaction_id.slice(0, 10)}...
                      </a>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td className="p-3 text-[#94a3b8]">{a.block_number ?? "-"}</td>
                  <td className="p-3">
                    {(a.status === "failed") && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setConfirmRetryAnchor(a)}
                      >
                        Retry
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {anchors.length === 0 && (
          <p className="py-6 text-center text-[#94a3b8]">Nenhum anchor encontrado.</p>
        )}
      </Card>

      {/* Batch detail modal */}
      {detailBatch && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl border border-[#334155] bg-[#1e293b] p-6 shadow-xl">
            <div className="mb-4 flex justify-between">
              <h2 className="text-lg font-semibold">Detalhes do Lote</h2>
              <button
                onClick={() => {
                  setDetailBatch(null);
                  setMerkleTree(null);
                }}
                className="rounded p-1 text-[#94a3b8] hover:bg-[#334155]"
              >
                ✕
              </button>
            </div>
            <div className="space-y-3 text-sm">
              <p><span className="text-[#94a3b8]">ID:</span> <span className="font-mono text-[#f8fafc]">{detailBatch.id}</span></p>
              <p><span className="text-[#94a3b8]">Status:</span> <span className={statusColor(detailBatch.status)}>{detailBatch.status}</span></p>
              <p><span className="text-[#94a3b8]">Produtos:</span> {detailBatch.product_count}</p>
              <p><span className="text-[#94a3b8]">Merkle Root:</span></p>
              <pre className="break-all rounded bg-[#0f172a] p-3 font-mono text-xs text-[#94a3b8]">
                {detailBatch.merkle_root ?? "-"}
              </pre>
              <div className="border-t border-[#334155] pt-3">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={loadMerkleTree}
                  disabled={merkleLoading}
                >
                  {merkleLoading ? "Carregando..." : "Ver árvore Merkle"}
                </Button>
                {merkleTree && (
                  <div className="mt-4">
                    <MerkleTreeView
                      tree={merkleTree.tree}
                      merkleRoot={merkleTree.merkle_root}
                      leavesCount={merkleTree.leaves?.length ?? 0}
                    />
                  </div>
                )}
              </div>
              <p><span className="text-[#94a3b8]">Transação Blockchain:</span></p>
              {detailBatch.blockchain_tx ? (
                <a
                  href={EXPLORER_URL + detailBatch.blockchain_tx}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="break-all text-blue-400 hover:underline"
                >
                  {detailBatch.blockchain_tx}
                </a>
              ) : (
                <span className="text-[#94a3b8]">-</span>
              )}
              {detailBatch.error && (
                <p><span className="text-[#94a3b8]">Erro:</span> <span className="text-red-400">{detailBatch.error}</span></p>
              )}
            </div>
          </div>
        </div>
      )}

      <ConfirmDialog
        open={!!confirmRetryBatch}
        title="Retentar batch"
        message={confirmRetryBatch ? `Retentar processamento do lote ${confirmRetryBatch.id.slice(0, 8)}...?` : ""}
        confirmLabel="Retentar"
        variant="warning"
        onConfirm={handleRetryBatch}
        onCancel={() => setConfirmRetryBatch(null)}
        loading={retryLoading}
      />

      <ConfirmDialog
        open={!!confirmRetryAnchor}
        title="Retentar anchor"
        message={confirmRetryAnchor ? `Retentar ancoragem ${confirmRetryAnchor.id.slice(0, 8)}...?` : ""}
        confirmLabel="Retentar"
        variant="warning"
        onConfirm={handleRetryAnchor}
        onCancel={() => setConfirmRetryAnchor(null)}
        loading={retryLoading}
      />
    </div>
  );
}
