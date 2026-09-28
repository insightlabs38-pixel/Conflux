import { useEffect, useState } from "react";

type Access = "roles" | "any_authenticated" | "public" | "unknown";
type MatrixEntry = {
  resource: string;
  view: string;
  path: string;
  method: string;
  access: Access;
  roles: string[];
};

const ROLE_OPTIONS = [
  "participant",
  "judge",
  "organizer",
  "admin",
  "mentor",
  "volunteer",
  "sponsor",
];

function grantsAccessTo(entry: MatrixEntry, actor: string): boolean {
  if (actor === "") return true;
  if (entry.access === "public") return true;
  if (entry.access === "any_authenticated")
    return actor !== "public" && actor !== "unauthenticated";
  if (entry.access === "roles") return entry.roles.includes(actor);
  return false;
}

type DryRunResult = {
  allowed: boolean;
  mode: "live" | "hypothetical";
  actual_roles?: string[];
};

export function PermissionMatrixExplorer({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const [matrix, setMatrix] = useState<MatrixEntry[]>([]);
  const [actor, setActor] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;

  const [dryRunKey, setDryRunKey] = useState("");
  const [subjectKind, setSubjectKind] = useState<"role" | "user">("role");
  const [subjectRole, setSubjectRole] = useState(ROLE_OPTIONS[0]);
  const [subjectUserId, setSubjectUserId] = useState("");
  const [dryRunError, setDryRunError] = useState("");
  const [dryRunBusy, setDryRunBusy] = useState(false);
  const [dryRunResult, setDryRunResult] = useState<DryRunResult | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    fetch(
      `/api/v1/workspaces/${workspaceId}/events/${eventId}/permission-matrix/`,
      { credentials: "include" },
    )
      .then((response) => {
        if (!response.ok)
          throw new Error(
            `Permission matrix request failed (${response.status}).`,
          );
        return response.json() as Promise<MatrixEntry[]>;
      })
      .then((result) => {
        if (active) setMatrix(result);
      })
      .catch((cause: unknown) => {
        if (active)
          setError(cause instanceof Error ? cause.message : "Could not load.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [workspaceId, eventId]);

  const visible = matrix.filter((entry) => grantsAccessTo(entry, actor));

  function runDryRun() {
    const [method, path] = dryRunKey.split("|", 2);
    if (!method || !path) {
      setDryRunError("Choose an endpoint first.");
      return;
    }
    setDryRunBusy(true);
    setDryRunError("");
    setDryRunResult(null);
    fetch(base + "authz-dry-run/", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path,
        method,
        subject_kind: subjectKind,
        subject: subjectKind === "role" ? subjectRole : subjectUserId.trim(),
      }),
    })
      .then(async (response) => {
        if (!response.ok) {
          const detail = (await response.json().catch(() => null)) as {
            detail?: string;
          } | null;
          throw new Error(
            detail?.detail ?? `Dry run failed (${response.status}).`,
          );
        }
        return response.json() as Promise<DryRunResult>;
      })
      .then(setDryRunResult)
      .catch((cause: unknown) =>
        setDryRunError(
          cause instanceof Error ? cause.message : "Dry run failed.",
        ),
      )
      .finally(() => setDryRunBusy(false));
  }

  return (
    <section aria-label="Permission matrix explorer">
      <h3>Permission matrix explorer</h3>
      <p>
        Every registered endpoint's actual access requirement, read directly
        from the same permission checks the API enforces -- pick a role to see
        everything that role (plus any endpoint open to any signed-in user or
        the public) can reach.
      </p>
      {error && <p role="alert">{error}</p>}
      <label>
        Role{" "}
        <select value={actor} onChange={(e) => setActor(e.target.value)}>
          <option value="">All roles</option>
          {ROLE_OPTIONS.map((role) => (
            <option key={role} value={role}>
              {role}
            </option>
          ))}
        </select>
      </label>
      {loading ? (
        <p>Loading…</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Resource</th>
              <th>View</th>
              <th>Method</th>
              <th>Path</th>
              <th>Access</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((entry) => (
              <tr key={`${entry.method}-${entry.path}`}>
                <td>{entry.resource}</td>
                <td>{entry.view}</td>
                <td>{entry.method}</td>
                <td>{entry.path}</td>
                <td>
                  {entry.access === "roles"
                    ? entry.roles.join(", ")
                    : entry.access === "any_authenticated"
                      ? "any signed-in user"
                      : entry.access === "public"
                        ? "public"
                        : "unknown"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h4>Authorization dry run</h4>
      <p>
        Test one endpoint against either a real user's current roles ("live" --
        calls the real permission check, never the endpoint's actual handler) or
        a bare hypothetical role with no membership at all ("hypothetical" --
        read from the matrix above).
      </p>
      {dryRunError && <p role="alert">{dryRunError}</p>}
      <label>
        Endpoint{" "}
        <select
          value={dryRunKey}
          onChange={(e) => setDryRunKey(e.target.value)}
        >
          <option value="">Choose an endpoint…</option>
          {matrix.map((entry) => (
            <option
              key={`${entry.method}-${entry.path}`}
              value={`${entry.method}|${entry.path}`}
            >
              {entry.method} {entry.path}
            </option>
          ))}
        </select>
      </label>
      <label>
        Subject{" "}
        <select
          value={subjectKind}
          onChange={(e) => setSubjectKind(e.target.value as "role" | "user")}
        >
          <option value="role">Hypothetical role</option>
          <option value="user">Real user (by ID)</option>
        </select>
      </label>
      {subjectKind === "role" ? (
        <select
          aria-label="Hypothetical role"
          value={subjectRole}
          onChange={(e) => setSubjectRole(e.target.value)}
        >
          {ROLE_OPTIONS.map((role) => (
            <option key={role} value={role}>
              {role}
            </option>
          ))}
        </select>
      ) : (
        <input
          value={subjectUserId}
          onChange={(e) => setSubjectUserId(e.target.value)}
          placeholder="User public ID"
        />
      )}
      <button type="button" disabled={dryRunBusy} onClick={runDryRun}>
        {dryRunBusy ? "Testing…" : "Test"}
      </button>
      {dryRunResult && (
        <p role="status">
          {dryRunResult.allowed ? "Allowed" : "Denied"} ({dryRunResult.mode})
          {dryRunResult.actual_roles
            ? ` — actual roles: ${dryRunResult.actual_roles.join(", ") || "none"}`
            : ""}
        </p>
      )}
    </section>
  );
}
