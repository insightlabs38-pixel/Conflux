import { useEffect, useRef, useState } from "react";
import { describeProblem } from "../lib/api";
import { useLoad } from "../hooks/useLoad";
import { Button } from "./Button";

type Consequences = {
  title: string;
  allowed: boolean;
  refusal: { code: string; message: string } | null;
  blockers: { code: string; message: string }[];
  consequences: { code: string; message: string; count: number | null }[];
  reversible: boolean;
  confirm_label: string;
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
  const dialog = useRef<HTMLDivElement>(null);
  const cancel = useRef(onCancel);
  cancel.current = onCancel;
  const data = load.data;

  // Focus moves in, stays in, and returns to what opened the dialog.
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    dialog.current?.focus();
    return () => opener?.focus?.();
  }, []);

  function keydown(event: React.KeyboardEvent) {
    if (event.key === "Escape") {
      event.stopPropagation();
      cancel.current();
      return;
    }
    if (event.key !== "Tab" || !dialog.current) return;
    const focusable = [
      ...dialog.current.querySelectorAll<HTMLElement>(
        "button:not([disabled]), [href], input, select, textarea",
      ),
    ];
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const active = document.activeElement;
    if (event.shiftKey && (active === first || active === dialog.current)) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && active === last) {
      event.preventDefault();
      first.focus();
    }
  }

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
    <div className="cx-consequence__backdrop">
      <div
        ref={dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby="consequence-title"
        tabIndex={-1}
        className="cx-consequence"
        onKeyDown={keydown}
      >
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
        {data && !data.allowed && (
          <>
            <p role="alert">This cannot be done right now:</p>
            <ul>
              {data.blockers.map((blocker) => (
                <li key={blocker.code + blocker.message}>{blocker.message}</li>
              ))}
            </ul>
          </>
        )}
        {data && data.allowed && (
          <>
            <p>This will:</p>
            <ul>
              {data.consequences.map((item) => (
                <li key={item.code + item.message}>{item.message}</li>
              ))}
            </ul>
            <p className="cx-muted">
              {data.reversible
                ? "You can add it back afterwards."
                : "This cannot be undone."}
            </p>
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
      </div>
    </div>
  );
}
