import { ReactNode, ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function Button({
  children,
  variant = "primary",
  size = "md",
  className = "",
  disabled,
  ...props
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#0f172a] disabled:opacity-50 disabled:cursor-not-allowed";
  const variants = {
    primary:
      "bg-brand-500 text-white hover:bg-brand-600 focus:ring-brand-500/50 shadow-theme-sm hover:shadow-theme-md",
    secondary:
      "bg-[#334155] text-[#f8fafc] hover:bg-[#475569] focus:ring-[#64748b]",
    ghost:
      "bg-transparent text-[#94a3b8] hover:bg-[#334155] hover:text-[#f8fafc] focus:ring-[#64748b] shadow-none",
    danger:
      "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
  };
  const sizes = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };
  return (
    <button
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}
