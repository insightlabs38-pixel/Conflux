import { useId } from "react";
import { Button } from "./Button";
import { Icon } from "./Icon";
import { describeFailure, type FailureKind } from "../lib/failure";

/**
 * A failure says what happened, whether the person's data was kept, and what Try again does
 * (S-ERR). `kind` states what failed: a read changes nothing; a write is described by
 * `lib/failure.ts` only as far as it is known (pass `kept` and `retry` from there, or let a
 * read use the defaults). `reference` is the server's request id when the API sends one.
 */
export function ErrorState({
  message,
  onRetry,
  kind,
  kept,
  retry,
  reference,
}: {
  message: string;
  onRetry?: () => void;
  kind?: FailureKind;
  kept?: string;
  retry?: string;
  reference?: string;
}) {
  const note = useId();
  const known = kind === "read" ? describeFailure(null, "read") : null;
  const keptText = kept ?? known?.kept;
  const retryText = retry ?? known?.retry;
  return (
    <div className="cx-state cx-state--error" role="alert">
      <p className="cx-state__title">
        <Icon name="circle-x" /> Something went wrong
      </p>
      <p>{message}</p>
      {keptText && <p className="cx-state__kept">{keptText}</p>}
      {onRetry && (
        <Button
          variant="secondary"
          onClick={onRetry}
          aria-describedby={retryText ? note : undefined}
        >
          Try again
        </Button>
      )}
      {onRetry && retryText && (
        <p id={note} className="cx-state__retry">
          {retryText}
        </p>
      )}
      {reference && (
        <p className="cx-state__ref">
          Reference <code>{reference}</code>
        </p>
      )}
    </div>
  );
}
