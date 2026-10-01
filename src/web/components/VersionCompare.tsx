import { useState } from "react";
import { useLoad } from "../hooks/useLoad";
import { describeProblem } from "../lib/api";
import {
  comparisonUrl,
  versionsUrl,
  type VersionComparison,
  type VersionInfo,
  type VersionList,
} from "../lib/versions";
import { DiffView } from "./DiffView";
import { ErrorState } from "./ErrorState";
import { LoadingState } from "./LoadingState";

const optionText = (version: VersionInfo) =>
  version.at && !version.current
    ? `${version.label} (${new Date(version.at).toLocaleDateString()})`
    : version.label;

/**
 * Pick any two versions of a registered source and see what changed between them. The list and
 * the comparison both come from the server; this only chooses and draws. Comparing writes nothing:
 * restoring a version is still the feature's own button.
 */
export function VersionCompare({
  workspaceId,
  source,
  reference,
  label,
}: {
  workspaceId: string;
  source: string;
  reference: Record<string, string>;
  /** Names the group, e.g. "Compare form versions". */
  label: string;
}) {
  const list = useLoad<VersionList>(
    versionsUrl(workspaceId, source, reference),
    {
      describe: describeProblem,
    },
  );
  const versions = list.data?.versions ?? [];
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const chosenFrom = from || versions[versions.length - 2]?.id || "";
  const chosenTo = to || versions[versions.length - 1]?.id || "";
  const comparison = useLoad<VersionComparison>(
    chosenFrom && chosenTo
      ? comparisonUrl(workspaceId, source, reference, chosenFrom, chosenTo)
      : null,
    { describe: describeProblem },
  );

  if (list.error)
    return <ErrorState message={list.error.message} onRetry={list.reload} />;
  if (!list.data) return <LoadingState label="Loading versions…" />;
  if (versions.length < 2) return <p>There is nothing to compare yet.</p>;
  return (
    <section aria-label={label} className="cx-version-compare">
      <div className="cx-version-compare__pick">
        {(
          [
            ["Compare", chosenFrom, setFrom],
            ["with", chosenTo, setTo],
          ] as const
        ).map(([text, value, set]) => (
          <label key={text}>
            {text}{" "}
            <select value={value} onChange={(event) => set(event.target.value)}>
              {versions.map((version) => (
                <option key={version.id} value={version.id}>
                  {optionText(version)}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>
      {comparison.error && (
        <ErrorState
          message={comparison.error.message}
          onRetry={comparison.reload}
        />
      )}
      {comparison.loading && !comparison.data && (
        <LoadingState label="Comparing…" />
      )}
      {comparison.data && !comparison.error && (
        <DiffView
          diff={comparison.data.diff}
          label={`Changes from ${comparison.data.older.label} to ${comparison.data.newer.label}`}
        />
      )}
    </section>
  );
}
