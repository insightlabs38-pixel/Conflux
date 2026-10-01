import { Badge } from "../../components/Badge";
import { Card } from "../../components/Card";
import { DataTable } from "../../components/Foundation";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { useLoad } from "../../hooks/useLoad";
import { describeProblem } from "../../lib/api";
import {
  CLAIM_TEXT,
  completenessUrl,
  stateList,
  transitionLines,
  type Completeness,
  type CompletenessFeature,
} from "../../lib/completeness";

function lifecycleSummary(feature: CompletenessFeature) {
  const life = feature.lifecycle;
  if (!life) return "Not declared";
  if (life.kind === "none") return "No states";
  return stateList(feature);
}

/**
 * Which features provide what across every surface, and whether the claims match the system.
 * Read-only: the registry is code, the server checks it, and nothing here changes anything. The
 * first property shown is identity and lifecycle; more appear as their checks land.
 */
export function CompletenessPanel({ workspaceId }: { workspaceId: string }) {
  const load = useLoad<Completeness>(completenessUrl(workspaceId), {
    describe: describeProblem,
  });
  const data = load.data;
  const landed = data?.properties.filter((p) => p.landed) ?? [];
  const pending = data?.properties.filter((p) => !p.landed) ?? [];
  return (
    <Card title="Completeness">
      <p className="cx-muted">
        What each important feature provides across the product, checked against
        the running system. A claim that does not match is a finding, not a
        setting.
      </p>
      {load.error && (
        <ErrorState message={load.error.message} onRetry={load.reload} />
      )}
      {!load.error && !data && <LoadingState label="Loading completeness…" />}
      {data && (
        <>
          {data.problems.length === 0 ? (
            <p role="status">
              <Badge tone="success">Consistent</Badge> Every claim matches the
              system for {data.features.length} features.
            </p>
          ) : (
            <div role="alert">
              <p>
                <Badge tone="danger">Inconsistent</Badge> {data.problems.length}{" "}
                finding
                {data.problems.length === 1 ? "" : "s"}.
              </p>
              <ul aria-label="Completeness findings">
                {data.problems.map((problem, index) => (
                  <li key={index}>
                    {problem.feature && <strong>{problem.feature}: </strong>}
                    {problem.message}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <DataTable label="Features and what they provide">
            <thead>
              <tr>
                <th scope="col">Feature</th>
                <th scope="col">Identity</th>
                <th scope="col">Lifecycle</th>
                {landed
                  .filter((p) => p.key !== "identity")
                  .map((p) => (
                    <th key={p.key} scope="col">
                      {p.label}
                    </th>
                  ))}
              </tr>
            </thead>
            <tbody>
              {data.features.map((feature) => {
                const lines = transitionLines(feature);
                const life = feature.lifecycle;
                return (
                  <tr key={feature.key}>
                    <th scope="row">
                      {feature.label}{" "}
                      <span className="cx-muted">({feature.key})</span>
                    </th>
                    <td>
                      {
                        CLAIM_TEXT[
                          feature.claims.identity?.state ?? "unclaimed"
                        ]
                      }
                      {feature.id_type === "UUIDField"
                        ? ` · public id (${feature.id_field})`
                        : ""}
                    </td>
                    <td>
                      <details>
                        <summary className="cx-summary">
                          {lifecycleSummary(feature)}
                        </summary>
                        {life?.kind === "none" ? (
                          <p className="cx-muted">{life.note}</p>
                        ) : (
                          <>
                            {life && life.initial.length > 0 && (
                              <p className="cx-muted">
                                Starts as {life.initial.join(", ")}
                                {life.terminal.length > 0
                                  ? `; ends at ${life.terminal.join(", ")}`
                                  : ""}
                                .
                              </p>
                            )}
                            {lines.length > 0 && (
                              <ul
                                aria-label={`Transitions of ${feature.label}`}
                              >
                                {lines.map((line) => (
                                  <li key={line}>{line}</li>
                                ))}
                              </ul>
                            )}
                          </>
                        )}
                      </details>
                    </td>
                    {landed
                      .filter((p) => p.key !== "identity")
                      .map((p) => (
                        <td key={p.key}>
                          {
                            CLAIM_TEXT[
                              feature.claims[p.key]?.state ?? "unclaimed"
                            ]
                          }
                        </td>
                      ))}
                  </tr>
                );
              })}
            </tbody>
          </DataTable>
          {pending.length > 0 && (
            <details>
              <summary className="cx-summary">
                {pending.length} properties are not checked yet
              </summary>
              <ul>
                {pending.map((p) => (
                  <li key={p.key}>
                    {p.label} <span className="cx-muted">({p.batch})</span>
                  </li>
                ))}
              </ul>
            </details>
          )}
        </>
      )}
    </Card>
  );
}
