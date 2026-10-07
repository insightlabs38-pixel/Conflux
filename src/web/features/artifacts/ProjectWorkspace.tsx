import { useState, type FormEvent } from "react";
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
import { apiJson, describeProblem } from "../../lib/api";
import { useLoad } from "../../hooks/useLoad";

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

export function ProjectWorkspace({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;
  const [selectedId, setSelectedId] = useState("");
  const [name, setName] = useState("");
  const [trackId, setTrackId] = useState("");
  const [actionError, setActionError] = useState("");
  const [busy, setBusy] = useState(false);
  const projectsLoad = useLoad<Project[]>(base + "projects/", {
    describe: describeProblem,
  });
  const tracksLoad = useLoad<Track[]>(base + "tracks/", {
    describe: describeProblem,
  });
  const projects = projectsLoad.data ?? [];
  const tracks = tracksLoad.data ?? [];
  const loaded = projectsLoad.data !== null && tracksLoad.data !== null;
  const loadError =
    projectsLoad.error?.message || tracksLoad.error?.message || "";
  const loading = !loaded && !loadError;
  const error = actionError || loadError;
  const retry = () =>
    void Promise.all([projectsLoad.reload(), tracksLoad.reload()]);

  function create(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setActionError("");
    void apiJson<TeamStatus>(base + "my-team/")
      .then((status) =>
        apiJson<Project>(base + "projects/", "POST", {
          name: name.trim(),
          ...(status.team ? { team: status.team.public_id } : {}),
          ...(trackId ? { track: trackId } : {}),
        }),
      )
      .then((project) => {
        projectsLoad.update((current) => [...(current ?? []), project]);
        setSelectedId(project.public_id);
        setName("");
        setTrackId("");
      })
      .catch((cause: unknown) => setActionError(message(cause)))
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
        <ErrorState kind="read" message={error} onRetry={retry} />
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
                      workspaceId={workspaceId}
                      onSaved={(next) =>
                        projectsLoad.update((items) =>
                          (items ?? []).map((item) =>
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
