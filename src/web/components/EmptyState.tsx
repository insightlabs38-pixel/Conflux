import type { ReactNode } from "react";

/**
 * An empty list says what is empty, why, and what can be done next (S-EMPTY). `why` is required so
 * a bare headline cannot ship; `next` is the one next action when the viewer has one (a button or a
 * link), and the reason itself names who acts when they do not. "No data yet" and "no matches" are
 * different states: a filtered list passes its Clear filter action as `next`.
 */
export function EmptyState({
  title,
  why,
  next,
  children,
}: {
  title: string;
  why: ReactNode;
  next?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <div className="cx-state cx-state--empty">
      <p className="cx-state__title">{title}</p>
      <p className="cx-state__why">{why}</p>
      {next && <div className="cx-state__next">{next}</div>}
      {children}
    </div>
  );
}
