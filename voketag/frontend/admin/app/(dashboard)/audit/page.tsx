"use client";

import { useCallback, useEffect, useState } from "react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/Table";
import { getAuditLogs, exportAuditLogs } from "@/lib/api-client";
import { useDebounce } from "@/hooks/useDebounce";
import { useAuditLogStream } from "@/hooks/useAuditLogStream";

interface AuditEntry {
  id?: string;
  entity_type?: string;
  entity_id?: string;
  action?: string;
  user_id?: string;
  changes?: string;
  ip_address?: string;
  created_at?: string;
  [key: string]: unknown;
}

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [entityType, setEntityType] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [search, setSearch] = useState("");
  const searchDebounced = useDebounce(search, 400);
  const [exporting, setExporting] = useState(false);
  const [liveMode, setLiveMode] = useState(false);
  const { connect, disconnect, isConnected } = useAuditLogStream();

  const loadLogs = useCallback(() => {
    setLoading(true);
    getAuditLogs({
      skip: page * 50,
      limit: 50,
      entity_type: entityType || undefined,
      action: actionFilter || undefined,
      search: searchDebounced || undefined,
    })
      .then((r) => setLogs(Array.isArray(r) ? r : []))
      .catch((e) => setError(e instanceof Error ? e.message : "Erro"))
      .finally(() => setLoading(false));
  }, [page, entityType, actionFilter, searchDebounced]);

  useEffect(() => {
    if (!liveMode) loadLogs();
  }, [loadLogs, liveMode]);

  useEffect(() => {
    if (liveMode) {
      connect({
        entityType: entityType || undefined,
        action: actionFilter || undefined,
        onLog: (log) => {
          setLogs((prev) => [log, ...prev.filter((l) => (l.id as string) !== (log.id as string))]);
        },
        onError: (e) => setError(e.message),
      });
      return () => disconnect();
    }
  }, [liveMode, entityType, actionFilter, connect, disconnect]);

  async function handleExport(format: "csv" | "json") {
    setExporting(true);
    try {
      const blob = await exportAuditLogs(format, entityType || undefined);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit_logs.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao exportar");
    } finally {
      setExporting(false);
    }
  }

  return (
    <div>
      <h1 className="font-display mb-6 text-2xl font-bold text-[#f8fafc]">Auditoria</h1>

      {error && (
        <div className="mb-6 rounded-lg border border-red-800 bg-red-900/30 p-4 text-red-300">
          {error}
        </div>
      )}

      <Card className="mb-6">
        <div className="mb-4 flex flex-wrap gap-4">
          <input
            type="text"
            placeholder="Busca full-text..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
            className="min-w-[200px] rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-sm text-[#f8fafc] placeholder-[#64748b] focus:border-blue-500 focus:outline-none"
          />
          <select
            value={entityType}
            onChange={(e) => {
              setEntityType(e.target.value);
              setPage(0);
            }}
            className="rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-sm text-[#f8fafc] focus:border-blue-500 focus:outline-none"
          >
            <option value="">Todos os tipos</option>
            <option value="admin_user">Admin User</option>
          </select>
          <select
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(0);
            }}
            className="rounded-lg border border-[#334155] bg-[#0f172a] px-3 py-2 text-sm text-[#f8fafc] focus:border-blue-500 focus:outline-none"
          >
            <option value="">Todas as ações</option>
            <option value="create">Create</option>
            <option value="update">Update</option>
            <option value="delete">Delete</option>
          </select>
          <Button
            variant={liveMode ? "primary" : "secondary"}
            size="sm"
            onClick={() => {
              if (!liveMode) {
                loadLogs();
                setError(null);
              }
              setLiveMode((v) => !v);
            }}
          >
            {liveMode ? (isConnected ? "● Ao vivo" : "Conectando...") : "Modo ao vivo"}
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => handleExport("csv")}
            disabled={exporting}
          >
            {exporting ? "..." : "Exportar CSV"}
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => handleExport("json")}
            disabled={exporting}
          >
            Exportar JSON
          </Button>
        </div>
      </Card>

      <Card>
        {loading ? (
          <p className="py-8 text-center text-[#94a3b8]">Carregando...</p>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Data</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Ação</TableHead>
                  <TableHead>Entidade ID</TableHead>
                  <TableHead>Usuário</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log, i) => (
                  <TableRow key={(log.id as string) ?? i}>
                    <TableCell className="text-[#94a3b8]">
                      {log.created_at
                        ? new Date(log.created_at).toLocaleString("pt-BR")
                        : "-"}
                    </TableCell>
                    <TableCell className="text-[#f8fafc]">
                      {log.entity_type ?? "-"}
                    </TableCell>
                    <TableCell>{log.action ?? "-"}</TableCell>
                    <TableCell className="font-mono text-xs text-[#94a3b8]">
                      {log.entity_id ?? "-"}
                    </TableCell>
                    <TableCell className="text-[#94a3b8]">
                      {log.user_id ?? "-"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {logs.length === 0 && (
              <p className="py-8 text-center text-[#94a3b8]">Nenhum log encontrado.</p>
            )}
            {!liveMode && (
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
                disabled={logs.length < 50}
              >
                Próxima
              </Button>
            </div>
            )}
          </>
        )}
      </Card>
    </div>
  );
}
