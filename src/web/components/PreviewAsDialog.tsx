import { useId, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useLocation } from "react-router";
import { useMe } from "../hooks/useMe";
import { useShellEvents } from "../hooks/useShellEvents";
import { useLoad } from "../hooks/useLoad";
import { describeProblem } from "../lib/api";
import {
  LIVE,
  previewAs,
  previewProblem,
  type PreviewAs,
} from "../lib/previewContext";
import { roleLabel } from "../lib/roles";
import { ErrorState } from "./ErrorState";
import { LoadingState } from "./LoadingState";
import { Modal } from "./Modal";
import { useWorkspaceNavigation } from "./WorkspaceNavigation";

export const PREVIEW_ROLES = ["participant", "judge", "public"] as const;
type Form = { public_id: string; name: string };
type FormPreview = {
  fields: { id: string; label: string; type: string; required: boolean }[];
  total: number;
  hidden: number;
};

/**
 * What another kind of person would see, asked of the server (PREVIEW_CONTEXT): the saved
 * application form as a participant, a judge or the public meets it, and the public page. The
 * context is request data in one body; nothing is stored, nothing is sent to anyone, and the person
 * stays themselves with their own permissions, so a preview can only show a subset of what they could
 * already read. This only chooses and draws.
 */
export function PreviewAsDialog({
  initialRole,
  onClose,
}: {
  initialRole: string;
  onClose: () => void;
}) {
  const navigation = useWorkspaceNavigation()!;
  const location = useLocation();
  const username = useMe().data?.username ?? "you";
  const titleId = useId();
  const [role, setRole] = useState(
    (PREVIEW_ROLES as readonly string[]).includes(initialRole)
      ? initialRole
      : "participant",
  );
  const [formId, setFormId] = useState("");
  const { workspaceId } = navigation;
  const { events } = useShellEvents(workspaceId, navigation.role);
  const requested = new URLSearchParams(location.search).get("event") ?? "";
  const eventId = events.some((event) => event.public_id === requested)
    ? requested
    : "";
  const forms = useLoad<Form[]>(
    eventId
      ? `/api/v1/workspaces/${workspaceId}/events/${eventId}/forms/`
      : null,
    { describe: describeProblem },
  );
  const list = Array.isArray(forms.data) ? forms.data : [];
  const chosen =
    list.find((form) => form.public_id === formId) ?? list[0] ?? null;

  const formPreview = useQuery({
    queryKey: [
      "preview-as",
      "form",
      workspaceId,
      eventId,
      chosen?.public_id,
      role,
    ],
    queryFn: ({ signal }) =>
      previewAs<FormPreview>(
        workspaceId,
        "form",
        { event: eventId, form: chosen!.public_id },
        { role, at: null, version: null },
        signal,
      ),
    enabled: !!chosen && !!eventId,
    retry: false,
  });
  const pagePreview = useQuery({
    queryKey: ["preview-as", "page", workspaceId, eventId],
    queryFn: ({ signal }) =>
      previewAs<{ html: string }>(
        workspaceId,
        "page",
        { event: eventId },
        LIVE,
        signal,
      ),
    enabled: role === "public" && !!eventId,
    retry: false,
  });

  return (
    <Modal titleId={titleId} onClose={onClose}>
      <h2 id={titleId}>Preview as {roleLabel(role).toLowerCase()}</h2>
      <fieldset className="cx-preview__roles">
        <legend>Preview as</legend>
        {PREVIEW_ROLES.map((value) => (
          <label key={value}>
            <input
              type="radio"
              name="preview-role"
              checked={role === value}
              onChange={() => setRole(value)}
            />{" "}
            {roleLabel(value)}
          </label>
        ))}
      </fieldset>
      <p role="note" className="cx-preview__note">
        A preview shows what a {roleLabel(role).toLowerCase()} would see.
        Nothing is saved or sent, and you are still signed in as {username} with
        your own permissions.
      </p>
      {!eventId ? (
        <p role="status">
          Choose an event first (the event switcher in the top bar).
        </p>
      ) : forms.loading ? (
        <LoadingState label="Loading forms…" />
      ) : forms.error ? (
        <ErrorState
          kind="read"
          message={forms.error.message}
          onRetry={forms.reload}
        />
      ) : (
        <>
          <section aria-label="Application form">
            <h3>Application form</h3>
            {list.length === 0 && (
              <p role="status">This event has no forms yet.</p>
            )}
            {list.length > 1 && (
              <label>
                Form{" "}
                <select
                  value={chosen?.public_id ?? ""}
                  onChange={(e) => setFormId(e.target.value)}
                >
                  {list.map((form) => (
                    <option key={form.public_id} value={form.public_id}>
                      {form.name}
                    </option>
                  ))}
                </select>
              </label>
            )}
            {chosen && formPreview.isPending && (
              <LoadingState label="Loading the preview…" />
            )}
            {chosen && formPreview.isError && (
              <ErrorState
                kind="read"
                message={previewProblem(formPreview.error)}
                onRetry={() => void formPreview.refetch()}
              />
            )}
            {formPreview.data && (
              <FormFields preview={formPreview.data} role={role} />
            )}
          </section>
          {role === "public" && (
            <section aria-label="Public page">
              <h3>Public page</h3>
              {pagePreview.isPending && (
                <LoadingState label="Loading the page…" />
              )}
              {pagePreview.isError && (
                <ErrorState
                  kind="read"
                  message={previewProblem(pagePreview.error)}
                  onRetry={() => void pagePreview.refetch()}
                />
              )}
              {pagePreview.data && (
                // the frame forbids scripts, links and forms: it is a picture of the page, not the page
                <iframe
                  title="The public page as a visitor sees it"
                  className="cx-preview__frame"
                  sandbox=""
                  srcDoc={pagePreview.data.data.html}
                />
              )}
            </section>
          )}
        </>
      )}
      <div className="cx-consequence__actions">
        <button
          type="button"
          className="cx-button cx-button--secondary"
          onClick={onClose}
        >
          Close
        </button>
      </div>
    </Modal>
  );
}

function FormFields({
  preview,
  role,
}: {
  preview: PreviewAs<FormPreview>;
  role: string;
}) {
  const { fields, hidden, total } = preview.data;
  return (
    <>
      <p role="status">{preview.summary}</p>
      {fields.length === 0 ? (
        <p>No fields are shown to a {roleLabel(role).toLowerCase()}.</p>
      ) : (
        <table className="cx-table">
          <caption className="cx-visually-hidden">Fields shown</caption>
          <thead>
            <tr>
              <th scope="col">Field</th>
              <th scope="col">Type</th>
              <th scope="col">Required</th>
            </tr>
          </thead>
          <tbody>
            {fields.map((field) => (
              <tr key={field.id}>
                <td>{field.label}</td>
                <td>{field.type.replace(/_/g, " ")}</td>
                <td>{field.required ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p className="cx-preview__note">
        {hidden === 0
          ? `All ${total} fields are shown.`
          : `${hidden} of ${total} fields are not shown to a ${roleLabel(role).toLowerCase()}.`}
      </p>
    </>
  );
}
