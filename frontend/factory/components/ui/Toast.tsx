"use client";

import { useEffect } from "react";

export type ToastType = "success" | "error" | "info";

export function Toast({
  message,
  type = "info",
  onDismiss,
  duration = 4000,
}: {
  message: string;
  type?: ToastType;
  onDismiss: () => void;
  duration?: number;
}) {
  useEffect(() => {
    const t = setTimeout(onDismiss, duration);
    return () => clearTimeout(t);
  }, [duration, onDismiss]);

  const colors =
    type === "success"
      ? "bg-success/20 text-success border-success/30"
      : type === "error"
      ? "bg-alert/20 text-alert border-alert/30"
      : "bg-primary-600/20 text-primary-400 border-primary-600/30";

  return (
    <div
      className={`fixed bottom-6 right-6 z-50 max-w-sm rounded-lg border px-4 py-3 shadow-lg ${colors} animate-slide-up`}
      role="alert"
    >
      {message}
    </div>
  );
}
