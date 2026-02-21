"use client";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "warning" | "info";
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  variant = "danger",
  onConfirm,
  onCancel,
  loading = false,
}: ConfirmDialogProps) {
  if (!open) return null;

  const buttonColor =
    variant === "danger"
      ? "bg-red-600 hover:bg-red-700"
      : variant === "warning"
      ? "bg-amber-600 hover:bg-amber-700"
      : "bg-blue-600 hover:bg-blue-700";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div
        className="w-full max-w-md rounded-xl border border-[#334155] bg-[#1e293b] p-6 shadow-xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
      >
        <h2 id="confirm-title" className="mb-3 text-lg font-semibold text-[#f8fafc]">
          {title}
        </h2>
        <p className="mb-6 text-sm text-[#94a3b8]">{message}</p>
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="rounded-lg border border-[#334155] bg-transparent px-4 py-2 text-sm font-medium text-[#94a3b8] hover:bg-[#334155] disabled:opacity-50"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className={`rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors disabled:opacity-50 ${buttonColor}`}
          >
            {loading ? "Processando..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
