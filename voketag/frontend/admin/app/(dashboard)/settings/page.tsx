"use client";

import { useCallback, useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import {
  getGodModeState,
  setKillSwitch,
  setInvestigationMode,
  setMaxAlertMode,
  setRiskLimit,
  blockCountry,
  unblockCountry,
  invalidateAllJwt,
} from "@/lib/api-client";

export default function SettingsPage() {
  const [state, setState] = useState<{
    kill_switch: boolean;
    investigation_mode: boolean;
    max_alert_mode: boolean;
    risk_limit: number;
    blocked_countries: string[];
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [riskLimitInput, setRiskLimitInput] = useState("70");
  const [countryInput, setCountryInput] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [confirmInvalidate, setConfirmInvalidate] = useState(false);

  const loadState = useCallback(async () => {
    setLoading(true);
    try {
      const s = await getGodModeState();
      setState(s);
      setRiskLimitInput(String(s.risk_limit));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
      setState(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadState();
  }, [loadState]);

  async function handleKillSwitch(active: boolean) {
    setActionLoading(true);
    try {
      await setKillSwitch(active);
      loadState();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleInvestigation(active: boolean) {
    setActionLoading(true);
    try {
      await setInvestigationMode(active);
      loadState();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleMaxAlert(active: boolean) {
    setActionLoading(true);
    try {
      await setMaxAlertMode(active);
      loadState();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleRiskLimit() {
    const limit = parseInt(riskLimitInput, 10);
    if (isNaN(limit) || limit < 0 || limit > 100) return;
    setActionLoading(true);
    try {
      await setRiskLimit(limit);
      loadState();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleBlockCountry() {
    if (!countryInput.trim()) return;
    const code = countryInput.trim().toUpperCase().slice(0, 2);
    setActionLoading(true);
    try {
      await blockCountry(code);
      setCountryInput("");
      loadState();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleUnblockCountry(code: string) {
    setActionLoading(true);
    try {
      await unblockCountry(code);
      loadState();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleInvalidateJwt() {
    setActionLoading(true);
    try {
      await invalidateAllJwt();
      setConfirmInvalidate(false);
      window.location.href = "/login";
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro");
    } finally {
      setActionLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[200px] items-center justify-center py-12">
        <p className="text-[#94a3b8]">Carregando...</p>
      </div>
    );
  }

  if (!state) {
    return (
      <div>
        <h1 className="mb-6 text-2xl font-bold text-[#f8fafc]">Configurações</h1>
        {error && (
          <div className="mb-6 rounded-lg border border-red-800 bg-red-900/30 p-4 text-red-300">
            {error}
          </div>
        )}
        <p className="text-[#94a3b8]">Acesso God Mode requer role super_admin.</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="font-display mb-6 text-2xl font-bold text-[#f8fafc]">Configurações (God Mode)</h1>

      {error && (
        <div className="mb-6 rounded-lg border border-red-800 bg-red-900/30 p-4 text-red-300">
          {error}
        </div>
      )}

      <div className="space-y-6">
        <Card>
          <h2 className="font-display mb-4 text-lg font-semibold">Kill Switch</h2>
          <p className="mb-4 text-sm text-[#94a3b8]">
            Desativa o sistema de forma emergencial. Em caso de comprometimento, use esta opção.
          </p>
          <Button
            variant={state.kill_switch ? "primary" : "danger"}
            size="sm"
            onClick={() => handleKillSwitch(!state.kill_switch)}
            disabled={actionLoading}
          >
            {state.kill_switch ? "Desativar Kill Switch" : "Ativar Kill Switch"}
          </Button>
          {state.kill_switch && (
            <span className="ml-2 text-amber-400">⚠️ ATIVO</span>
          )}
        </Card>

        <Card>
          <h2 className="font-display mb-4 text-lg font-semibold">Modo Investigação</h2>
          <p className="mb-4 text-sm text-[#94a3b8]">
            Ativa modo de investigação para análise de incidentes.
          </p>
          <Button
            variant={state.investigation_mode ? "primary" : "secondary"}
            size="sm"
            onClick={() => handleInvestigation(!state.investigation_mode)}
            disabled={actionLoading}
          >
            {state.investigation_mode ? "Desativar" : "Ativar"} Modo Investigação
          </Button>
        </Card>

        <Card>
          <h2 className="font-display mb-4 text-lg font-semibold">Modo Alerta Máximo</h2>
          <p className="mb-4 text-sm text-[#94a3b8]">
            Eleva sensibilidade de detecção ao máximo.
          </p>
          <Button
            variant={state.max_alert_mode ? "danger" : "secondary"}
            size="sm"
            onClick={() => handleMaxAlert(!state.max_alert_mode)}
            disabled={actionLoading}
          >
            {state.max_alert_mode ? "Desativar" : "Ativar"} Alerta Máximo
          </Button>
        </Card>

        <Card>
          <h2 className="font-display mb-4 text-lg font-semibold">Limite de Risco Global (0-100)</h2>
          <p className="mb-4 text-sm text-[#94a3b8]">
            Score mínimo para considerar suspeito e bloquear.
          </p>
          <div className="flex gap-2">
            <input
              type="number"
              min={0}
              max={100}
              value={riskLimitInput}
              onChange={(e) => setRiskLimitInput(e.target.value)}
              className="w-24 rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-sm text-[#f8fafc]"
            />
            <Button variant="secondary" size="sm" onClick={handleRiskLimit} disabled={actionLoading}>
              Salvar
            </Button>
          </div>
        </Card>

        <Card>
          <h2 className="font-display mb-4 text-lg font-semibold">Bloquear País</h2>
          <p className="mb-4 text-sm text-[#94a3b8]">
            Bloqueie scans de países específicos (código ISO 2: BR, US, etc.).
          </p>
          <div className="mb-4 flex gap-2">
            <input
              type="text"
              placeholder="Ex: BR"
              value={countryInput}
              onChange={(e) => setCountryInput(e.target.value.toUpperCase())}
              maxLength={2}
              className="w-24 rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-sm text-[#f8fafc] uppercase"
            />
            <Button variant="secondary" size="sm" onClick={handleBlockCountry} disabled={actionLoading || !countryInput.trim()}>
              Bloquear
            </Button>
          </div>
          {state.blocked_countries.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {state.blocked_countries.map((c) => (
                <span
                  key={c}
                  className="inline-flex items-center gap-1 rounded bg-red-900/50 px-2 py-1 text-sm"
                >
                  {c}
                  <button
                    onClick={() => handleUnblockCountry(c)}
                    disabled={actionLoading}
                    className="text-red-300 hover:text-white"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <h2 className="font-display mb-4 text-lg font-semibold">Invalidar Todos os JWT</h2>
          <p className="mb-4 text-sm text-[#94a3b8]">
            Invalida todas as sessões. Todos os usuários precisarão fazer login novamente.
          </p>
          <Button variant="danger" size="sm" onClick={() => setConfirmInvalidate(true)} disabled={actionLoading}>
            Invalidar Todas as Sessões
          </Button>
        </Card>
      </div>

      <ConfirmDialog
        open={confirmInvalidate}
        title="Invalidar todas as sessões"
        message="Todos os usuários serão deslogados. Continuar?"
        confirmLabel="Sim, invalidar"
        variant="danger"
        onConfirm={handleInvalidateJwt}
        onCancel={() => setConfirmInvalidate(false)}
        loading={actionLoading}
      />
    </div>
  );
}
