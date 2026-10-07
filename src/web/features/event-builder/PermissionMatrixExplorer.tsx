import { useState } from "react";
import { apiRequest } from "../../lib/api";
import { useLoad } from "../../hooks/useLoad";
import { RecordPicker, participantSource } from "../../components/RecordPicker";

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
  const [actor, setActor] = useState("");
  const {
    data,
    error: failure,
    loading,
  } = useLoad<MatrixEntry[]>(
    `/api/v1/workspaces/${workspaceId}/events/${eventId}/permission-matrix/`,
    {
      describe: (status) => `Permission matrix request failed (${status}).`,
    },
  );
  const matrix = data ?? [];
  const error = failure?.message ?? "";
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;

  const [dryRunKey, setDryRunKey] = useState("");
  const [subjectKind, setSubjectKind] = useState<"role" | "user">("role");
  const [subjectRole, setSubjectRole] = useState(ROLE_OPTIONS[0]);
  const [subjectUserId, setSubjectUserId] = useState("");
  const [dryRunError, setDryRunError] = useState("");
  const [dryRunBusy, setDryRunBusy] = useState(false);
  const [dryRunResult, setDryRunResult] = useState<DryRunResult | null>(null);

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
    apiRequest<DryRunResult>(base + "authz-dry-run/", {
      method: "POST",
      body: {
        path,
        method,
        subject_kind: subjectKind,
        subject: subjectKind === "role" ? subjectRole : subjectUserId.trim(),
      },
      describe: (status, detail) =>
        (detail as { detail?: string } | undefined)?.detail ??
        `Dry run failed (${status}).`,
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
          <option value="user">Real person</option>
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
        <RecordPicker
          source={participantSource(workspaceId)}
          label="Person"
          noun="person"
          value={subjectUserId}
          onChange={setSubjectUserId}
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
