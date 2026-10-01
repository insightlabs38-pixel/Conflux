import { useState } from "react";
import { describeProblem } from "../lib/api";
import { useLoad } from "../hooks/useLoad";
import type { Explanation } from "../lib/explain";
import { Button } from "./Button";
import { ExplanationView } from "./ExplanationView";
import { Modal } from "./Modal";

type Consequences = {
  title: string;
  allowed: boolean;
  refusal: { code: string; message: string } | null;
  blockers: { code: string; message: string }[];
  consequences: { code: string; message: string; count: number | null }[];
  reversible: boolean;
  confirm_label: string;
  explanation: Explanation;
};

/**
 * Confirm a destructive or high-impact operation by stating what it would do, from the server
 * (`GET …/consequences/`), instead of a generic "Are you sure?". A refused operation says why and
 * offers no confirmation. The button is named for the operation; Escape and Cancel change nothing.
 * The operation's own endpoint still validates and audits: `onConfirm` performs it.
 */
export function ConsequenceDialog({
  url,
  onConfirm,
  onCancel,
}: {
  url: string;
  onConfirm: () => Promise<void>;
  onCancel: () => void;
}) {
  const load = useLoad<Consequences>(url, { describe: describeProblem });
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  const data = load.data;

  async function confirm() {
    setBusy(true);
    setFailure("");
    try {
      await onConfirm();
    } catch (cause) {
      setFailure(cause instanceof Error ? cause.message : "Request failed.");
      setBusy(false);
    }
  }

  return (
    <Modal titleId="consequence-title" onClose={onCancel}>
      <h2 id="consequence-title">{data?.title ?? "Checking…"}</h2>
      {!data && !load.error && (
        <p className="cx-muted">Checking what this would change…</p>
      )}
      {load.error && (
        <p role="alert">
          {load.error.message}{" "}
          <button type="button" onClick={() => void load.reload()}>
            Try again
          </button>
        </p>
      )}
      {data && (
        <>
          <ExplanationView
            explanation={data.explanation}
            label={data.allowed ? "What this will do" : "Why this is refused"}
            alert
          />
          {data.allowed && data.reversible && (
            <p className="cx-muted">You can add it back afterwards.</p>
          )}
        </>
      )}
      {failure && <p role="alert">{failure}</p>}
      <div className="cx-consequence__actions">
        <Button variant="secondary" onClick={onCancel} disabled={busy}>
          {data && !data.allowed ? "Close" : "Cancel"}
        </Button>
        {data?.allowed && (
          <Button
            variant="danger"
            onClick={() => void confirm()}
            disabled={busy}
          >
            {data.confirm_label}
          </Button>
        )}
      </div>
    </Modal>
  );
}
