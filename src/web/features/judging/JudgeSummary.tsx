import { Badge } from "../../components/Badge";
import { DestinationLink } from "../../components/WorkspaceNavigation";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { useLoad } from "../pvs/http";

type Candidate = { project: string; name: string; status: string };
type Assignment = {
  project: string;
  status: "pending" | "accepted" | "declined";
};
type Route = {
  stops: {
    project: string;
    project_name: string;
    location_name: string;
    room: string | null;
  }[];
};

function list<T>(value: T[] | null): T[] {
  return Array.isArray(value) ? value : [];
}

export type Progress = {
  total: number;
  done: number;
  remaining: number;
  next: Candidate | null;
};

export function progressOf(candidates: Candidate[]): Progress {
  const done = candidates.filter(
    (candidate) => candidate.status === "submitted",
  ).length;
  return {
    total: candidates.length,
    done,
    remaining: candidates.length - done,
    next:
      candidates.find(
        (candidate) =>
          candidate.status !== "submitted" && candidate.status !== "queued",
      ) ?? null,
  };
}

export function ProgressMeter({ progress }: { progress: Progress }) {
  return (
    <div className="cx-judge-progress">
      <p>
        <strong>
          {progress.done} of {progress.total}
        </strong>{" "}
        scored · {progress.remaining} remaining
      </p>
      <progress
        max={Math.max(progress.total, 1)}
        value={progress.done}
        aria-label="Scoring progress"
      />
    </div>
  );
}

/** Overview: what is assigned, what remains, what is next, conflicts, route. */
export function JudgeSummary({ planBase }: { planBase: string }) {
  const candidates = useLoad<Candidate[]>(`${planBase}candidates/`);
  const assignments = useLoad<Assignment[]>(`${planBase}my-assignments/`);
  const route = useLoad<Route>(`${planBase}my-route/?remaining_only=true`);

  if (candidates.loading) return <LoadingState label="Loading your summary…" />;
  if (candidates.error)
    return (
      <ErrorState
        message={candidates.error.message}
        onRetry={candidates.reload}
      />
    );
  const progress = progressOf(list(candidates.data));
  const declined = list(assignments.data).filter(
    (row) => row.status === "declined",
  ).length;
  const pending = list(assignments.data).filter(
    (row) => row.status === "pending",
  ).length;
  const stop = (route.data?.stops ?? []).find(
    (item) => item.project === progress.next?.project,
  );
  return (
    <section className="cx-judge-summary" aria-label="Your judging summary">
      <div className="cx-next-action">
        <p className="cx-eyebrow">
          {progress.total === 0
            ? "No assignments"
            : progress.remaining === 0
              ? "All done"
              : "Up next"}
        </p>
        <h2>
          {progress.total === 0
            ? "Nothing is assigned to you yet"
            : progress.next
              ? progress.next.name
              : progress.remaining === 0
                ? "Every assigned project is scored"
                : "Remaining ballots are waiting to sync"}
        </h2>
        {stop && (
          <p>
            {stop.room ? `${stop.room} / ` : ""}
            {stop.location_name}
          </p>
        )}
        <ProgressMeter progress={progress} />
        {progress.next && (
          <DestinationLink id="queue" className="cx-button cx-button--primary">
            <strong>Continue scoring</strong>
          </DestinationLink>
        )}
      </div>
      <dl className="cx-judge-facts">
        <div>
          <dt>Assigned</dt>
          <dd>{progress.total}</dd>
        </div>
        <div>
          <dt>Remaining</dt>
          <dd>{progress.remaining}</dd>
        </div>
        <div>
          <dt>Awaiting your response</dt>
          <dd>{pending}</dd>
        </div>
        <div>
          <dt>Recused</dt>
          <dd>{declined > 0 ? <Badge tone="warning">{declined}</Badge> : 0}</dd>
        </div>
      </dl>
    </section>
  );
}
