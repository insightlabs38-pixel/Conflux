import { useLoad } from "../hooks/useLoad";
import { describeProblem } from "../lib/api";
import {
  KIND_LABEL,
  factRow,
  humanSize,
  isWebUrl,
  previewUrl,
  type Preview,
} from "../lib/preview";
import { Status } from "./Status";
import { ErrorState } from "./ErrorState";
import { LoadingState } from "./LoadingState";

const TONE = {
  blocked: "danger",
  warning: "warning",
  info: "neutral",
} as const;

/**
 * Draws one preview descriptor: what the thing is, what the safety checks found, the facts, a
 * bounded excerpt or an archive listing, and the download the source already offers. Everything
 * is a text node. A thing that cannot be previewed says why instead of showing nothing.
 */
export function ArtifactPreview({
  preview,
  showDownload = true,
}: {
  preview: Preview;
  /** Hide the link and download when the surrounding panel already has them. */
  showDownload?: boolean;
}) {
  const facts = Object.entries(preview.facts);
  return (
    <div className="cx-preview" data-state={preview.state}>
      <p className="cx-preview__summary">
        {KIND_LABEL[preview.kind]}
        {preview.size !== null && <> · {humanSize(preview.size)}</>}
        {preview.state === "pending" && <> · not inspected yet</>}
      </p>
      {preview.reason && (
        <p
          className="cx-preview__reason"
          role={preview.state === "unavailable" ? "note" : undefined}
        >
          {preview.reason.message}
        </p>
      )}
      {preview.detected_type && <p>Detected type: {preview.detected_type}</p>}
      {preview.findings.length > 0 && (
        <ul
          className="cx-artifact__findings"
          aria-label={`Findings for ${preview.name}`}
        >
          {preview.findings.map((finding, index) => (
            <li key={`${finding.code}-${index}`}>
              <Status tone={TONE[finding.level]}>{finding.level}</Status>{" "}
              {finding.message}
            </li>
          ))}
          {preview.findings_total > preview.findings.length && (
            <li className="cx-muted">
              and {preview.findings_total - preview.findings.length} more
            </li>
          )}
        </ul>
      )}
      {facts.length > 0 && (
        <dl className="cx-artifact__facts">
          {facts.map(([key, value]) => {
            const [label, text] = factRow(key, value);
            return (
              <div key={key}>
                <dt>{label}</dt>
                <dd>{text}</dd>
              </div>
            );
          })}
        </dl>
      )}
      {preview.text && (
        <pre
          className="cx-scroll-region cx-artifact__preview"
          aria-label={`Preview of ${preview.name}`}
          tabIndex={0}
        >
          {preview.text}
        </pre>
      )}
      {preview.entries.length > 0 && (
        <div
          className="cx-scroll-region"
          role="region"
          tabIndex={0}
          aria-label={`Files in ${preview.name}`}
        >
          <table className="cx-preview__entries">
            <thead>
              <tr>
                <th scope="col">File</th>
                <th scope="col">Size</th>
              </tr>
            </thead>
            <tbody>
              {preview.entries.map((entry, index) => (
                <tr key={index}>
                  <td>{entry.name}</td>
                  <td>{entry.size === null ? "" : humanSize(entry.size)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {preview.entries_total > preview.entries.length && (
            <p className="cx-muted">
              Showing {preview.entries.length} of {preview.entries_total} files.
            </p>
          )}
        </div>
      )}
      {showDownload && isWebUrl(preview.link) && (
        <p>
          <a
            className="cx-button cx-button--secondary"
            href={preview.link}
            target="_blank"
            rel="noopener noreferrer"
          >
            Open {preview.link}
          </a>
        </p>
      )}
      {showDownload && preview.media && (
        <p>
          <a
            className="cx-button cx-button--secondary"
            href={preview.media.url}
            rel="noopener noreferrer"
          >
            Download {preview.media.filename}
          </a>{" "}
          <span className="cx-muted">
            Files are untrusted content; open with care.
          </span>
        </p>
      )}
    </div>
  );
}

/** Loads the descriptor for a registered source and draws it, with every state a panel needs. */
export function PreviewLoader({
  workspaceId,
  source,
  reference,
  showDownload,
}: {
  workspaceId: string;
  source: string;
  reference: Record<string, string>;
  showDownload?: boolean;
}) {
  const load = useLoad<Preview>(previewUrl(workspaceId, source, reference), {
    describe: describeProblem,
    absent: [404],
  });
  if (load.error)
    return (
      <ErrorState
        kind="read"
        message={load.error.message}
        onRetry={load.reload}
      />
    );
  if (load.loading && !load.data)
    return <LoadingState label="Loading preview…" />;
  if (!load.data)
    return <p role="note">There is nothing here you can preview.</p>;
  return <ArtifactPreview preview={load.data} showDownload={showDownload} />;
}
