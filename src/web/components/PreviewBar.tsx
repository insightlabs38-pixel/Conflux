import { Button } from "./Button";
import {
  LIVE,
  fromLocalInput,
  isLive,
  toLocalInput,
  type PreviewContext,
  type PreviewNotice,
} from "../lib/previewContext";
import type { VersionInfo } from "../lib/versions";

const versionText = (version: VersionInfo) =>
  version.at && !version.current
    ? `${version.label} (${new Date(version.at).toLocaleDateString()})`
    : version.label;

/**
 * Chooses who, which version or what time a preview is for, and always says in words what it is
 * showing and that nothing is saved or sent. Controlled: the parent keeps the context and asks the
 * server; this never decides anything. A version and a time are two ways to pick one version, so
 * choosing one clears the other. "Back to live" is always one click away.
 */
export function PreviewBar({
  roles,
  versions,
  value,
  onChange,
  summary,
  notices = [],
  busy = false,
}: {
  roles: string[];
  versions: VersionInfo[];
  value: PreviewContext;
  onChange: (context: PreviewContext) => void;
  summary: string;
  notices?: PreviewNotice[];
  busy?: boolean;
}) {
  return (
    <fieldset className="cx-preview-bar" aria-busy={busy || undefined}>
      <legend>Preview as</legend>
      <div className="cx-preview-bar__pick">
        {roles.length > 0 && (
          <label>
            Person{" "}
            <select
              value={value.role ?? ""}
              onChange={(event) =>
                onChange({ ...value, role: event.target.value || null })
              }
            >
              <option value="">Myself (all fields)</option>
              {roles.map((role) => (
                <option key={role} value={role}>
                  {role}
                </option>
              ))}
            </select>
          </label>
        )}
        {versions.length > 0 && (
          <>
            <label>
              Version{" "}
              <select
                value={value.version ?? ""}
                onChange={(event) =>
                  onChange({
                    ...value,
                    version: event.target.value || null,
                    at: null,
                  })
                }
              >
                <option value="">Live</option>
                {versions.map((version) => (
                  <option key={version.id} value={version.id}>
                    {versionText(version)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              As of{" "}
              <input
                type="datetime-local"
                value={toLocalInput(value.at)}
                onChange={(event) =>
                  onChange({
                    ...value,
                    at: fromLocalInput(event.target.value),
                    version: null,
                  })
                }
              />
            </label>
          </>
        )}
        <Button
          type="button"
          variant="secondary"
          disabled={isLive(value)}
          onClick={() => onChange(LIVE)}
        >
          Back to live
        </Button>
      </div>
      <p role="status" className="cx-preview-bar__summary">
        <strong>Preview.</strong> {summary}
      </p>
      {notices.length > 0 && (
        <ul className="cx-preview-bar__notices">
          {notices.map((notice) => (
            <li key={notice.code}>{notice.message}</li>
          ))}
        </ul>
      )}
    </fieldset>
  );
}
