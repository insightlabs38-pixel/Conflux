import type { ReactNode } from "react";

export function EmptyState({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="cx-state">
      <p className="cx-state__title">{title}</p>
      {children}
    </div>
  );
}
