import { ReactNode } from "react";

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`rounded-xl border border-[#334155] bg-[#1e293b] p-5 shadow-theme-md ${className}`}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`mb-4 text-lg font-semibold ${className}`}>{children}</div>;
}

export function CardContent({ children }: { children: ReactNode }) {
  return <div>{children}</div>;
}
