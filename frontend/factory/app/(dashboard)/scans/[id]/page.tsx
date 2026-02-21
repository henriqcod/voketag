"use client";

import Link from "next/link";
import { useScanDetail } from "@/hooks/useScans";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";

const RISK_VARIANTS = {
  low: "success" as const,
  medium: "warning" as const,
  high: "alert" as const,
};

export default function ScanDetailPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const { data: scan, isLoading, error } = useScanDetail(id);

  if (isLoading || !scan) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Link href="/scans" className="text-sm text-graphite-500 hover:text-graphite-900 dark:hover:text-white">
          ← Voltar
        </Link>
        <p className="text-alert">Scan não encontrado.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <Link href="/scans" className="text-sm text-graphite-500 hover:text-graphite-900 dark:hover:text-white">
            ← Voltar
          </Link>
          <h2 className="mt-2 text-xl font-semibold text-graphite-900 dark:text-white">Detalhe do scan</h2>
        </div>
        <div className="flex gap-2">
          <Badge variant={RISK_VARIANTS[scan.risk_status] ?? "default"}>{scan.risk_status}</Badge>
          {scan.is_duplicate && <Badge variant="alert">Duplicata</Badge>}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <h3 className="font-medium text-graphite-900 dark:text-white">Informações</h3>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-graphite-500 dark:text-graphite-400">Serial</p>
              <p className="mt-1 font-mono text-graphite-800 dark:text-graphite-200">{scan.serial_number}</p>
            </div>
            <div>
              <p className="text-sm text-graphite-500 dark:text-graphite-400">Lote</p>
              <p className="mt-1 font-mono text-graphite-800 dark:text-graphite-200">{scan.batch_id}</p>
            </div>
            <div>
              <p className="text-sm text-graphite-500 dark:text-graphite-400">Horário</p>
              <p className="mt-1 text-graphite-700 dark:text-graphite-300">
                {new Date(scan.scanned_at).toLocaleString("pt-BR")}
              </p>
            </div>
            <div>
              <p className="text-sm text-graphite-500 dark:text-graphite-400">País</p>
              <p className="mt-1 text-graphite-700 dark:text-graphite-300">{scan.country ?? "—"}</p>
            </div>
            <div>
              <p className="text-sm text-graphite-500 dark:text-graphite-400">Dispositivo</p>
              <p className="mt-1 text-graphite-700 dark:text-graphite-300">{scan.device ?? "—"}</p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="font-medium text-graphite-900 dark:text-white">Status de risco</h3>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-graphite-500 dark:text-graphite-400">Nível</p>
              <Badge variant={RISK_VARIANTS[scan.risk_status] ?? "default"} className="mt-1">
                {scan.risk_status}
              </Badge>
            </div>
            {scan.is_duplicate && (
              <div>
                <p className="text-sm text-graphite-500 dark:text-graphite-400">Alerta</p>
                <p className="mt-1 text-amber-600 dark:text-amber-400">
                  Este serial foi escaneado mais de uma vez.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
