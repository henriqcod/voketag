"use client";

import type { VerifyProduct } from "@/store/verifyStore";

interface Props {
  product?: VerifyProduct | null;
  scanCount: number;
  firstScanAt: string | null;
  riskScore: number;
  onReportClick?: () => void;
}

export function ResultWarning({ product, scanCount, firstScanAt, riskScore, onReportClick }: Props) {
  const riskPercent = Math.min(100, Math.round(riskScore * 100));

  return (
    <div className="verify-result verify-result-warning">
      <div className="verify-icon verify-icon-warning">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <h1 className="verify-title">ATENÇÃO</h1>
      <h2 className="verify-title-secondary">Produto já verificado várias vezes</h2>
      <p className="verify-subtitle">
        Este código já foi escaneado anteriormente. Recomendamos confirmar a procedência do produto.
      </p>

      {product && (
        <div className="verify-card verify-card-warning">
          <div className="verify-card-row">
            <span className="label">Nome</span>
            <span className="value">{product.name}</span>
          </div>
          <div className="verify-card-row">
            <span className="label">Lote</span>
            <span className="value">{product.batch}</span>
          </div>
          <div className="verify-card-row">
            <span className="label">Fábrica</span>
            <span className="value">{product.factory}</span>
          </div>
        </div>
      )}
      <div className="verify-warning-stats">
        <div className="verify-stat">
          <span className="label">Número de verificações</span>
          <span className="value">{scanCount}</span>
        </div>
        {firstScanAt && (
          <div className="verify-stat">
            <span className="label">Primeira verificação</span>
            <span className="value">{new Date(firstScanAt).toLocaleDateString("pt-BR")}</span>
          </div>
        )}
      </div>

      <div className="verify-risk-bar">
        <div className="verify-risk-label">
          <span>Indicador de risco</span>
          <span>{riskPercent}%</span>
        </div>
        <div className="verify-risk-track">
          <div className="verify-risk-fill" style={{ width: `${riskPercent}%` }} />
        </div>
      </div>

      <button type="button" className="verify-btn verify-btn-secondary" onClick={onReportClick}>
        Reportar possível irregularidade
      </button>
    </div>
  );
}
