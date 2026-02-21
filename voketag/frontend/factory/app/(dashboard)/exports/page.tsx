"use client";

import { useState, useMemo } from "react";
import { useToast } from "@/lib/toast-context";
import { useBatchesList, useBatchProducts } from "@/hooks/useBatches";
import { Card, CardContent, CardHeader } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import * as XLSX from "xlsx";

const baseUrl = process.env.NEXT_PUBLIC_VERIFY_URL || "https://verify.voketag.com.br";

function downloadCsv(data: string[][], filename: string) {
  const csv = data.map((row) => row.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

function downloadXlsx(data: string[][], filename: string) {
  const ws = XLSX.utils.aoa_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "NTAG Export");
  XLSX.writeFile(wb, filename);
}

export default function ExportsPage() {
  const [selectedBatch, setSelectedBatch] = useState<string>("");
  const [format, setFormat] = useState<"csv" | "xlsx">("csv");

  const { data: batches = [] } = useBatchesList({ limit: 100 });
  const { data: products = [], isLoading: productsLoading } = useBatchProducts(
    selectedBatch || null,
    !!selectedBatch
  );

  const completedBatches = batches.filter((b) => b.status === "completed");
  const [showPreview, setShowPreview] = useState(false);
  const { success: toastSuccess } = useToast();

  const selectedBatchData = batches.find((b) => b.id === selectedBatch);

  const exportRows = useMemo(() => {
    const headers = ["serial_number", "qr_code_url", "nfc_payload", "blockchain_hash", "verification_url"];
    const rows: string[][] = [headers];
    if (products.length > 0) {
      for (const p of products) {
        const url = p.verification_url || `${baseUrl}/r/${encodeURIComponent(p.serial_number)}`;
        rows.push([
          p.serial_number,
          p.qr_code_url || url,
          p.nfc_payload || p.serial_number,
          p.blockchain_hash || selectedBatchData?.blockchain_tx || selectedBatchData?.id || "",
          url,
        ]);
      }
    } else if (selectedBatchData) {
      for (let i = 0; i < selectedBatchData.product_count; i++) {
        const serial = `SN-${selectedBatchData.id.slice(0, 8)}-${String(i + 1).padStart(5, "0")}`;
        const url = `${baseUrl}/r/${encodeURIComponent(serial)}`;
        rows.push([
          serial,
          url,
          selectedBatchData.id,
          selectedBatchData.blockchain_tx ?? selectedBatchData.id,
          url,
        ]);
      }
    }
    return rows;
  }, [products, selectedBatchData]);

  const previewRows = useMemo(() => exportRows.slice(0, 6), [exportRows]);

  const handleExport = () => {
    if (!selectedBatch || exportRows.length <= 1) return;
    const base = `ntag_export_${selectedBatch.slice(0, 8)}`;
    const ext = format === "xlsx" ? ".xlsx" : ".csv";
    if (format === "xlsx") {
      downloadXlsx(exportRows, `${base}${ext}`);
    } else {
      downloadCsv(exportRows, `${base}${ext}`);
    }
    toastSuccess("Planilha exportada com sucesso.");
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h2 className="text-xl font-semibold text-graphite-900 dark:text-white">Exportação Padrão NTAG</h2>
        <p className="mt-1 text-sm text-graphite-500 dark:text-graphite-400">
          Gere planilha para impressoras QR e gravadoras NFC NTAG213/215/216
        </p>
      </div>

      <Card>
        <CardHeader>
          <h3 className="font-medium text-graphite-900 dark:text-white">Exportar planilha</h3>
          <p className="mt-1 text-sm text-graphite-500 dark:text-graphite-400">
            Campos: serial_number, qr_code_url, nfc_payload, blockchain_hash, verification_url
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          {completedBatches.length === 0 ? (
            <EmptyState
              title="Nenhum lote completo"
              description="Complete um registro de lote antes de exportar."
            />
          ) : (
            <>
              <div>
                <label className="block text-sm text-graphite-400">
                  Selecione o lote
                </label>
                <select
                  value={selectedBatch}
                  onChange={(e) => setSelectedBatch(e.target.value)}
                  className="mt-2 w-full max-w-md rounded-lg border border-graphite-300 bg-white px-4 py-2 text-graphite-900 dark:border-graphite-700 dark:bg-graphite-900 dark:text-white"
                >
                  <option value="">Escolha um lote</option>
                  {completedBatches.map((b) => (
                    <option key={b.id} value={b.id}>
                      {b.id.slice(0, 8)}... — {b.product_count} produtos
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-graphite-400">
                  Formato
                </label>
                <select
                  value={format}
                  onChange={(e) => setFormat(e.target.value as "csv" | "xlsx")}
                  className="mt-2 w-full max-w-md rounded-lg border border-graphite-300 bg-white px-4 py-2 text-graphite-900 dark:border-graphite-700 dark:bg-graphite-900 dark:text-white"
                >
                  <option value="csv">CSV</option>
                  <option value="xlsx">XLSX</option>
                </select>
              </div>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => selectedBatch && setShowPreview(true)}
                  disabled={!selectedBatch || productsLoading}
                  className="rounded-lg border border-graphite-300 px-4 py-2 text-sm font-medium text-graphite-700 hover:bg-graphite-100 dark:border-graphite-600 dark:text-graphite-300 dark:hover:bg-graphite-800"
                >
                  {productsLoading ? "Carregando..." : "Visualizar preview"}
                </button>
                <button
                  onClick={handleExport}
                  disabled={!selectedBatch || exportRows.length <= 1 || productsLoading}
                  className="rounded-lg bg-primary-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-primary-500 disabled:opacity-50"
                >
                  Baixar planilha NTAG
                </button>
              </div>
              {showPreview && selectedBatch && (
                <div className="mt-6 rounded-lg border border-graphite-200 bg-graphite-50 p-4 dark:border-graphite-700 dark:bg-graphite-900">
                  <div className="mb-2 flex items-center justify-between">
                    <h4 className="text-sm font-medium text-graphite-700 dark:text-graphite-300">Preview da exportação</h4>
                    <button
                      type="button"
                      onClick={() => setShowPreview(false)}
                      className="text-graphite-500 hover:text-graphite-700 dark:hover:text-graphite-300"
                    >
                      Fechar
                    </button>
                  </div>
                  <div className="max-h-48 overflow-auto text-xs">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-graphite-200 dark:border-graphite-700">
                          {previewRows[0]?.map((h, i) => (
                            <th key={i} className="px-2 py-1 text-left font-medium">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {previewRows.slice(1).map((row, i) => (
                          <tr key={i} className="border-b border-graphite-100 dark:border-graphite-800">
                            {row.map((c, j) => (
                              <td key={j} className="max-w-[120px] truncate px-2 py-1" title={c}>{c}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <p className="mt-2 text-xs text-graphite-500">
                    Mostrando 5 primeiros. Total: {exportRows.length - 1} registros.
                  </p>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
