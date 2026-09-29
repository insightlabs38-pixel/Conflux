import { useEffect, useState } from "react";
import { Badge } from "../../components/Badge";
import { Card } from "../../components/Card";

type ChecklistItem = {
  id: string;
  severity: "blocker" | "warning";
  passed: boolean;
  detail: string;
};
type Checklist = {
  status: "ready" | "warning" | "blocked";
  items: ChecklistItem[];
};

type CappedList<T> = { items: T[]; total: number };

type Summary = {
  participants: {
    participant_count: number;
    unteamed: CappedList<string>;
    team_count: number;
    teams_without_project: CappedList<string>;
  };
  submissions: {
    project_count: number;
    counts: Record<string, number>;
    blocked_projects: CappedList<{ project: string; checks: string[] }>;
    missing_artifacts: CappedList<string>;
  };
  judging: {
    plans: {
      plan: string;
      name: string;
      stage: string;
      candidate_count: number;
      submitted_ballots: number;
      expected_ballots: number | null;
      rubric_published: boolean;
      results_published: boolean;
    }[];
  };
  stages: {
    stages: {
      public_id: string;
      name: string;
      position: number;
      active_entries: number;
      total_entries: number;
    }[];
  };
  publication: {
    event_public: boolean;
    page_configured: boolean;
    page_block_count: number;
    award_count: number;
    awards_published: number;
  };
  moderation: {
    voting_configured: boolean;
    unresolved_signals: CappedList<{
      public_id: string;
      signal_type: string;
      detail: string;
    }>;
  };
};

async function readJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { credentials: "include" });
  if (!response.ok)
    throw new Error(`Operations center request failed (${response.status}).`);
  return response.json() as Promise<T>;
}

function severityTone(item: ChecklistItem): "success" | "warning" | "danger" {
  if (item.passed) return "success";
  return item.severity === "blocker" ? "danger" : "warning";
}

export function OperationsCenter({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/operations/`;
  const [checklist, setChecklist] = useState<Checklist | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([
      readJson<Checklist>(base + "checklist/"),
      readJson<Summary>(base + "summary/"),
    ])
      .then(([nextChecklist, nextSummary]) => {
        if (active) {
          setChecklist(nextChecklist);
          setSummary(nextSummary);
        }
      })
      .catch((cause: unknown) => {
        if (active)
          setError(
            cause instanceof Error
              ? cause.message
              : "Operations center could not load.",
          );
      });
    return () => {
      active = false;
    };
  }, [base]);

  return (
    <Card title="Operations center">
      {error && <p role="alert">{error}</p>}
      {checklist && (
        <section>
          <h4>
            Launch checklist ·{" "}
            <Badge
              tone={
                checklist.status === "ready"
                  ? "success"
                  : checklist.status === "warning"
                    ? "warning"
                    : "danger"
              }
            >
              {checklist.status}
            </Badge>
          </h4>
          <ul>
            {checklist.items.map((item) => (
              <li key={item.id}>
                <Badge tone={severityTone(item)}>
                  {item.passed ? "OK" : item.severity}
                </Badge>{" "}
                {item.detail}
              </li>
            ))}
          </ul>
        </section>
      )}
      {summary && (
        <div className="cx-ops-sections">
          <section>
            <h4>Participants &amp; teams</h4>
            <p>
              {summary.participants.participant_count} participants ·{" "}
              {summary.participants.team_count} teams
            </p>
            {summary.participants.unteamed.total > 0 && (
              <p>
                Unteamed ({summary.participants.unteamed.total}):{" "}
                {summary.participants.unteamed.items.join(", ")}
              </p>
            )}
            {summary.participants.teams_without_project.total > 0 && (
              <p>
                Teams without a project (
                {summary.participants.teams_without_project.total}):{" "}
                {summary.participants.teams_without_project.items.join(", ")}
              </p>
            )}
          </section>
          <section>
            <h4>Submissions</h4>
            <p>
              {summary.submissions.project_count} projects · ready{" "}
              {summary.submissions.counts.ready ?? 0} · warning{" "}
              {summary.submissions.counts.warning ?? 0} · blocked{" "}
              {summary.submissions.counts.blocked ?? 0}
            </p>
            {summary.submissions.blocked_projects.total > 0 && (
              <ul>
                {summary.submissions.blocked_projects.items.map((row) => (
                  <li key={row.project}>
                    <Badge tone="danger">blocked</Badge> {row.project}:{" "}
                    {row.checks.join("; ")}
                  </li>
                ))}
              </ul>
            )}
            {summary.submissions.missing_artifacts.total > 0 && (
              <p>
                No artifacts yet ({summary.submissions.missing_artifacts.total}
                ): {summary.submissions.missing_artifacts.items.join(", ")}
              </p>
            )}
          </section>
          <section>
            <h4>Judging</h4>
            {summary.judging.plans.length === 0 ? (
              <p>No evaluation plans configured.</p>
            ) : (
              <ul>
                {summary.judging.plans.map((plan) => (
                  <li key={plan.plan}>
                    {plan.stage}: {plan.name} — {plan.submitted_ballots}
                    {plan.expected_ballots != null
                      ? `/${plan.expected_ballots}`
                      : ""}{" "}
                    ballots
                    {!plan.rubric_published && (
                      <>
                        {" "}
                        · <Badge tone="danger">no rubric</Badge>
                      </>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
          <section>
            <h4>Stages</h4>
            <ul>
              {summary.stages.stages.map((stage) => (
                <li key={stage.public_id}>
                  {stage.name}: {stage.active_entries} active /{" "}
                  {stage.total_entries} total
                </li>
              ))}
            </ul>
          </section>
          <section>
            <h4>Publication</h4>
            <p>
              Public site:{" "}
              <Badge
                tone={summary.publication.event_public ? "success" : "neutral"}
              >
                {summary.publication.event_public ? "on" : "off"}
              </Badge>
              {" · "}
              Page:{" "}
              <Badge
                tone={
                  summary.publication.page_configured ? "success" : "warning"
                }
              >
                {summary.publication.page_configured
                  ? `${summary.publication.page_block_count} blocks`
                  : "not configured"}
              </Badge>
              {" · "}
              Awards published: {summary.publication.awards_published}/
              {summary.publication.award_count}
            </p>
            {summary.publication.event_public && (
              <p>
                <a href={`?event=${eventId}`} target="_blank" rel="noreferrer">
                  View public event site
                </a>
              </p>
            )}
          </section>
          <section>
            <h4>Moderation</h4>
            {!summary.moderation.voting_configured ? (
              <p>No community voting configured.</p>
            ) : summary.moderation.unresolved_signals.total === 0 ? (
              <p>No unresolved abuse signals.</p>
            ) : (
              <p>
                {summary.moderation.unresolved_signals.total} unresolved abuse
                signal(s) — review in the community voting panel below.
              </p>
            )}
          </section>
        </div>
      )}
    </Card>
  );
}
