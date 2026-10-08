import { useId, type ReactNode } from "react";
import { Button } from "./Button";

/**
 * The bar of actions for the rows a person selected in a list (PD-F006-B01-T05, design
 * `organizer-data-surface`). One bar for every list: it states how many rows are chosen, shows
 * exactly one primary action, at most four actions in view and the rest under More, and says why an
 * action is unavailable instead of hiding it. An action only starts the list's own workflow - the
 * bulk planner's preview, a dialog - it never changes anything from the bar itself. Clearing the
 * selection is the grid's own control, so there is one.
 */
export type BulkAction = {
  id: string;
  label: string;
  run: () => void;
  /** The one emphasised action; the first action when none is marked. */
  primary?: boolean;
  disabled?: boolean;
  /** Why it is unavailable, shown beside the bar and tied to the button. */
  reason?: string;
};

export const MAX_BULK_VISIBLE = 4;

export function BulkBar({
  count,
  actions,
  children,
}: {
  count: number;
  actions: BulkAction[];
  /** Controls an action needs before it can run (a track to move to), shown before the actions. */
  children?: ReactNode;
}) {
  const id = useId();
  if (count <= 0) return null;
  const primaryId = (actions.find((a) => a.primary) ?? actions[0])?.id;
  const visible = actions.slice(0, MAX_BULK_VISIBLE);
  const more = actions.slice(MAX_BULK_VISIBLE);
  const reasons = actions.filter((a) => a.disabled && a.reason);
  const button = (action: BulkAction) => (
    <Button
      key={action.id}
      variant={action.id === primaryId ? "primary" : "secondary"}
      disabled={action.disabled}
      aria-describedby={
        action.disabled && action.reason ? `${id}-${action.id}` : undefined
      }
      onClick={action.run}
    >
      {action.label}
    </Button>
  );
  return (
    <div role="group" aria-label="Bulk actions" className="cx-bulkbar">
      <span className="cx-bulkbar__count">{count} selected</span>
      {children}
      {visible.map(button)}
      {more.length > 0 && (
        <details className="cx-bulkbar__more">
          <summary>More</summary>
          <div>{more.map(button)}</div>
        </details>
      )}
      {reasons.map((action) => (
        <span
          key={action.id}
          id={`${id}-${action.id}`}
          className="cx-muted cx-bulkbar__reason"
        >
          {action.reason}
        </span>
      ))}
    </div>
  );
}
