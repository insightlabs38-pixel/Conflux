import { useEffect, useState } from "react";
import { PreviewBar } from "../../components/PreviewBar";
import { DataTable } from "../../components/Foundation";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import {
  LIVE,
  previewAs,
  previewProblem,
  type PreviewAs,
  type PreviewContext,
} from "../../lib/previewContext";

type Condition = { field: string; equals: string | boolean };
type Row = {
  id: string;
  label: string;
  type: string;
  required: boolean;
  required_if: Condition | null;
  visible_to: string[];
  visible_if: Condition | null;
};
type FormPreview = { fields: Row[]; total: number; hidden: number };

type State =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "ready"; preview: PreviewAs<FormPreview> };

/**
 * A saved form as someone else would meet it, at a kept version or as of a time. The server says
 * which fields a person is shown (the form's own rule) and resolves the version; this only lists
 * them. The live editor preview above shows unsaved edits, which a server cannot know.
 */
export function FormPreviewAs({
  workspaceId,
  eventId,
  formId,
  refreshKey,
}: {
  workspaceId: string;
  eventId: string;
  formId: string;
  /** Changes when the form is saved or published, so the preview is asked again. */
  refreshKey: number;
}) {
  const [context, setContext] = useState<PreviewContext>(LIVE);
  const [state, setState] = useState<State>({ kind: "loading" });
  const [last, setLast] = useState<PreviewAs<FormPreview> | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setState({ kind: "loading" });
    previewAs<FormPreview>(
      workspaceId,
      "form",
      { event: eventId, form: formId },
      context,
      controller.signal,
    )
      .then((preview) => {
        setLast(preview);
        setState({ kind: "ready", preview });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        setState({ kind: "error", message: previewProblem(error) });
      });
    return () => controller.abort();
  }, [workspaceId, eventId, formId, context, refreshKey, attempt]);

  if (!last)
    return state.kind === "error" ? (
      <ErrorState
        kind="read"
        message={state.message}
        onRetry={() => setAttempt((n) => n + 1)}
      />
    ) : (
      <LoadingState label="Loading preview…" />
    );

  const preview = state.kind === "ready" ? state.preview : last;
  const labels = new Map(preview.data.fields.map((f) => [f.id, f.label]));
  const when = (c: Condition) =>
    `${labels.get(c.field) ?? c.field} is ${String(c.equals)}`;
  return (
    <section aria-label="Preview of the saved form">
      <PreviewBar
        roles={last.roles}
        versions={last.versions}
        value={context}
        onChange={setContext}
        summary={preview.summary}
        notices={state.kind === "ready" ? preview.notices : []}
        busy={state.kind === "loading"}
      />
      {state.kind === "error" && <p role="alert">{state.message}</p>}
      {state.kind === "loading" && <p role="status">Updating preview…</p>}
      {preview.data.fields.length === 0 ? (
        <p>
          {preview.data.total === 0
            ? "This version has no fields."
            : "None of this form's fields are shown to that person."}
        </p>
      ) : (
        <DataTable label="Fields in the preview">
          <thead>
            <tr>
              <th scope="col">Field</th>
              <th scope="col">Type</th>
              <th scope="col">Needed</th>
              <th scope="col">Shown</th>
              <th scope="col">Visible to</th>
            </tr>
          </thead>
          <tbody>
            {preview.data.fields.map((field) => (
              <tr key={field.id}>
                <th scope="row">{field.label}</th>
                <td>{field.type}</td>
                <td>
                  {field.required
                    ? "Required"
                    : field.required_if
                      ? `Required when ${when(field.required_if)}`
                      : "Optional"}
                </td>
                <td>
                  {field.visible_if
                    ? `When ${when(field.visible_if)}`
                    : "Always"}
                </td>
                <td>{field.visible_to.join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      )}
      {preview.data.hidden > 0 && (
        <p className="cx-field__hint">
          {preview.data.hidden} of {preview.data.total}{" "}
          {preview.data.total === 1 ? "field" : "fields"}{" "}
          {preview.data.hidden === 1 ? "is" : "are"} not shown to that person.
        </p>
      )}
    </section>
  );
}
