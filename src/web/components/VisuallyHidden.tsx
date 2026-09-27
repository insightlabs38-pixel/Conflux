import type { ReactNode } from "react";

/** Content read by screen readers but not shown visually (e.g. table/column labels). */
export function VisuallyHidden({ children }: { children: ReactNode }) {
  return <span className="cx-visually-hidden">{children}</span>;
}
