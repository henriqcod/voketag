"use client";

import type { VerifyProduct } from "@/store/verifyStore";

interface Props {
  product: VerifyProduct;
  firstScanAt: string | null;
  onDetailsClick?: () => void;
}

export function ResultOriginal({ product, firstScanAt, onDetailsClick }: Props) {
  return (
    <div className="verify-result verify-result-original">
      <div className="verify-icon verify-icon-success">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M20 6L9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <h1 className="verify-title">Produto Original</h1>
      <p className="verify-subtitle">Este produto é autêntico e foi validado com sucesso.</p>

      <div className="verify-card">
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
        <div className="verify-card-row">
          <span className="label">Data de fabricação</span>
          <span className="value">{product.manufactured_at}</span>
        </div>
        {firstScanAt && (
          <div className="verify-card-row">
            <span className="label">Primeiro scan</span>
            <span className="value">{new Date(firstScanAt).toLocaleDateString("pt-BR")}</span>
          </div>
        )}
      </div>

      <button type="button" className="verify-btn verify-btn-primary" onClick={onDetailsClick}>
        Ver detalhes da autenticidade
      </button>
    </div>
  );
}
