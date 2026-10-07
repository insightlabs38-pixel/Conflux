import { Status } from "../../components/Status";
import { Card } from "../../components/Card";
import { DataTable } from "../../components/Foundation";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { useLoad } from "../../hooks/useLoad";
import { describeProblem } from "../../lib/api";
import {
  extensionsUrl,
  requirementText,
  type Extensions,
} from "../../lib/extensions";

/**
 * What this deployment's code provides, for organizers and admins: the sources that declare
 * themselves, the capabilities they provide and whether the declarations agree with what is really
 * registered. Read-only; there is no loader and nothing here installs or changes anything.
 */
export function ExtensionsPanel({ workspaceId }: { workspaceId: string }) {
  const load = useLoad<Extensions>(extensionsUrl(workspaceId), {
    describe: describeProblem,
  });
  const data = load.data;
  return (
    <Card title="Extensions">
      <p className="cx-muted">
        Everything extensible here is application source loaded by this
        deployment. This list shows what it provides and whether its
        declarations match what is registered.
      </p>
      {load.error && (
        <ErrorState
          kind="read"
          message={load.error.message}
          onRetry={load.reload}
        />
      )}
      {!load.error && !data && <LoadingState label="Loading extensions…" />}
      {data && (
        <>
          {data.problems.length === 0 ? (
            <p role="status">
              <Status tone="success">Consistent</Status> Every registered
              extension is declared and every declaration is registered.
            </p>
          ) : (
            <div role={data.ok ? "status" : "alert"}>
              <p>
                <Status tone={data.ok ? "warning" : "danger"}>
                  {data.ok ? "Needs a look" : "Inconsistent"}
                </Status>{" "}
                {data.problems.length} finding
                {data.problems.length === 1 ? "" : "s"}.
              </p>
              <ul aria-label="Extension findings">
                {data.problems.map((problem, index) => (
                  <li key={index}>
                    <Status
                      tone={problem.severity === "error" ? "danger" : "warning"}
                    >
                      {problem.severity}
                    </Status>{" "}
                    {problem.manifest && <strong>{problem.manifest}: </strong>}
                    {problem.message}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <h4>Sources</h4>
          <DataTable label="Extension sources">
            <thead>
              <tr>
                <th scope="col">Source</th>
                <th scope="col">Version</th>
                <th scope="col">Provides</th>
                <th scope="col">Needs</th>
              </tr>
            </thead>
            <tbody>
              {data.manifests.map((manifest) => (
                <tr key={manifest.id}>
                  <th scope="row">
                    {manifest.label}{" "}
                    <span className="cx-muted">({manifest.id})</span>
                  </th>
                  <td>
                    {manifest.version}{" "}
                    <span className="cx-muted">API {manifest.api_version}</span>
                  </td>
                  <td>{manifest.provides.length}</td>
                  <td>
                    {manifest.requires.length
                      ? manifest.requires.map(requirementText).join(", ")
                      : "Nothing"}
                  </td>
                </tr>
              ))}
            </tbody>
          </DataTable>
          <h4>Capabilities</h4>
          {data.capabilities.map((capability) => (
            <details key={capability.kind}>
              <summary className="cx-summary">
                {capability.label} ({capability.entries.length})
                {capability.declared_only && " · declared only"}
              </summary>
              <p className="cx-muted">{capability.description}</p>
              <ul>
                {capability.entries.map((entry) => (
                  <li key={entry.id}>
                    {entry.label} <span className="cx-muted">({entry.id})</span>
                    {entry.manifest ? ` · ${entry.manifest}` : " · unclaimed"}
                  </li>
                ))}
              </ul>
            </details>
          ))}
        </>
      )}
    </Card>
  );
}
