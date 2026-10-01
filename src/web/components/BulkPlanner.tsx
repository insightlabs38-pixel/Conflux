import { useCallback, useEffect, useRef, useState } from "react";
import {
  applyBulk,
  bulkUrl,
  describeEffect,
  isRefusal,
  approvalMessage,
  isStale,
  needsApproval,
  previewBulk,
  type BulkApplied,
  type BulkOperation,
  type BulkPreview,
  type Names,
} from "../lib/bulk";
import { Button } from "./Button";
import { Modal } from "./Modal";

type Phase =
  | { kind: "previewing" }
  | { kind: "ready"; preview: BulkPreview }
  | { kind: "applying"; preview: BulkPreview }
  | { kind: "applied"; result: BulkApplied }
  | { kind: "held"; preview: BulkPreview; message: string }
  | { kind: "stale"; message: string }
  | { kind: "refused"; message: string }
  | { kind: "unsure"; preview: BulkPreview; message: string };

/**
 * Run a bulk operation in four steps the organizer can see: a dry run that states the exact
 * effects, an explicit apply, a receipt, and a safe retry. The plan is all-or-nothing on the
 * server (a failure changes nothing), a stale preview (expired, or the data moved) asks for a new
 * preview instead of applying something the organizer did not see, and trying again after a lost
 * connection re-sends the same preview, which the server never applies twice.
 */
export function BulkPlanner({
  workspaceId,
  eventId,
  title,
  operations,
  names,
  applyLabel = "Apply",
  onApplied,
  onClose,
}: {
  workspaceId: string;
  eventId: string;
  title: string;
  operations: BulkOperation[];
  names?: Names;
  applyLabel?: string;
  /** The changes were applied (the list behind the dialog can reload). */
  onApplied?: (result: BulkApplied) => void;
  onClose: () => void;
}) {
  const url = bulkUrl(workspaceId, eventId);
  const [phase, setPhase] = useState<Phase>({ kind: "previewing" });
  const applied = useRef(onApplied);
  applied.current = onApplied;

  const preview = useCallback(async () => {
    setPhase({ kind: "previewing" });
    try {
      setPhase({ kind: "ready", preview: await previewBulk(url, operations) });
    } catch (cause) {
      setPhase({
        kind: "refused",
        message: cause instanceof Error ? cause.message : "Request failed.",
      });
    }
    // The operations are the caller's at the time the dialog opens.
  }, [url]);
  useEffect(() => {
    void preview();
  }, [preview]);

  async function apply(from: BulkPreview) {
    setPhase({ kind: "applying", preview: from });
    try {
      const result = await applyBulk(url, operations, from.preview_token);
      setPhase({ kind: "applied", result });
      applied.current?.(result);
    } catch (cause) {
      const message =
        cause instanceof Error ? cause.message : "Request failed.";
      if (needsApproval(cause))
        setPhase({ kind: "held", preview: from, message });
      else if (isStale(cause)) setPhase({ kind: "stale", message });
      else if (isRefusal(cause)) setPhase({ kind: "refused", message });
      else setPhase({ kind: "unsure", preview: from, message });
    }
  }

  const busy = phase.kind === "previewing" || phase.kind === "applying";
  const effects =
    phase.kind === "applied"
      ? phase.result.effects
      : phase.kind === "ready" ||
          phase.kind === "applying" ||
          phase.kind === "unsure"
        ? phase.preview.effects
        : [];

  return (
    <Modal titleId="bulk-title" onClose={onClose}>
      <h2 id="bulk-title">{title}</h2>
      {phase.kind === "previewing" && (
        <p role="status" className="cx-muted">
          Checking what this would change…
        </p>
      )}
      {(phase.kind === "ready" || phase.kind === "applying") && (
        <>
          <p>This will:</p>
          <ul>
            {effects.map((effect, index) => (
              <li key={index}>{describeEffect(effect, names)}</li>
            ))}
          </ul>
          {phase.preview.approvals?.length ? (
            <p role="note">
              Another person has to approve this first:{" "}
              {phase.preview.approvals.map((a) => a.label).join(", ")}. Applying
              asks for that approval and changes nothing yet.
            </p>
          ) : null}
          <p className="cx-muted">
            All or nothing: if any step fails, nothing is changed. The preview
            is valid for {Math.round(phase.preview.expires_in / 60)} minutes.
          </p>
        </>
      )}
      {phase.kind === "applied" && (
        <>
          <p role="status">Applied. Nothing is left to do.</p>
          <ul aria-label="Receipt">
            {effects.map((effect, index) => (
              <li key={index}>{describeEffect(effect, names)}</li>
            ))}
          </ul>
          <p className="cx-muted">
            The change is on the audit record, and the receipt is listed under
            the event&apos;s bulk operations.
          </p>
        </>
      )}
      {phase.kind === "held" && (
        <>
          <p role="status">
            Waiting for approval. Nothing was applied: {phase.message}
          </p>
          <p>
            Once another person approves it under Operations, apply again with
            the same preview.
          </p>
        </>
      )}
      {phase.kind === "stale" && (
        <>
          <p role="alert">
            Things changed since the preview, so nothing was applied:{" "}
            {phase.message}
          </p>
          <p>Preview again to see the current effects.</p>
        </>
      )}
      {phase.kind === "refused" && (
        <p role="alert">Cannot be done: {phase.message}</p>
      )}
      {phase.kind === "unsure" && (
        <>
          <p role="alert">Could not confirm the result: {phase.message}</p>
          <p>
            Trying again is safe. The same preview is never applied twice, so if
            it already went through you will get its receipt.
          </p>
        </>
      )}
      <div className="cx-consequence__actions">
        <Button variant="secondary" onClick={onClose} disabled={busy}>
          {phase.kind === "applied" ? "Close" : "Cancel"}
        </Button>
        {phase.kind === "stale" && (
          <Button onClick={() => void preview()}>Preview again</Button>
        )}
        {phase.kind === "refused" && (
          <Button variant="secondary" onClick={() => void preview()}>
            Preview again
          </Button>
        )}
        {phase.kind === "unsure" && (
          <Button onClick={() => void apply(phase.preview)}>Try again</Button>
        )}
        {phase.kind === "held" && (
          <Button onClick={() => void apply(phase.preview)}>Apply again</Button>
        )}
        {(phase.kind === "ready" || phase.kind === "applying") && (
          <Button
            variant="danger"
            disabled={busy}
            onClick={() => void apply(phase.preview)}
          >
            {applyLabel}
          </Button>
        )}
      </div>
    </Modal>
  );
}
