"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";
import {
  getAnalyticsFraud,
  getAnalyticsGeographic,
  getAnalyticsTrends,
  getAnalyticsHeatmap,
  getAnalyticsScansPerMinute,
  getAnalyticsFraudsPerHour,
  getAnalyticsRiskEvolution,
} from "@/lib/api-client";

const DAYS = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
const HEATMAP_COLORS = ["#0f172a", "#1e3a5f", "#2563eb", "#f59e0b", "#ef4444"];

function getHeatmapColor(value: number, max: number) {
  if (max === 0) return HEATMAP_COLORS[0];
  const idx = Math.min(
    Math.floor((value / max) * (HEATMAP_COLORS.length - 1)) + 1,
    HEATMAP_COLORS.length - 1
  );
  return HEATMAP_COLORS[idx];
}

export default function AntifraudPage() {
  const [fraud, setFraud] = useState<Record<string, unknown> | null>(null);
  const [geo, setGeo] = useState<Record<string, unknown> | null>(null);
  const [trends, setTrends] = useState<Record<string, unknown> | null>(null);
  const [heatmap, setHeatmap] = useState<{ day: number; hour: number; count: number }[]>([]);
  const [scansPerMin, setScansPerMin] = useState<{ minute: string; count: number }[]>([]);
  const [fraudsPerHour, setFraudsPerHour] = useState<{ hour: string; count: number }[]>([]);
  const [riskEvo, setRiskEvo] = useState<{ date: string; avg_risk: number; count: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(7);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [f, g, t, h, spm, fph, re] = await Promise.all([
          getAnalyticsFraud({ days: 30, min_risk_score: 70 }),
          getAnalyticsGeographic(30),
          getAnalyticsTrends(30),
          getAnalyticsHeatmap({ days, min_risk: 50 }),
          getAnalyticsScansPerMinute(24),
          getAnalyticsFraudsPerHour(7),
          getAnalyticsRiskEvolution(30),
        ]);
        setFraud(f);
        setGeo(g);
        setTrends(t);
        setHeatmap((h as { heatmap?: { day: number; hour: number; count: number }[] }).heatmap ?? []);
        setScansPerMin((spm as { scans_per_minute?: { minute: string; count: number }[] }).scans_per_minute ?? []);
        setFraudsPerHour((fph as { frauds_per_hour?: { hour: string; count: number }[] }).frauds_per_hour ?? []);
        setRiskEvo((re as { risk_evolution?: { date: string; avg_risk: number; count: number }[] }).risk_evolution ?? []);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Erro");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [days]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-[#94a3b8]">Carregando...</p>
      </div>
    );
  }

  const heatmapGrid: { day: number; hour: number; count: number }[] = [];
  for (let d = 0; d < 7; d++) {
    for (let h = 0; h < 24; h++) {
      const found = heatmap.find((x) => x.day === d && x.hour === h);
      heatmapGrid.push({ day: d, hour: h, count: found?.count ?? 0 });
    }
  }
  const maxHeat = Math.max(...heatmapGrid.map((x) => x.count), 1);

  const scansChartData = scansPerMin.map((x) => ({
    time: x.minute ? new Date(x.minute).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : "",
    count: x.count,
  }));

  const fraudsChartData = fraudsPerHour.map((x) => ({
    time: x.hour ? new Date(x.hour).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit" }) : "",
    count: x.count,
  }));

  const riskChartData = riskEvo.map((x) => ({
    date: x.date,
    risk: x.avg_risk,
    scans: x.count,
  }));

  const byCountry = (geo?.by_country as { country: string; count: number }[]) ?? [];
  const scansByDay = (trends?.scans_by_day as { date: string; count: number }[]) ?? [];

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-[#f8fafc]">Antifraude</h1>

      {error && (
        <div className="mb-6 rounded-lg border border-red-800 bg-red-900/30 p-4 text-red-300">
          {error}
        </div>
      )}

      <div className="mb-6 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <p className="mb-1 text-xs text-[#94a3b8]">Scans suspeitos (risk ≥ 70)</p>
          <p className="text-2xl font-bold text-red-400">
            {(fraud?.high_risk_scans as number) ?? 0}
          </p>
        </Card>
        <Card>
          <p className="mb-1 text-xs text-[#94a3b8]">Scans inválidos</p>
          <p className="text-2xl font-bold text-amber-400">
            {(fraud?.invalid_scans_count as number) ?? 0}
          </p>
        </Card>
        <Card>
          <p className="mb-1 text-xs text-[#94a3b8]">Países (geo)</p>
          <p className="text-2xl font-bold text-blue-400">
            {byCountry.length}
          </p>
        </Card>
        <Card>
          <p className="mb-1 text-xs text-[#94a3b8]">Produtos alto scan</p>
          <p className="text-2xl font-bold text-cyan-400">
            {((fraud?.products_with_high_scan_count as unknown[])?.length ?? 0)}
          </p>
        </Card>
      </div>

      <div className="mb-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="mb-4 text-lg font-semibold">Heatmap – scans suspeitos (hora × dia)</h2>
          <div className="flex gap-1">
            <select
              value={days}
              onChange={(e) => setDays(parseInt(e.target.value, 10))}
              className="mb-2 rounded border border-[#334155] bg-[#0f172a] px-2 py-1 text-sm text-[#f8fafc]"
            >
              <option value={3}>3 dias</option>
              <option value={7}>7 dias</option>
              <option value={14}>14 dias</option>
            </select>
          </div>
          <div className="overflow-x-auto">
            <div className="inline-grid gap-0.5" style={{ gridTemplateColumns: "repeat(24, 1fr)" }}>
              {Array.from({ length: 7 }).map((_, d) =>
                Array.from({ length: 24 }).map((_, h) => {
                  const cell = heatmapGrid.find((x) => x.day === d && x.hour === h);
                  const count = cell?.count ?? 0;
                  return (
                    <div
                      key={`${d}-${h}`}
                      className="h-4 w-4 rounded-sm"
                      style={{ backgroundColor: getHeatmapColor(count, maxHeat) }}
                      title={`${DAYS[d]} ${h}h: ${count}`}
                    />
                  );
                })
              )}
            </div>
          </div>
          <p className="mt-2 text-xs text-[#94a3b8]">
            Linhas: Dom–Sáb. Colunas: 0h–23h. Cores: intensidade de scans suspeitos.
          </p>
        </Card>

        <Card>
          <h2 className="mb-4 text-lg font-semibold">Padrões – distribuição por país</h2>
          <div className="h-64">
            {byCountry.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={byCountry.slice(0, 10)} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="country" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                  <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155" }} />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="flex h-full items-center justify-center text-[#94a3b8]">Sem dados de países</p>
            )}
          </div>
        </Card>
      </div>

      <div className="mb-6 grid gap-6 lg:grid-cols-3">
        <Card>
          <h2 className="mb-4 text-lg font-semibold">Scans/min (últimas 24h)</h2>
          <div className="h-48">
            {scansChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={scansChartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="time" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
                  <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155" }} />
                  <Line type="monotone" dataKey="count" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="flex h-full items-center justify-center text-[#94a3b8]">Sem dados</p>
            )}
          </div>
        </Card>

        <Card>
          <h2 className="mb-4 text-lg font-semibold">Fraudes/hora (últimos 7 dias)</h2>
          <div className="h-48">
            {fraudsChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={fraudsChartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="time" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} />
                  <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155" }} />
                  <Bar dataKey="count" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="flex h-full items-center justify-center text-[#94a3b8]">Sem fraudes no período</p>
            )}
          </div>
        </Card>

        <Card>
          <h2 className="mb-4 text-lg font-semibold">Evolução do risco (30 dias)</h2>
          <div className="h-48">
            {riskChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={riskChartData} margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 10 }} domain={[0, 100]} />
                  <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155" }} />
                  <Line type="monotone" dataKey="risk" stroke="#f59e0b" strokeWidth={2} dot={false} name="Risco médio" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="flex h-full items-center justify-center text-[#94a3b8]">Sem dados</p>
            )}
          </div>
        </Card>
      </div>

      <Card>
        <h2 className="mb-4 text-lg font-semibold">Scans por dia (tendências)</h2>
        <div className="h-64">
          {scansByDay.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={scansByDay.map((x) => ({ date: x.date, scans: x.count }))}
                margin={{ top: 5, right: 5, left: 5, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155" }} />
                <Line type="monotone" dataKey="scans" stroke="#10b981" strokeWidth={2} dot={false} name="Scans" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="flex h-full items-center justify-center text-[#94a3b8]">Sem dados</p>
          )}
        </div>
      </Card>
    </div>
  );
}
