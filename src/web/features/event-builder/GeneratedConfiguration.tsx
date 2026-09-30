import { useState } from "react";
import { describeProblem } from "../../lib/api";
import { useLoad } from "../../hooks/useLoad";

type Generated = {
  explicit: { key: string }[];
  inherited: { key: string }[];
  document: { format: string | null };
  text: string;
};

/**
 * The event's configuration as a document that states only what is necessary: what the organizer
 * set or changed from the format. Inherited values stay readable as comments but are not stated, so
 * the few decisions are not buried. The text comes from the server, the same as automation gets.
 */
export function GeneratedConfiguration({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const [opened, setOpened] = useState(false);
  const [copied, setCopied] = useState("");
  const load = useLoad<Generated>(
    opened
      ? `/api/v1/workspaces/${workspaceId}/events/${eventId}/configuration/generated/`
      : null,
    { describe: describeProblem },
  );
  const data = load.data;

  async function copy() {
    try {
      await navigator.clipboard.writeText(data?.text ?? "");
      setCopied("Copied to the clipboard.");
    } catch {
      setCopied("Could not copy; select the text and copy it.");
    }
  }

  return (
    <details onToggle={(e) => e.currentTarget.open && setOpened(true)}>
      <summary>Generated configuration</summary>
      <p>
        Only what was set or changed is stated; everything inherited from the
        format or the defaults is listed in comments so it stays readable.
      </p>
      {load.error && (
        <p role="alert">
          {load.error.message}{" "}
          <button type="button" onClick={() => void load.reload()}>
            Try again
          </button>
        </p>
      )}
      {opened && !data && !load.error && (
        <p className="cx-muted">Generating…</p>
      )}
      {data && (
        <>
          <p className="cx-muted">
            {data.explicit.length} stated, {data.inherited.length} inherited
            {data.document.format ? ` from ${data.document.format}` : ""}.
          </p>
          <pre className="cx-generated-config" tabIndex={0}>
            {data.text}
          </pre>
          <button type="button" onClick={() => void copy()}>
            Copy
          </button>
          <span role="status">{copied}</span>
        </>
      )}
    </details>
  );
}
