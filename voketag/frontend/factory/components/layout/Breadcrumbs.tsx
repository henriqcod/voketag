"use client";

import Link from "next/link";

export function Breadcrumbs({
  items,
}: {
  items: { label: string; href?: string }[];
}) {
  return (
    <nav className="flex items-center gap-1 text-sm" aria-label="Breadcrumb">
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && (
            <span className="text-graphite-400 dark:text-graphite-500">/</span>
          )}
          {item.href ? (
            <Link
              href={item.href}
              className="text-graphite-500 hover:text-primary-600 dark:text-graphite-400 dark:hover:text-primary-400"
            >
              {item.label}
            </Link>
          ) : (
            <span className="text-graphite-700 dark:text-graphite-300">
              {item.label}
            </span>
          )}
        </span>
      ))}
    </nav>
  );
}
