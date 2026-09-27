import type { ReactNode } from "react";

type Tone = "neutral" | "info" | "success" | "warning" | "danger";

export function Badge({
  tone = "neutral",
  children,
}: {
  tone?: Tone;
  children: ReactNode;
}) {
  return <span className={`cx-badge cx-badge--${tone}`}>{children}</span>;
}
