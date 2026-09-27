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
    </section>
  );
}
