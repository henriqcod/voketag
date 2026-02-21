"use client";

import { useCallback, useRef, useEffect, Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useVerifyStore } from "@/store/verifyStore";
import { scanProductWithRetry } from "@/lib/scan-api";
import { getGeolocation } from "@/lib/geolocation";
import { QRScanner } from "@/components/scan/QRScanner";
import { NFCReader } from "@/components/scan/NFCReader";
import { ResultOriginal } from "@/components/scan/ResultOriginal";
import { ResultWarning } from "@/components/scan/ResultWarning";
import { ResultFake } from "@/components/scan/ResultFake";
import { DetailsModal } from "@/components/scan/DetailsModal";
import { ReportModal } from "@/components/scan/ReportModal";

const MOCK_ORIGINAL = {
  status: "original" as const,
  product: { name: "Tênis Voke X", batch: "L2026-01", factory: "Voke Brasil", manufactured_at: "2026-01-10" },
  scan_count: 1,
  first_scan_at: "2026-02-01T10:00:00Z",
  risk_score: 0,
};

const MOCK_WARNING = {
  status: "warning" as const,
  product: { name: "Tênis Voke X", batch: "L2026-01", factory: "Voke Brasil", manufactured_at: "2026-01-10" },
  scan_count: 12,
  first_scan_at: "2026-02-01T10:00:00Z",
  risk_score: 0.45,
};

const MOCK_FAKE = { status: "fake" as const, risk_score: 1, lastScannedCode: "00000000-0000-0000-0000-000000000000" };

function ScanPageContent() {
  const searchParams = useSearchParams();
  const { status, product, scanCount, firstScanAt, riskScore, lastScannedCode, loading, error, setLoading, setError, setResult, reset } = useVerifyStore();
  const processingRef = useRef(false);
  const [modal, setModal] = useState<"details" | "report-irregularity" | "report-fake" | null>(null);

  const showSimulate = process.env.NODE_ENV === "development" || searchParams.get("dev") === "1";

  useEffect(() => {
    if (!showSimulate) return;
    const sim = searchParams.get("simulate");
    if (sim === "original") setResult({ ...MOCK_ORIGINAL, lastScannedCode: "00000000-0000-0000-0000-000000000001" });
    else if (sim === "warning") setResult({ ...MOCK_WARNING, lastScannedCode: "00000000-0000-0000-0000-000000000002" });
    else if (sim === "fake") setResult(MOCK_FAKE);
  }, [searchParams, setResult, showSimulate]);

  const performScan = useCallback(
    async (code: string) => {
      if (loading || status || processingRef.current) return;
      processingRef.current = true;
      setLoading(true);
      setError(null);
      await new Promise((r) => setTimeout(r, 1200));
      try {
        const geo = await getGeolocation();
        const metadata = geo ? { latitude: geo.latitude, longitude: geo.longitude } : undefined;
        const data = await scanProductWithRetry(code, metadata);
        setResult({ ...data, lastScannedCode: code });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao verificar.");
      } finally {
        processingRef.current = false;
      }
    },
    [loading, status, setLoading, setError, setResult]
  );

  const handleScan = useCallback((code: string) => performScan(code), [performScan]);
  const handleNewScan = useCallback(() => reset(), [reset]);

  if (status) {
    return (
      <div className={`scan-page scan-result-${status}`}>
        <header className="scan-header">
          <div className="scan-logo">VokeTag</div>
          {showSimulate && (
            <div className="scan-simulate">
              <span className="scan-simulate-label">Simular:</span>
              <button type="button" className="scan-simulate-btn" onClick={() => setResult(MOCK_ORIGINAL)}>Original</button>
              <button type="button" className="scan-simulate-btn" onClick={() => setResult(MOCK_WARNING)}>Warning</button>
              <button type="button" className="scan-simulate-btn" onClick={() => setResult(MOCK_FAKE)}>Fake</button>
            </div>
          )}
        </header>
        <main className="scan-main">
          {status === "original" && product && (
            <ResultOriginal
              product={product}
              firstScanAt={firstScanAt}
              onDetailsClick={() => setModal("details")}
            />
          )}
          {status === "warning" && (
            <ResultWarning
              product={product}
              scanCount={scanCount}
              firstScanAt={firstScanAt}
              riskScore={riskScore}
              onReportClick={() => setModal("report-irregularity")}
            />
          )}
          {status === "fake" && (
            <ResultFake onReportClick={() => setModal("report-fake")} />
          )}
          <button type="button" className="scan-new-btn" onClick={handleNewScan}>
            Escanear outro código
          </button>
        </main>
        {modal === "details" && product && (
          <DetailsModal product={product} firstScanAt={firstScanAt} onClose={() => setModal(null)} />
        )}
        {modal === "report-irregularity" && lastScannedCode && (
          <ReportModal
            title="Reportar possível irregularidade"
            reportType="irregularity"
            code={lastScannedCode}
            onClose={() => setModal(null)}
          />
        )}
        {modal === "report-fake" && lastScannedCode && (
          <ReportModal
            title="Reportar falsificação"
            reportType="fake"
            code={lastScannedCode}
            onClose={() => setModal(null)}
          />
        )}
      </div>
    );
  }

  return (
    <div className="scan-page scan-page-scanner">
      <NFCReader onScan={handleScan} disabled={!!status || loading} />
      <header className="scan-header">
        <div className="scan-logo">VokeTag</div>
        <span className="scan-badge">Verificação de Autenticidade</span>
        {showSimulate && (
          <div className="scan-simulate scan-simulate-fixed">
            <span className="scan-simulate-label">Simular:</span>
            <button type="button" className="scan-simulate-btn" onClick={() => setResult(MOCK_ORIGINAL)}>Original</button>
            <button type="button" className="scan-simulate-btn" onClick={() => setResult(MOCK_WARNING)}>Warning</button>
            <button type="button" className="scan-simulate-btn" onClick={() => setResult(MOCK_FAKE)}>Fake</button>
          </div>
        )}
      </header>
      <main className="scan-main">
        {loading && (
          <div className="scan-loading">
            <div className="scan-spinner" />
            <p>Verificando produto...</p>
          </div>
        )}
        {error && (
          <div className="scan-error">
            <p>{error}</p>
            <button type="button" onClick={reset}>
              Tentar novamente
            </button>
          </div>
        )}
        {!loading && !error && (
          <>
            <p className="scan-instruction">
              Aponte a câmera para o QR Code ou aproxime o celular do NFC
            </p>
            <QRScanner onScan={handleScan} disabled={!!status || loading} />
          </>
        )}
      </main>
    </div>
  );
}

export default function ScanPage() {
  return (
    <Suspense fallback={<div className="scan-page"><div className="scan-loading"><div className="scan-spinner" /><p>Carregando...</p></div></div>}>
      <ScanPageContent />
    </Suspense>
  );
}