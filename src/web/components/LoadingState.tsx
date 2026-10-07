import { useEffect, useState, type CSSProperties } from "react";
import { Button } from "./Button";
import { Icon } from "./Icon";

/** After this long a wait is no longer a blink: say so and offer a way out (S-LOAD). */
export const SLOW_AFTER_MS = 8000;

/**
 * A wait whose result has no predictable layout: a spinner and words. Where the layout is known
 * (a grid, a list of rows) render a skeleton of it instead and keep headers and toolbars live.
 * Past 8 seconds it says what is slow and, when the caller can stop the work, offers Cancel; the
 * work itself is the caller's operation (hooks/useOperation), never invented here.
 */
export function LoadingState({
  label = "Loading…",
  slowAfterMs = SLOW_AFTER_MS,
  slowNote = "This is taking longer than usual. Your data is safe; you can keep waiting.",
  onCancel,
}: {
  label?: string;
  slowAfterMs?: number;
  slowNote?: string;
  onCancel?: () => void;
}) {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), slowAfterMs);
    return () => clearTimeout(timer);
  }, [slowAfterMs]);
  return (
    <div className="cx-state cx-state--loading" role="status">
      <p className="cx-state__title">
        <Icon name="loader" className="cx-spin" />
        {label}
      </p>
      {slow && (
        <p>
          {slowNote}{" "}
          {onCancel && (
            <Button variant="secondary" size="sm" onClick={onCancel}>
              Cancel
            </Button>
          )}
        </p>
      )}
    </div>
  );
}

/**
 * Placeholder rows for a table whose columns are known; static, because nothing should move. They
 * are blocks, not table rows, so nothing that counts real rows can mistake them for data.
 */
export function SkeletonRows({
  columns,
  rows = 5,
}: {
  columns: number;
  rows?: number;
}) {
  return (
    <div
      className="cx-skeleton-rows"
      aria-hidden="true"
      style={{ "--cols": columns } as CSSProperties}
    >
      {Array.from({ length: rows * columns }, (_, cell) => (
        <span key={cell} className="cx-skeleton" />
      ))}
    </div>
  );
}
