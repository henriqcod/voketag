"use client";

import { useState, useCallback } from "react";
import { useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/lib/toast-context";
import {
  createBatch,
  getBatchStatus,
  uploadBatchCsv,
  type BatchCreateResponse,
} from "@/lib/api/batches";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";

type CsvRow = Record<string, string>;

function parseCsv(text: string): CsvRow[] {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) return [];
  const headers = lines[0].split(",").map((h) => h.trim().toLowerCase().replace(/\s/g, "_"));
  const rows: CsvRow[] = [];
  for (let i = 1; i < lines.length; i++) {
    const vals = lines[i].split(",").map((v) => v.trim());
    const row: CsvRow = {};
    headers.forEach((h, j) => {
      row[h] = vals[j] ?? "";
    });
    rows.push(row);
  }
  return rows;
}

function validateCsv(rows: CsvRow[]): {
  valid: number;
  invalid: number;
  duplicates: number;
  errors: string[];
  riskScore: number;
} {
  const errors: string[] = [];
  const serials = new Set<string>();
  let invalid = 0;
  let duplicates = 0;

  rows.forEach((row, i) => {
    const sn = row.serial_number?.trim();
    if (!sn) {
      invalid++;
      errors.push(`Linha ${i + 2}: serial_number vazio`);
    } else if (serials.has(sn)) {
      duplicates++;
    } else {
      serials.add(sn);
    }
    if (!row.product_code?.trim()) {
      invalid++;
      if (errors.length < 10) errors.push(`Linha ${i + 2}: product_code vazio`);
    }
  });

  const total = rows.length;
  const riskScore = total > 0
    ? Math.min(100, Math.round(((invalid + duplicates) / total) * 100))
    : 0;

  return {
    valid: total - invalid - duplicates,
    invalid,
    duplicates,
    errors: errors.slice(0, 10),
    riskScore,
  };
}

type AnchorFormValues = { confirmIrreversibility: boolean };

