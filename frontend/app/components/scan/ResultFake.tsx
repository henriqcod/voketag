"use client";

interface Props {
  onReportClick?: () => void;
}

export function ResultFake({ onReportClick }: Props) {
  return (
    <div className="verify-result verify-result-fake">
      <div className="verify-icon verify-icon-error">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 6L6 18M6 6l12 12" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <h1 className="verify-title">Produto Falsificado</h1>
      <p className="verify-subtitle">
        Este código não corresponde a um registro válido. Recomendamos NÃO utilizar este produto.
      </p>

      <div className="verify-fake-message">
        <span>Código não registrado ou inválido.</span>
      </div>

      <button type="button" className="verify-btn verify-btn-danger" onClick={onReportClick}>
        Reportar falsificação
      </button>
    </div>
  );
}
