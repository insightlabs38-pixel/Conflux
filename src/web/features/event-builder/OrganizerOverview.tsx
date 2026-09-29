import type { ReactNode } from "react";
import { Badge } from "../../components/Badge";
import { DestinationLink } from "../../components/WorkspaceNavigation";
import { useLoad, type Loaded } from "../pvs/http";

type Application = { status: string };
type Review = { status: string; open_findings: number };
type Workload = { assigned_count: number; submitted_count: number };
type PublicationRequest = { status: string };
type Onsite = {
  participants: number;
  checked_in: number;
  projects: number;
  projects_placed: number;
};

function list<T>(value: T[] | null): T[] {
  return Array.isArray(value) ? value : [];
}

function Metric({
  label,
  load,
  render,
  destination,
  action,
}: {
  label: string;
  load: Loaded<unknown>;
  render: () => ReactNode;
  destination: string;
  action: string;
}) {
  return (
    <section className="cx-ops-card" aria-label={label}>
      <h4>{label}</h4>
      {load.loading && <p className="cx-muted">Loading…</p>}
      {load.error && (
        <p role="alert">
          {label} could not load.{" "}
          <button type="button" onClick={load.reload}>
            Retry
          </button>
        </p>
      )}
      {!load.loading && !load.error && load.data !== null && render()}
      <DestinationLink
        id={destination}
        className="cx-button cx-button--secondary"
      >
        {action}
      </DestinationLink>
    </section>
  );
}

function when(value: string | null): string {
  return value
    ? new Date(value).toLocaleString("en-US", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "UTC",
      }) + " UTC"
    : "Not scheduled";
}

/** Operational overview built from existing read endpoints; failures are per card. */
export function OrganizerOverview({
  workspaceId,
  eventId,
  starts,
  ends,
  status,
  checks,
}: {
  workspaceId: string;
  eventId: string;
  starts: string | null;
  ends: string | null;
  status: string;
  checks: string[];
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;
  const applications = useLoad<Application[]>(`${base}applications/`);
  const reviews = useLoad<Review[]>(`${base}eligibility-reviews/`);
  const workload = useLoad<Workload[]>(`${base}judge-workload/`);
  const requests = useLoad<PublicationRequest[]>(
    `${base}result-publication-requests/`,
  );
  const onsite = useLoad<Onsite>(`${base}onsite-summary/`);

  const apps = list(applications.data);
  const rows = list(reviews.data);
  const judges = list(workload.data);
  const reqs = list(requests.data);
  const assigned = judges.reduce((sum, row) => sum + row.assigned_count, 0);
  const submitted = judges.reduce((sum, row) => sum + row.submitted_count, 0);
  const behind = judges.filter(
    (row) => row.assigned_count > 0 && row.submitted_count < row.assigned_count,
  ).length;
  const needsReview = rows.filter(
    (row) => row.status === "pending" || row.status === "needs_remediation",
  ).length;
  const awaitingApproval = reqs.filter(
    (row) => row.status === "pending",
  ).length;
  const unplaced = onsite.data
    ? onsite.data.projects - onsite.data.projects_placed
    : 0;

  const issues: { key: string; text: string; destination: string }[] = [];
  if (needsReview > 0)
    issues.push({
      key: "elig",
      text: `${needsReview} project${needsReview === 1 ? "" : "s"} need eligibility review`,
      destination: "eligibility",
    });
  if (behind > 0)
    issues.push({
      key: "judges",
      text: `${behind} judge${behind === 1 ? " has" : "s have"} unscored assignments`,
      destination: "judging",
    });
  if (awaitingApproval > 0)
    issues.push({
      key: "publish",
      text: `${awaitingApproval} publication request${awaitingApproval === 1 ? "" : "s"} awaiting approval`,
      destination: "results",
    });
  if (unplaced > 0)
    issues.push({
      key: "onsite",
      text: `${unplaced} project${unplaced === 1 ? "" : "s"} without a table or booth`,
      destination: "onsite",
    });
  checks.forEach((check) =>
    issues.push({ key: `check-${check}`, text: check, destination: "setup" }),
  );

  return (
    <section
      className="cx-workspace-overview cx-ops"
      aria-label="Event overview"
    >
      <h3>Event operations</h3>
      <p className="cx-ops__timing">
        <Badge tone={status === "open" ? "success" : "neutral"}>{status}</Badge>{" "}
        Starts {when(starts)} · Ends {when(ends)}
      </p>
      <section className="cx-ops-issues" aria-label="Needs action">
        <h4>Needs action</h4>
        {issues.length === 0 ? (
          <p>Nothing needs attention right now.</p>
        ) : (
          <ul>
            {issues.map((issue) => (
              <li key={issue.key}>
                <DestinationLink
                  id={issue.destination}
                  className="cx-inline-link"
                >
                  {issue.text}
                </DestinationLink>
              </li>
            ))}
          </ul>
        )}
      </section>
      <div className="cx-ops-grid">
        <Metric
          label="Registrations"
          load={applications}
          destination="participants"
          action="Manage participants"
          render={() => (
            <p>
              <strong>{apps.length}</strong> applications ·{" "}
              {apps.filter((a) => a.status === "approved").length} approved ·{" "}
              {apps.filter((a) => a.status === "pending").length} pending
            </p>
          )}
        />
        <Metric
          label="Eligibility workload"
          load={reviews}
          destination="eligibility"
          action="Open review queue"
          render={() => (
            <p>
              <strong>{needsReview}</strong> to review · {rows.length} reviewed
              records · {rows.filter((r) => r.status === "cleared").length}{" "}
              cleared
            </p>
          )}
        />
        <Metric
          label="Judging progress"
          load={workload}
          destination="judging"
          action="Manage judging"
          render={() => (
            <>
              <p>
                <strong>
                  {submitted} of {assigned}
                </strong>{" "}
                ballots submitted · {judges.length} judges
              </p>
              <progress
                max={Math.max(assigned, 1)}
                value={submitted}
                aria-label="Judging progress"
              />
            </>
          )}
        />
        <Metric
          label="Results and publication"
          load={requests}
          destination="results"
          action="Deliberate and publish"
          render={() => (
            <p>
              <strong>{awaitingApproval}</strong> awaiting approval ·{" "}
              {reqs.filter((r) => r.status === "approved").length} approved
            </p>
          )}
        />
        <Metric
          label="On-site readiness"
          load={onsite}
          destination="onsite"
          action="Open on-site desk"
          render={() =>
            onsite.data && (
              <p>
                <strong>
                  {onsite.data.checked_in} of {onsite.data.participants}
                </strong>{" "}
                checked in · {onsite.data.projects_placed} of{" "}
                {onsite.data.projects} projects placed
              </p>
            )
          }
        />
      </div>
    </section>
  );
}
