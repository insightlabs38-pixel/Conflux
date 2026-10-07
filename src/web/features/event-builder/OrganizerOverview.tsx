import { useState, type ReactNode } from "react";
import { Status } from "../../components/Status";
import {
  DestinationLink,
  useModuleEnabled,
} from "../../components/WorkspaceNavigation";
import { unresolvedItems, type Readiness } from "../../hooks/useReadiness";
import { useLoad, type Loaded } from "../pvs/http";
import {
  dayHeading,
  rangeText,
  timelineUrl,
  wall,
  type Timeline,
} from "../../lib/timeline";

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

/**
 * One figure of the summary strip: a number that is a link to the records behind it, and one line
 * of detail. A figure that is still loading or failed says so in its own place, so the others
 * stay readable (S-LOAD, S-ERR); nothing here is a card (V-SLOP-3).
 */
function Figure({
  label,
  load,
  figure,
  unit,
  detail,
  destination,
  section,
}: {
  label: string;
  load: Pick<Loaded<unknown>, "data" | "error" | "loading" | "reload">;
  figure: ReactNode;
  unit: string;
  detail: ReactNode;
  destination: string;
  section?: string;
}) {
  return (
    <li className="cx-strip__item" data-figure={label}>
      {load.loading && <span className="cx-muted">{label}: Loading…</span>}
      {load.error && (
        <span role="alert">
          {label} could not load.{" "}
          <button type="button" onClick={load.reload}>
            Retry
          </button>
        </span>
      )}
      {!load.loading && !load.error && load.data !== null && (
        <>
          <DestinationLink
            id={destination}
            section={section}
            className="cx-strip__link"
          >
            <strong>{figure}</strong> {unit}
          </DestinationLink>
          <span className="cx-muted">{detail}</span>
        </>
      )}
    </li>
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
  readiness,
}: {
  workspaceId: string;
  eventId: string;
  starts: string | null;
  ends: string | null;
  status: string;
  readiness: Loaded<Readiness>;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;
  // A card for a module that is off would link to a destination that is not offered.
  const eligibilityOn = useModuleEnabled("eligibility_review");
  const onsiteOn = useModuleEnabled("onsite");
  const applications = useLoad<Application[]>(`${base}applications/`);
  const reviews = useLoad<Review[]>(`${base}eligibility-reviews/`);
  const workload = useLoad<Workload[]>(`${base}judge-workload/`);
  const requests = useLoad<PublicationRequest[]>(
    `${base}result-publication-requests/`,
  );
  const onsite = useLoad<Onsite>(`${base}onsite-summary/`);
  // "Coming up" is judged from the moment the overview opened (a stable request, not a clock tick).
  const [openedAt] = useState(
    () => new Date().toISOString().slice(0, 16) + ":00Z",
  );
  const upcoming = useLoad<Timeline>(
    timelineUrl(workspaceId, eventId, { from: openedAt, limit: 5 }),
  );

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

  const issues: {
    key: string;
    text: string;
    destination: string;
    section?: string;
  }[] = [];
  if (eligibilityOn && needsReview > 0)
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
  if (onsiteOn && unplaced > 0)
    issues.push({
      key: "onsite",
      text: `${unplaced} project${unplaced === 1 ? "" : "s"} without a table or booth`,
      destination: "onsite",
    });
  const clashes = list(upcoming.data?.conflicts ?? null).length;
  const coming = list(upcoming.data?.items ?? null);
  if (clashes > 0)
    issues.push({
      key: "timeline",
      text: `${clashes} scheduling conflict${clashes === 1 ? "" : "s"} among what is coming up`,
      destination: "operations",
      section: "TimelinePanel",
    });
  // What readiness says is missing (the same server list as Setup and operations), with its fix.
  unresolvedItems(readiness.data).forEach((item) =>
    issues.push({
      key: `ready-${item.id}`,
      text: item.detail,
      destination: item.fix.destination,
      section: item.fix.section || undefined,
    }),
  );

  return (
    <section
      className="cx-workspace-overview cx-ops"
      aria-label="Event overview"
    >
      <h3>Event operations</h3>
      <p className="cx-ops__timing">
        <Status tone={status === "open" ? "success" : "neutral"}>
          {status}
        </Status>{" "}
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
                  section={issue.section}
                  className="cx-inline-link"
                >
                  {issue.text}
                </DestinationLink>
              </li>
            ))}
          </ul>
        )}
      </section>
      <ul className="cx-strip" aria-label="Event summary">
        <Figure
          label="Registrations"
          load={applications}
          figure={apps.length}
          unit="applications"
          detail={`${apps.filter((a) => a.status === "approved").length} approved · ${apps.filter((a) => a.status === "pending").length} pending`}
          destination="participants"
        />
        {eligibilityOn && (
          <Figure
            label="Eligibility workload"
            load={reviews}
            figure={needsReview}
            unit="to review"
            detail={`${rows.length} reviewed records · ${rows.filter((r) => r.status === "cleared").length} cleared`}
            destination="eligibility"
          />
        )}
        <Figure
          label="Judging progress"
          load={workload}
          figure={`${submitted} of ${assigned}`}
          unit="ballots submitted"
          detail={`${judges.length} judges`}
          destination="judging"
        />
        <Figure
          label="Results and publication"
          load={requests}
          figure={awaitingApproval}
          unit="awaiting approval"
          detail={`${reqs.filter((r) => r.status === "approved").length} approved`}
          destination="results"
        />
        {onsiteOn && (
          <Figure
            label="On-site readiness"
            load={onsite}
            figure={
              onsite.data
                ? `${onsite.data.checked_in} of ${onsite.data.participants}`
                : ""
            }
            unit="checked in"
            detail={
              onsite.data
                ? `${onsite.data.projects_placed} of ${onsite.data.projects} projects placed`
                : ""
            }
            destination="onsite"
          />
        )}
      </ul>
      <section className="cx-ops-coming" aria-label="Coming up">
        <h4>Coming up</h4>
        {upcoming.loading && <p className="cx-muted">Loading…</p>}
        {upcoming.error && (
          <p role="alert">
            Coming up could not load.{" "}
            <button type="button" onClick={upcoming.reload}>
              Retry
            </button>
          </p>
        )}
        {!upcoming.loading &&
          !upcoming.error &&
          upcoming.data !== null &&
          (coming.length === 0 ? (
            <p>Nothing else is scheduled.</p>
          ) : (
            <ul className="cx-plain-list">
              {coming.map((item) => (
                <li key={item.key}>
                  <span className="cx-muted">
                    {dayHeading(wall(item.local_starts_at).date)}{" "}
                    {rangeText(item)}
                  </span>{" "}
                  {item.label}
                </li>
              ))}
            </ul>
          ))}
        <p>
          <DestinationLink
            id="operations"
            section="TimelinePanel"
            className="cx-inline-link"
          >
            Open the timeline
          </DestinationLink>
        </p>
      </section>
    </section>
  );
}
