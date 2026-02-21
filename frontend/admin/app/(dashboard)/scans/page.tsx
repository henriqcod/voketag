"use client";

import { useCallback, useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import {
  listScans,
  blockScan,
  observationScan,
  markFraudScan,
  updateScanStatus,
  type ScanItem,
} from "@/lib/api-client";

const POLL_INTERVAL_MS = 8000;

export default function ScansPage() {
  const [scans, setScans] = useState<ScanItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [country, setCountry] = useState("");
  const [productId, setProductId] = useState("");
  const [riskMin, setRiskMin] = useState("");
  const [riskMax, setRiskMax] = useState("");
  const [periodDays, setPeriodDays] = useState("30");
  const [statusFilter, setStatusFilter] = useState("");
  const [actionTarget, setActionTarget] = useState<{ tagId: string; action: "block" | "observation" | "fraud" | "ok" } | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const loadScans = useCallback(async () => {
    setLoading(true);
    try {
      const res = await listScans({
        skip: page * 50,
        limit: 50,
        country: country || undefined,
        product_id: productId || undefined,
        risk_min: riskMin ? parseInt(riskMin, 10) : undefined,
        risk_max: riskMax ? parseInt(riskMax, 10) : undefined,
        days: periodDays ? parseInt(periodDays, 10) : 30,
        status: statusFilter || undefined,
      });
      setScans(res.scans);
      setTotal(res.total);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar");
    } finally {
      setLoading(false);
    }
  }, [page, country, productId, riskMin, riskMax, periodDays, statusFilter]);

  useEffect(() => {
    loadScans();
  }, [loadScans]);

  useEffect(() => {
    const t = setInterval(loadScans, POLL_INTERVAL_MS);
    return () => clearInterval(t);
  }, [loadScans]);

  async function handleAction() {
    if (!actionTarget) return;
    setActionLoading(true);
    try {
      if (actionTarget.action === "block") await blockScan(actionTarget.tagId);
      else if (actionTarget.action === "observation") await observationScan(actionTarget.tagId);
      else if (actionTarget.action === "fraud") await markFraudScan(actionTarget.tagId);
      else await updateScanStatus(actionTarget.tagId, "ok");
      setActionTarget(null);
      loadScans();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro na ação");
    } finally {
      setActionLoading(false);
    }
  }

  function statusColor(s: string) {
    if (s === "blocked" || s === "fraud") return "text-red-400";
    if (s === "observation") return "text-amber-400";
    return "text-emerald-400";
  }

  if (loading && scans.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-[#94a3b8]">Carregando...</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-[#f8fafc]">Scans (tempo real)</h1>

      {error && (
        <div className="mb-6 rounded-lg border border-red-800 bg-red-900/30 p-4 text-red-300">
          {error}
        </div>
      )}

      <Card className="mb-6">
        <h2 className="mb-4 text-lg font-semibold">Filtros</h2>
        <div className="mb-4 flex flex-wrap gap-3">
          <input
            type="text"
            placeholder="País (ex: BR)"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            className="rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-sm text-[#f8fafc] w-24"
          />
          <input
            type="text"
            placeholder="ID Produto"
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            className="rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-sm text-[#f8fafc] w-48"
          />
          <input
            type="number"
            placeholder="Risco min (0-100)"
            value={riskMin}
            onChange={(e) => setRiskMin(e.target.value)}
            min={0}
            max={100}
            className="rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-sm text-[#f8fafc] w-28"
          />
          <input
            type="number"
            placeholder="Risco max"
            value={riskMax}
            onChange={(e) => setRiskMax(e.target.value)}
            min={0}
            max={100}
            className="rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-sm text-[#f8fafc] w-28"
          />
          <select
            value={periodDays}
            onChange={(e) => setPeriodDays(e.target.value)}
            className="rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-sm text-[#f8fafc]"
          >
            <option value="7">7 dias</option>
            <option value="14">14 dias</option>
            <option value="30">30 dias</option>
            <option value="90">90 dias</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-sm text-[#f8fafc]"
          >
            <option value="">Todos status</option>
            <option value="ok">OK</option>
            <option value="blocked">Bloqueado</option>
            <option value="observation">Em observação</option>
            <option value="fraud">Fraude</option>
          </select>
          <Button variant="secondary" size="sm" onClick={() => { setPage(0); loadScans(); }}>
            Aplicar
          </Button>
        </div>
      </Card>

      <Card>
        <div className="mb-2 flex justify-between">
          <h2 className="text-lg font-semibold">Tabela de Scans</h2>
          <span className="text-sm text-[#94a3b8]">Atualiza a cada {POLL_INTERVAL_MS / 1000}s</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#334155] text-left text-[#94a3b8]">
                <th className="p-3">Tag ID</th>
                <th className="p-3">Produto</th>
                <th className="p-3">País</th>
                <th className="p-3">Status</th>
                <th className="p-3">Risco</th>
                <th className="p-3">Scans</th>
                <th className="p-3">Válido</th>
                <th className="p-3">Última atualização</th>
                <th className="p-3">Ações</th>
              </tr>
            </thead>
            <tbody>
              {scans.map((s) => (
                <tr key={s.tag_id} className="border-b border-[#334155]/50">
                  <td className="p-3 font-mono text-xs text-[#94a3b8]">{s.tag_id.slice(0, 8)}...</td>
                  <td className="p-3">{s.product_name || s.product_token || "-"}</td>
                  <td className="p-3">{s.country ?? "-"}</td>
                  <td className="p-3">
                    <span className={statusColor(s.status)}>{s.status}</span>
                  </td>
                  <td className="p-3">
                    <span className={s.risk_score >= 70 ? "text-red-400" : s.risk_score >= 40 ? "text-amber-400" : "text-[#94a3b8]"}>
                      {s.risk_score}
                    </span>
                  </td>
                  <td className="p-3 text-[#94a3b8]">{s.scan_count}</td>
                  <td className="p-3">{s.valid ? "Sim" : "Não"}</td>
                  <td className="p-3 text-[#94a3b8]">
                    {s.updated_at ? new Date(s.updated_at).toLocaleString("pt-BR") : "-"}
                  </td>
                  <td className="p-3">
                    <div className="flex gap-1">
                      {s.status !== "blocked" && (
                        <Button variant="secondary" size="sm" onClick={() => setActionTarget({ tagId: s.tag_id, action: "block" })}>
                          Bloquear
                        </Button>
                      )}
                      {s.status !== "observation" && (
                        <Button variant="secondary" size="sm" onClick={() => setActionTarget({ tagId: s.tag_id, action: "observation" })}>
                          Observação
                        </Button>
                      )}
                      {s.status !== "fraud" && (
                        <Button variant="secondary" size="sm" onClick={() => setActionTarget({ tagId: s.tag_id, action: "fraud" })}>
                          Fraude
                        </Button>
                      )}
                      {(s.status === "blocked" || s.status === "observation" || s.status === "fraud") && (
                        <Button variant="secondary" size="sm" onClick={() => setActionTarget({ tagId: s.tag_id, action: "ok" })}>
                          Liberar
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {scans.length === 0 && (
          <p className="py-8 text-center text-[#94a3b8]">Nenhum scan encontrado.</p>
        )}
        <div className="mt-4 flex justify-between">
          <span className="text-sm text-[#94a3b8]">Total: {total}</span>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}>
              Anterior
            </Button>
            <Button variant="secondary" size="sm" onClick={() => setPage((p) => p + 1)} disabled={scans.length < 50}>
              Próxima
            </Button>
          </div>
        </div>
      </Card>

      <ConfirmDialog
        open={!!actionTarget}
        title={actionTarget?.action === "block" ? "Bloquear código" : actionTarget?.action === "observation" ? "Colocar em observação" : actionTarget?.action === "fraud" ? "Marcar como fraude" : "Liberar código"}
        message={
          actionTarget
            ? actionTarget.action === "ok"
              ? `Liberar o código ${actionTarget.tagId.slice(0, 8)}...?`
              : `Confirmar ação para ${actionTarget.tagId.slice(0, 8)}...?`
            : ""
        }
        confirmLabel="Confirmar"
        variant="warning"
        onConfirm={handleAction}
        onCancel={() => setActionTarget(null)}
        loading={actionLoading}
      />
    </div>
  );
}