export default function AnchorPage() {
  const [file, setFile] = useState<File | null>(null);
  const [parsedRows, setParsedRows] = useState<CsvRow[]>([]);
  const [validation, setValidation] = useState<ReturnType<typeof validateCsv> | null>(null);
  const [anchorResult, setAnchorResult] = useState<BatchCreateResponse | null>(null);
  const [batchStatus, setBatchStatus] = useState<{ merkle_root?: string; blockchain_tx?: string } | null>(null);
  const [progress, setProgress] = useState(0);
  const [statusLog, setStatusLog] = useState<string[]>([]);
  const [showConfirm, setShowConfirm] = useState(false);
  const { success: toastSuccess, error: toastError } = useToast();

  const { register, handleSubmit: rhfSubmit } = useForm<AnchorFormValues>();

  const addLog = useCallback((msg: string) => {
    setStatusLog((prev) => [...prev, `${new Date().toLocaleTimeString()} - ${msg}`]);
  }, []);

  const queryClient = useQueryClient();
  const createMutation = useMutation({
    mutationFn: createBatch,
    onSuccess: async (res) => {
      addLog(`Lote criado: ${res.batch_id}`);
      addLog(`Job: ${res.job_id}`);
      addLog(`Rede de validação: principal`);
      setAnchorResult(res);
      if (file) {
        try {
          addLog("Enviando CSV...");
          await uploadMutation.mutateAsync({ batchId: res.batch_id, file });
          addLog("CSV enviado. Processando...");
        } catch (e) {
          addLog(`Erro no upload: ${String(e)}`);
        }
      }
      pollStatus(res.batch_id);
    },
    onError: (e) => {
      addLog(`Erro: ${String(e)}`);
      toastError(String(e));
    },
  });

  const uploadMutation = useMutation({
    mutationFn: ({ batchId, file }: { batchId: string; file: File }) =>
      uploadBatchCsv(batchId, file),
  });

  const pollStatus = useCallback(
    async (batchId: string) => {
      setProgress(10);
      let attempts = 0;
      const maxAttempts = 120;
      const poll = async () => {
        try {
          const st = await getBatchStatus(batchId);
          addLog(`Status: ${st.status}`);
          setProgress(Math.min(90, 10 + attempts * 5));
          if (st.status === "completed") {
            setProgress(100);
            setBatchStatus({ merkle_root: st.merkle_root ?? undefined, blockchain_tx: st.blockchain_tx ?? undefined });
            addLog("Registro concluído. Chave de integridade: " + (st.merkle_root ?? "N/A"));
            addLog("Timestamp UTC: " + new Date().toISOString());
            queryClient.invalidateQueries({ queryKey: ["batches"] });
            queryClient.invalidateQueries({ queryKey: ["dashboard"] });
            toastSuccess("Registro concluído com sucesso.");
            return;
          }
          if (["failed", "anchor_failed"].includes(st.status)) {
            addLog("Falha: " + (st.error ?? "Desconhecido"));
            return;
          }
          attempts++;
          if (attempts < maxAttempts) setTimeout(poll, 3000);
        } catch (e) {
          addLog(`Erro ao consultar status: ${String(e)}`);
          if (attempts < maxAttempts) setTimeout(poll, 5000);
        }
      };
      poll();
    },
    [addLog, queryClient]
  );

  const handleFile = (f: File) => {
    setFile(f);
    setAnchorResult(null);
    setBatchStatus(null);
    setValidation(null);
    setProgress(0);
    setStatusLog([]);
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result ?? "");
      const rows = parseCsv(text);
      setParsedRows(rows);
      setValidation(validateCsv(rows));
    };
    reader.readAsText(f, "UTF-8");
  };

  const onAnchor = () => {
    if (!file || parsedRows.length === 0) return;
    setShowConfirm(false);
    addLog("Iniciando registro...");
    createMutation.mutate({
      product_count: parsedRows.length,
      product_name: file.name,
      metadata: { source: "csv", columns: Object.keys(parsedRows[0] ?? {}), metadata: "anchor" },
    });
  };

  const downloadNtagCsv = () => {
    if (!anchorResult || parsedRows.length === 0) return;
    const baseUrl = process.env.NEXT_PUBLIC_VERIFY_URL || "https://verify.voketag.com.br";
    const lines = [
      "serial_number,qr_code_url,nfc_payload,codigo_validacao,verification_url",
      ...parsedRows.map((r) => {
        const sn = r.serial_number ?? "";
        const url = `${baseUrl}/verify?serial=${encodeURIComponent(sn)}`;
        return `${sn},${url},${anchorResult.batch_id},${anchorResult.batch_id},${url}`;
      }),
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `ntag_export_${anchorResult.batch_id.slice(0, 8)}.csv`;
    a.click();
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f?.name.endsWith(".csv")) handleFile(f);
  };

  const onDragOver = (e: React.DragEvent) => e.preventDefault();

  return (
    <div className="space-y-6 animate-fade-in">
      <Card>
        <CardHeader>
          <h3 className="font-medium text-graphite-900 dark:text-white">Upload de CSV</h3>
          <p className="mt-1 text-sm text-graphite-500 dark:text-graphite-400">
            Campos: serial_number, product_code, batch_id, manufacture_date, metadata
          </p>
        </CardHeader>
        <CardContent>
          <div
            onDrop={onDrop}
            onDragOver={onDragOver}
            className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-graphite-300 bg-graphite-50 py-16 transition-colors hover:border-primary-500 dark:border-graphite-700 dark:bg-graphite-900/50 dark:hover:border-primary-500"
          >
            <input
              type="file"
              accept=".csv"
              className="hidden"
              id="csv-upload"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
              }}
            />
            <label
              htmlFor="csv-upload"
              className="cursor-pointer rounded-lg bg-primary-600 px-6 py-3 text-sm font-medium text-white hover:bg-primary-500"
            >
              {file ? `Arquivo: ${file.name}` : "Selecionar ou arrastar CSV"}
            </label>
          </div>

          {validation && (
            <div className="mt-6 grid gap-4 sm:grid-cols-4">
              <div className="rounded-lg border border-graphite-200 p-4 dark:border-graphite-800">
                <p className="text-sm text-graphite-500 dark:text-graphite-400">Total</p>
                <p className="text-2xl font-bold text-graphite-900 dark:text-white">{parsedRows.length}</p>
              </div>
              <div className="rounded-lg border border-graphite-200 p-4 dark:border-graphite-800">
                <p className="text-sm text-graphite-500 dark:text-graphite-400">Válidos</p>
                <p className="text-2xl font-bold text-success">{validation.valid}</p>
              </div>
              <div className="rounded-lg border border-graphite-200 p-4 dark:border-graphite-800">
                <p className="text-sm text-graphite-500 dark:text-graphite-400">Inválidos / Duplicados</p>
                <p className="text-2xl font-bold text-alert">
                  {validation.invalid} / {validation.duplicates}
                </p>
              </div>
              <div className="rounded-lg border border-graphite-200 p-4 dark:border-graphite-800">
                <p className="text-sm text-graphite-500 dark:text-graphite-400">Score de risco preliminar</p>
                <p className={`text-2xl font-bold ${validation.riskScore > 20 ? "text-amber-600" : "text-graphite-900 dark:text-white"}`}>
                  {validation.riskScore}%
                </p>
              </div>
            </div>
          )}

          {validation && parsedRows.length > 0 && (
            <div className="mt-6">
              <h4 className="mb-3 text-sm font-medium text-graphite-700 dark:text-graphite-300">Pré-visualização da planilha</h4>
              <div className="max-h-48 overflow-auto rounded-lg border border-graphite-200 dark:border-graphite-700">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-graphite-100 dark:bg-graphite-800">
                    <tr>
                      {Object.keys(parsedRows[0] ?? {}).map((h) => (
                        <th key={h} className="border-b border-graphite-200 px-3 py-2 text-left font-medium text-graphite-600 dark:border-graphite-700 dark:text-graphite-400">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {parsedRows.slice(0, 10).map((row, i) => (
                      <tr key={i} className="border-b border-graphite-100 dark:border-graphite-800">
                        {Object.values(row).map((v, j) => (
                          <td key={j} className="px-3 py-2 text-graphite-700 dark:text-graphite-300">{v}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {parsedRows.length > 10 && (
                  <p className="border-t border-graphite-200 bg-graphite-50 px-3 py-2 text-xs text-graphite-500 dark:border-graphite-700 dark:bg-graphite-900">
                    Mostrando 10 de {parsedRows.length} registros
                  </p>
                )}
              </div>
            </div>
          )}

          {validation && validation.valid > 0 && !anchorResult && (
            <form
              onSubmit={rhfSubmit(onAnchor, () => toastError("Confirme a irreversibilidade para continuar."))}
              className="mt-6 space-y-4"
            >
              {!showConfirm ? (
                <button
                  type="button"
                  onClick={() => setShowConfirm(true)}
                  className="rounded-lg bg-primary-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-primary-500"
                >
                  Registrar Lote
                </button>
              ) : (
                <>
                  <label className="flex cursor-pointer items-start gap-2">
                    <input
                      type="checkbox"
                      {...register("confirmIrreversibility", { required: true })}
                      className="mt-1 rounded"
                    />
                    <span className="text-sm text-graphite-700 dark:text-graphite-300">
                      Confirmo que compreendo: esta ação é irreversível e registrará os dados de forma permanente e criptografada.
                    </span>
                  </label>
                  <div className="flex flex-wrap items-center gap-4">
                    <button
                      type="submit"
                      disabled={createMutation.isPending}
                      className="rounded-lg bg-primary-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-primary-500 disabled:opacity-50"
                    >
                      {createMutation.isPending ? "Registrando..." : "Confirmar Registro"}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowConfirm(false)}
                      className="rounded-lg border border-graphite-300 px-6 py-2.5 text-sm text-graphite-700 hover:bg-graphite-100 dark:border-graphite-600 dark:text-graphite-300 dark:hover:bg-graphite-800"
                    >
                      Cancelar
                    </button>
                  </div>
                </>
              )}
            </form>
          )}

          {anchorResult && progress === 100 && (
            <div className="mt-6 rounded-lg border border-success/30 bg-success/10 p-4 dark:border-success/30 dark:bg-success/10">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="success">Validado</Badge>
                <span className="text-xs text-graphite-600 dark:text-graphite-300">Registro criptografado</span>
              </div>
              <div className="mt-4 space-y-2 text-sm">
                {batchStatus?.merkle_root && (
                  <p><span className="text-graphite-500">Chave de integridade:</span> <code className="font-mono">{batchStatus.merkle_root}</code></p>
                )}
                {batchStatus?.blockchain_tx && (
                  <p><span className="text-graphite-500">Código de validação:</span> <code className="font-mono break-all">{batchStatus.blockchain_tx}</code></p>
                )}
                <p><span className="text-graphite-500">Rede de validação:</span> principal</p>
              </div>
              <button
                onClick={downloadNtagCsv}
                className="mt-4 rounded-lg bg-primary-600 px-4 py-2 text-sm text-white hover:bg-primary-500"
              >
                Exportar Planilha NTAG
              </button>
            </div>
          )}

          {(createMutation.isPending || statusLog.length > 0) && (
            <div className="mt-6 space-y-2">
              <div className="flex items-center gap-2 text-sm">
                <Badge variant={progress === 100 ? "success" : "info"}>{progress === 100 ? "Confirmed" : progress > 0 ? "Processing" : "Pending"}</Badge>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-graphite-200 dark:bg-graphite-800">
                <div
                  className="h-full bg-primary-600 transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <pre className="max-h-40 overflow-auto rounded-lg bg-graphite-100 p-3 text-xs text-graphite-700 dark:bg-graphite-900 dark:text-graphite-300">
                {statusLog.join("\n")}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
