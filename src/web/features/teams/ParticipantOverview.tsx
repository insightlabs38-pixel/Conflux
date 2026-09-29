import { useEffect, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { Grid } from "../../components/Foundation";
import {
  DestinationLink,
  useWorkspaceNavigation,
} from "../../components/WorkspaceNavigation";
import { api, eventBase, messageOf } from "../pvs/http";

type Stage = { name: string; submission: { status: string } | null };
type Review = {
  status: string;
  findings: { state: string; severity: string }[];
};
type Project = { public_id: string; name: string };
type Team = {
  team: { name: string; members: unknown[] } | null;
  my_role: string | null;
};
type Summary = {
  team: Team;
  projects: (Project & { stages: Stage[]; review: Review })[];
  event: {
    name: string;
    timezone: string;
    ends_at: string | null;
    status: string;
  };
};

export function ParticipantOverview({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const view = useWorkspaceNavigation()?.view;
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (view && view !== "overview") {
      setLoading(false);
      return;
    }
    let active = true;
    setLoading(true);
    setError("");
    const base = eventBase(workspaceId, eventId);
    Promise.all([
      api<Team>(base + "my-team/"),
      api<Project[]>(base + "projects/"),
      api<Summary["event"]>(`/api/v1/events/${eventId}/`),
    ])
      .then(async ([team, projects, event]) => ({
        team,
        event,
        projects: await Promise.all(
          projects.map(async (project) => {
            const [stages, review] = await Promise.all([
              api<Stage[]>(base + `projects/${project.public_id}/submissions/`),
              api<Review>(base + `projects/${project.public_id}/eligibility/`),
            ]);
            return { ...project, stages, review };
          }),
        ),
      }))
      .then((next) => {
        if (active) setSummary(next);
      })
      .catch((cause: unknown) => {
        if (active) setError(messageOf(cause));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [workspaceId, eventId, view, retry]);
  if (loading) return <LoadingState label="Loading your event status…" />;
  if (error)
    return (
      <ErrorState
        message={error}
        onRetry={() => setRetry((count) => count + 1)}
      />
    );
  if (!summary) return null;
  const changes = summary.projects.reduce(
    (total, project) =>
      total +
      project.review.findings.filter((finding) => finding.state === "open")
        .length,
    0,
  );
  const finalized = summary.projects
    .flatMap((project) => project.stages)
    .filter((stage) => stage.submission?.status === "finalized").length;
  const stages = summary.projects.flatMap((project) => project.stages).length;
  const next =
    summary.event.status !== "open"
      ? "This event is closed"
      : summary.projects.length === 0
        ? "Create your project or find a team"
        : stages === 0
          ? "Submission stages are not configured yet"
          : changes
            ? "Resolve your eligibility findings"
            : finalized < stages
              ? "Prepare and finalize your submission"
              : "Your submissions are finalized";
  const deadline = summary.event.ends_at
    ? new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: summary.event.timezone,
      }).format(new Date(summary.event.ends_at))
    : "No event deadline configured";
  return (
    <section
      aria-label="Participant overview"
      className="cx-participant-overview"
    >
      <header className="cx-next-action">
        <p className="cx-eyebrow">{summary.event.name}</p>
        <h2>{next}</h2>
        <p>
          Event submission deadline: <strong>{deadline}</strong> (
          {summary.event.timezone}). Server deadlines and policy decisions apply
          when you submit.
        </p>
        <DestinationLink id="project" className="cx-button cx-button--primary">
          Open project & submission
        </DestinationLink>
      </header>
      <Grid>
        <DestinationLink id="team">
          <strong>{summary.team.team?.name ?? "Looking for a team"}</strong>
          <span>
            {summary.team.team
              ? `${summary.team.team.members.length} members · ${summary.team.my_role}`
              : "Create a team, accept an invitation, or meet teammates."}
          </span>
        </DestinationLink>
        <DestinationLink id="project">
          <strong>
            {summary.projects.length} project
            {summary.projects.length === 1 ? "" : "s"}
          </strong>
          <span>
            {finalized} / {stages} stage submissions finalized
          </span>
        </DestinationLink>
        <DestinationLink id="project">
          <strong>Eligibility</strong>
          <span>
            {changes
              ? `${changes} open findings require attention`
              : "No open findings"}
          </span>
        </DestinationLink>
      </Grid>
      <section
        className="cx-overview-projects"
        aria-label="Your project status"
      >
        <h3>Project status</h3>
        {summary.projects.length === 0 ? (
          <p>No project yet. Build your team, then start your project.</p>
        ) : (
          <ul>
            {summary.projects.map((project) => (
              <li key={project.public_id}>
                <strong>{project.name}</strong>
                <Badge
                  tone={
                    project.review.status === "cleared"
                      ? "success"
                      : project.review.status === "ineligible"
                        ? "danger"
                        : "info"
                  }
                >
                  {project.review.status.replaceAll("_", " ")}
                </Badge>
                <span>
                  {project.stages
                    .map(
                      (stage) =>
                        `${stage.name}: ${stage.submission?.status ?? "not started"}`,
                    )
                    .join(" · ")}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
      <Grid>
        <DestinationLink id="resources">
          <strong>Event resources</strong>
          <span>Rules, sponsor challenges and on-site participation.</span>
        </DestinationLink>
        <DestinationLink id="messages">
          <strong>Messages</strong>
          <span>Read event announcements and direct messages.</span>
        </DestinationLink>
      </Grid>
      <Button
        variant="secondary"
        onClick={() => setRetry((count) => count + 1)}
      >
        Refresh event status
      </Button>
    </section>
  );
}
