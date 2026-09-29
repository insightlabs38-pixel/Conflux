import { useEffect, useState, type FormEvent } from "react";
import { WorkflowSections } from "../../components/WorkflowSections";
import { ProjectStoryEditor } from "./ProjectStoryEditor";
import { ArtifactPanel } from "./ArtifactPanel";
import { SubmissionPanel } from "../submissions/SubmissionPanel";
import { ProjectForms } from "../form-builder/ProjectForms";
import {
  ProjectContinuationPanel,
  ProjectEligibilityPanel,
  ProjectExceptionPanel,
  ProjectMentorshipPanel,
} from "../pvs";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";

type Project = {
  public_id: string;
  name: string;
  description?: string;
  team: string | null;
  track: string | null;
};
type TeamStatus = { team: { public_id: string } | null };
type Track = { public_id: string; name: string };

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
  const [tracks, setTracks] = useState<Track[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [name, setName] = useState("");
  const [trackId, setTrackId] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    Promise.all([
      request<Project[]>(base + "projects/"),
      request<Track[]>(base + "tracks/"),
    ])
      .then(([nextProjects, nextTracks]) => {
        if (active) {
          setProjects(nextProjects);
          setTracks(nextTracks);
          setLoaded(true);
        }
      })
      .catch((cause: unknown) => {
        if (active) {
          setLoaded(false);
          setError(message(cause));
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [base, retry]);

  function create(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    void request<TeamStatus>(base + "my-team/")
      .then((status) =>
        request<Project>(base + "projects/", "POST", {
          name: name.trim(),
          ...(status.team ? { team: status.team.public_id } : {}),
          ...(trackId ? { track: trackId } : {}),
        }),
      )
      .then((project) => {
        setProjects((current) => [...current, project]);
        setSelectedId(project.public_id);
        setName("");
        setTrackId("");
      })
      .catch((cause: unknown) => setError(message(cause)))
      .finally(() => setBusy(false));
  }

  if (loading)
    return (
      <section aria-label="My projects">
        <h2>My projects</h2>
        <LoadingState label="Loading projects…" />
      </section>
    );
  if (!loaded)
    return (
      <section aria-label="My projects">
        <h2>My projects</h2>
        <ErrorState
          message={error}
          onRetry={() => setRetry((count) => count + 1)}
        />
      </section>
    );

  return (
    <section aria-label="My projects">
      <h2>My projects</h2>
      {error && <p role="alert">{error}</p>}
      <details open={projects.length === 0} className="cx-project-create">
        <summary>Create a new project</summary>
        <form onSubmit={create}>
          <label>
            Project name{" "}
            <input
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
            />
          </label>
          {tracks.length > 0 && (
            <label>
              Track{" "}
              <select
                value={trackId}
                onChange={(event) => setTrackId(event.target.value)}
              >
                <option value="">No track</option>
                {tracks.map((track) => (
                  <option key={track.public_id} value={track.public_id}>
                    {track.name}
                  </option>
                ))}
              </select>
            </label>
          )}
          <button disabled={busy}>Create project</button>
        </form>
      </details>
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
      {selectedId &&
        projects.some((project) => project.public_id === selectedId) && (
          <div key={selectedId} className="cx-project-workspace">
            <header className="cx-project-workspace__header">
              <h3>
                {
                  projects.find((project) => project.public_id === selectedId)
                    ?.name
                }
              </h3>
              <p>
                Prepare the story and evidence, complete the event forms, then
                finalize a stage submission.
              </p>
            </header>
            <WorkflowSections
              label="Project tasks"
              sections={[
                {
                  id: "story",
                  label: "Project story",
                  description: "Title and description",
                  content: (
                    <ProjectStoryEditor
                      project={projects.find(
                        (project) => project.public_id === selectedId,
                      )!}
                      base={base}
                      onSaved={(next) =>
                        setProjects((items) =>
                          items.map((item) =>
                            item.public_id === next.public_id ? next : item,
                          ),
                        )
                      }
                    />
                  ),
                },
                {
                  id: "evidence",
                  label: "Evidence & checks",
                  description: "Artifacts and preflight",
                  content: (
                    <ArtifactPanel
                      workspaceId={workspaceId}
                      eventId={eventId}
                      projectId={selectedId}
                    />
                  ),
                },
                {
                  id: "forms",
                  label: "Event forms",
                  description: "Required project information",
                  content: (
                    <ProjectForms
                      workspaceId={workspaceId}
                      eventId={eventId}
                      projectId={selectedId}
                    />
                  ),
                },
                {
                  id: "submission",
                  label: "Submission",
                  description: "Draft, finalize and receipt",
                  content: (
                    <SubmissionPanel
                      workspaceId={workspaceId}
                      eventId={eventId}
                      projectId={selectedId}
                    />
                  ),
                },
                {
                  id: "eligibility",
                  label: "Eligibility",
                  description: "Resolve requested changes",
                  content: (
                    <ProjectEligibilityPanel
                      workspaceId={workspaceId}
                      eventId={eventId}
                      projectId={selectedId}
                    />
                  ),
                },
                {
                  id: "support",
                  label: "Support",
                  description: "Exceptions and mentorship",
                  content: (
                    <>
                      <ProjectExceptionPanel
                        workspaceId={workspaceId}
                        eventId={eventId}
                        projectId={selectedId}
                      />
                      <ProjectMentorshipPanel
                        workspaceId={workspaceId}
                        eventId={eventId}
                        projectId={selectedId}
                      />
                    </>
                  ),
                },
                {
                  id: "continuation",
                  label: "After the event",
                  description: "Continue your project",
                  content: (
                    <ProjectContinuationPanel
                      workspaceId={workspaceId}
                      eventId={eventId}
                      projectId={selectedId}
                    />
                  ),
                },
              ]}
            />
          </div>
        )}
    </section>
  );
}
