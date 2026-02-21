import { ReactNode } from "react";

export function Table({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">{children}</table>
    </div>
  );
}

export function TableHeader({ children }: { children: ReactNode }) {
  return (
    <thead className="border-b border-[#334155] text-[#94a3b8] font-medium">
      {children}
    </thead>
  );
}

export function TableBody({ children }: { children: ReactNode }) {
  return <tbody className="divide-y divide-[#334155]">{children}</tbody>;
}

export function TableRow({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <tr className={className}>{children}</tr>;
}

export function TableHead({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <th className={`px-4 py-3 ${className}`} scope="col">
      {children}
    </th>
  );
}

export function TableCell({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <td className={`px-4 py-3 ${className}`}>{children}</td>;
}
