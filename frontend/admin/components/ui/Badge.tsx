import { ReactNode } from "react";

export function Badge({
  children,
  variant = "default",
  className = "",
}: {
  children: ReactNode;
  variant?: "default" | "success" | "warning" | "error" | "info";
  className?: string;
}) {
  const variants = {
    default: "bg-[#334155] text-[#94a3b8]",
    success: "bg-emerald-900/60 text-emerald-300 border border-emerald-700/30",
    warning: "bg-amber-900/60 text-amber-300 border border-amber-700/30",
    error: "bg-red-900/60 text-red-300 border border-red-700/30",
    info: "bg-blue-900/60 text-blue-300 border border-blue-700/30",
  };
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variants[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
