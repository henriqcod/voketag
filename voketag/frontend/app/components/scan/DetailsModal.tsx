"use client";

import type { VerifyProduct } from "@/store/verifyStore";

interface Props {
  product: VerifyProduct;
  firstScanAt: string | null;
  onClose: () => void;
}

export function DetailsModal({ product, firstScanAt, onClose }: Props) {
  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="modal-content modal-details">
        <h2 id="modal-title" className="modal-title">
          Detalhes da autenticidade
        </h2>
        <div className="modal-body">
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
          <p className="modal-hint">
            Este produto foi verificado e considerado autêntico pelo sistema VokeTag.
          </p>
        </div>
        <button type="button" className="modal-btn modal-btn-primary" onClick={onClose}>
          Fechar
        </button>
      </div>
    </div>
  );
}
