"use client";

import { useState } from "react";
import { reportScan, type ReportType } from "@/lib/scan-api";

interface Props {
  title: string;
  reportType: ReportType;
  code: string;
  onClose: () => void;
}

export function ReportModal({ title, reportType, code, onClose }: Props) {
  const [reason, setReason] = useState("");
  const [details, setDetails] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await reportScan(code, reason.trim(), details.trim(), reportType);
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao enviar.");
    } finally {
      setLoading(false);
    }
  };

  if (sent) {
    return (
      <div
        className="modal-overlay"
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.target === e.currentTarget && onClose()}
      >
        <div className="modal-content">
          <h2 className="modal-title">Obrigado</h2>
          <p className="modal-success">
            Seu reporte foi enviado com sucesso. Nossa equipe analisará a situação.
          </p>
          <button type="button" className="modal-btn modal-btn-primary" onClick={onClose}>
            Fechar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="report-modal-title"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="modal-content">
        <h2 id="report-modal-title" className="modal-title">
          {title}
        </h2>
        <form onSubmit={handleSubmit} className="report-form-inline">
          <label htmlFor="report-reason">Motivo (obrigatório)</label>
          <input
            id="report-reason"
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Descreva brevemente o motivo"
            required
            disabled={loading}
            className="report-input"
          />
          <label htmlFor="report-details">Detalhes (opcional)</label>
          <textarea
            id="report-details"
            value={details}
            onChange={(e) => setDetails(e.target.value)}
            placeholder="Informações adicionais"
            rows={3}
            disabled={loading}
            className="report-textarea"
          />
          {error && <p className="report-error">{error}</p>}
          <div className="modal-actions">
            <button type="button" className="modal-btn modal-btn-secondary" onClick={onClose}>
              Cancelar
            </button>
            <button
              type="submit"
              className="modal-btn modal-btn-primary"
              disabled={!reason.trim() || loading}
            >
              {loading ? "Enviando..." : "Enviar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
