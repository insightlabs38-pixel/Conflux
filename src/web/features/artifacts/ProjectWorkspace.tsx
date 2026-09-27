import { useEffect, useState, type FormEvent } from "react";
import { ArtifactPanel } from "./ArtifactPanel";

type Project = { public_id: string; name: string; team: string | null };
type TeamStatus = { team: { public_id: string } | null };

function message(value: unknown): string {
  if (typeof value === "string") return value;
  if (value instanceof Error) return value.message;
  if (Array.isArray(value)) return value.map(message).join(" ");
  if (value && typeof value === "object")
    return Object.entries(value)
      .map(([key, item]) => `${key}: ${message(item)}`)
      .join(" ");
  return "Request failed.";
}

async function request<T>(
  url: string,
  method = "GET",
  body?: object,
): Promise<T> {
  const response = await fetch(url, {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    let detail: unknown = `Request failed (${response.status}).`;
    try {
      detail = await response.json();
    } catch {
      /* Retain status. */
    }
    throw new Error(message(detail));
  }
  return response.json() as Promise<T>;
}

export function ProjectWorkspace({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    request<Project[]>(base + "projects/")
      .then((items) => {
        if (active) setProjects(items);
      })
      .catch((cause: unknown) => {
        if (active) setError(message(cause));
      });
    return () => {
      active = false;
    };
  }, [base]);

  function create(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    void request<TeamStatus>(base + "my-team/")
      .then((status) =>
        request<Project>(base + "projects/", "POST", {
          name: name.trim(),
          ...(status.team ? { team: status.team.public_id } : {}),
        }),
      )
      .then((project) => {
        setProjects([...projects, project]);
        setSelectedId(project.public_id);
        setName("");
      })
      .catch((cause: unknown) => setError(message(cause)))
      .finally(() => setBusy(false));
  }

  return (
    <section aria-label="My projects">
      <h2>My projects</h2>
      {error && <p role="alert">{error}</p>}
      <form onSubmit={create}>
        <label>
          Project name{" "}
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
          />
        </label>
        <button disabled={busy}>Create project</button>
      </form>
      {projects.length === 0 ? (
        <p>No projects yet.</p>
      ) : (
        <label>
          Project{" "}
          <select
            value={selectedId}
            onChange={(event) => setSelectedId(event.target.value)}
          >
            <option value="">Choose a project</option>
            {projects.map((project) => (
              <option key={project.public_id} value={project.public_id}>
                {project.name}
              </option>
            ))}
          </select>
        </label>
      )}
      {selectedId && (
        <ArtifactPanel
          key={selectedId}
          workspaceId={workspaceId}
          eventId={eventId}
          projectId={selectedId}
        />
      )}
    </section>
  );
}
