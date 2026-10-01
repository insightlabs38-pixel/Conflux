import { useEffect, useId, useState } from "react";
import { Field } from "./Foundation";
import { RichDoc } from "./RichDoc";
import { Button } from "./Button";
import { previewRich, type RichPreview, type RichProfile } from "../lib/rich";

const DELAY_MS = 350;

/**
 * A text box for rich content with an optional preview. The preview is rendered by the server
 * for this person only (nothing is saved) and drawn from its tree, so it shows what the profile
 * will keep and what it drops. The editor never decides what is allowed; it shows the answer.
 */
export function RichEditor({
  label,
  hint,
  value,
  onChange,
  profile,
  workspaceId,
  rows = 12,
}: {
  label: string;
  hint?: string;
  value: string;
  onChange: (value: string) => void;
  profile: RichProfile;
  workspaceId: string;
  rows?: number;
}) {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<
    | { kind: "loading" }
    | { kind: "error"; message: string }
    | { kind: "ready"; preview: RichPreview }
  >({ kind: "loading" });
  const panel = useId();

  useEffect(() => {
    if (!open || !value.trim()) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setState({ kind: "loading" });
      previewRich(workspaceId, profile, value, controller.signal)
        .then((preview) => setState({ kind: "ready", preview }))
        .catch((error: unknown) => {
          if (controller.signal.aborted) return;
          setState({
            kind: "error",
            message: error instanceof Error ? error.message : "Preview failed.",
          });
        });
    }, DELAY_MS);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [open, value, profile, workspaceId]);

  return (
    <div className="cx-rich-editor">
      <Field label={label} hint={hint}>
        {(props) => (
          <textarea
            {...props}
            rows={rows}
            value={value}
            onChange={(event) => onChange(event.target.value)}
          />
        )}
      </Field>
      <Button
        type="button"
        variant="secondary"
        aria-expanded={open}
        aria-controls={panel}
        onClick={() => setOpen((current) => !current)}
      >
        {open ? "Hide preview" : "Preview"}
      </Button>
      <div id={panel} className="cx-rich-editor__preview" hidden={!open}>
        {open && !value.trim() ? (
          <p className="cx-field__hint">Nothing to preview yet.</p>
        ) : open && state.kind === "loading" ? (
          <p role="status">Rendering preview…</p>
        ) : open && state.kind === "error" ? (
          <p role="alert">{state.message}</p>
        ) : open && state.kind === "ready" ? (
          <RichDoc tree={state.preview.tree} label={`${label} preview`} />
        ) : null}
      </div>
    </div>
  );
}
