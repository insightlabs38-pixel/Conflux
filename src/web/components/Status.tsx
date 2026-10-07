import type { ReactNode } from "react";
import { Icon, type IconName } from "./Icon";

export type StatusTone = "neutral" | "info" | "success" | "warning" | "danger";

const STATUS_ICON: Record<StatusTone, IconName> = {
  neutral: "circle",
  info: "info",
  success: "circle-check",
  warning: "triangle-alert",
  danger: "circle-x",
};

/**
 * A state, as an icon and a word in the tone's ink, never a coloured chip: colour alone must not
 * carry meaning (V-COLOR-2). Use it where the state matters to the next action; plain attributes
 * (a track, a role, a count) are text or a `Tag`.
 */
export function Status({
  tone = "neutral",
  children,
}: {
  tone?: StatusTone;
  children: ReactNode;
}) {
  return (
    <span className={`cx-status cx-status--${tone}`}>
      <Icon name={STATUS_ICON[tone]} />
      {children}
    </span>
  );
}

/** A neutral attribute label (at most one per row); it carries no state and no colour. */
export function Tag({ children }: { children: ReactNode }) {
  return <span className="cx-tag">{children}</span>;
}
