import type { OperationState } from "../hooks/useOperation";
import { Button } from "./Button";
import { ErrorState } from "./ErrorState";

/**
 * The one surface for a running/finished operation (contract: hooks/useOperation.ts). Pending,
 * success and cancelled are polite status messages; failure is an alert with a retry. Render it
 * next to the control that started the operation.
 */
export function OperationStatus<T>({
  state,
  pendingLabel = "Working…",
  successMessage,
  onCancel,
  onRetry,
  onDismiss,
}: {
  state: OperationState<T>;
  pendingLabel?: string;
  successMessage?: string | ((result: T) => string);
  onCancel?: () => void;
  onRetry?: () => void;
  onDismiss?: () => void;
}) {
  if (state.status === "idle") return null;
  if (state.status === "failed")
    return <ErrorState message={state.error} onRetry={onRetry} />;
  if (state.status === "pending") {
    const { progress } = state;
    const determinate =
      progress?.total !== undefined && progress.done !== undefined;
    return (
      <div className="cx-operation" role="status" aria-busy="true">
        <span>{progress?.label ?? pendingLabel}</span>
        {determinate && (
          <progress
            value={progress.done}
            max={progress.total}
            aria-label={progress.label}
          />
        )}
        {state.cancellable && onCancel && (
          <Button variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>
    );
  }
  if (state.status === "cancelled")
    return (
      <div className="cx-operation" role="status">
        <span>Cancelled. Nothing was changed after this point.</span>
        {onRetry && (
          <Button variant="secondary" onClick={onRetry}>
            Start again
          </Button>
        )}
        {onDismiss && (
          <Button variant="secondary" onClick={onDismiss}>
            Dismiss
          </Button>
        )}
      </div>
    );
  const message =
    typeof successMessage === "function"
      ? successMessage(state.result)
      : (successMessage ?? "Done.");
  return (
    <div className="cx-operation cx-operation--success" role="status">
      <span>{message}</span>
      {onDismiss && (
        <Button variant="secondary" onClick={onDismiss}>
          Dismiss
        </Button>
      )}
    </div>
  );
}
