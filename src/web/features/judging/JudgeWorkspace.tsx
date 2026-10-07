import { ProfilePanel } from "../profile/ProfilePanel";
import {
  Destination,
  DestinationLink,
  WorkspaceViewTitle,
} from "../../components/WorkspaceNavigation";
import { PageHeader, Grid } from "../../components/Foundation";
import { useEffect, useRef, useState } from "react";
import { Status } from "../../components/Status";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { Inbox } from "../communications/Inbox";
import { JudgeCalendarPanel } from "./JudgeCalendarPanel";
import { JudgeExpertisePanel } from "./JudgeExpertisePanel";
import { JudgeInvitationInbox } from "./JudgeInvitationInbox";
import { JudgeSummary, ProgressMeter, progressOf } from "./JudgeSummary";
import {
  ArtifactInspector,
  JudgeAssignmentsPanel,
  JudgeRoutePanel,
} from "../pvs";
import { apiJson, describeProblem } from "../../lib/api";
import { useLoad } from "../../hooks/useLoad";
import { useMe } from "../../hooks/useMe";
import { useUrlParam } from "../../lib/urlState";

type Event = { public_id: string; name: string };
type Stage = { public_id: string; name: string };
type Plan = {
  public_id: string;
  name: string;
  current_rubric_version: number | null;
};
type Candidate = {
  project: string;
  name: string;
  status: "pending" | "drafted" | "submitted" | "queued";
};
type Criterion = {
  id: string;
  name: string;
  weight: number;
  min_score: number;
  max_score: number;
  anchors: Record<string, string>;
};
type RubricVersion = { number: number; criteria: Criterion[] };
type Draft = { responses: Record<string, number>; comment: string } | null;

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

// Offline support (VS21): a judge's assignments/rubric are cached on every
// successful load, and a ballot submission that fails because the request
// never reached the server (not because the server rejected it) queues
// locally instead of erroring -- the queue flushes automatically once the
// browser reports connectivity again.
type BallotPayload = {
  project: string;
  comment: string;
  responses: { criterion_id: string; score: number }[];
};
type CachedQueue = { candidates: Candidate[]; rubric: RubricVersion | null };

function isNetworkFailure(cause: unknown): boolean {
  return (
    (typeof navigator !== "undefined" && !navigator.onLine) ||
    cause instanceof TypeError
  );
}

function readJSON<T>(key: string): T | null {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

function writeJSON(key: string, value: unknown): void {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* Storage unavailable (private browsing, quota) -- offline support
       degrades to "try again once online" rather than failing loudly. */
  }
}

// Offline state belongs to the account that produced it: the cache holds that judge's assignments
// and the outbox their unsent ballots. Keys are scoped by user, so on a shared device one judge's
// queued ballots are never replayed as another judge, and one judge's queue is never shown to the
// next. With no known account nothing is stored (offline support degrades to online-only).
// Earlier versions used unscoped keys (`conflux.judge-*.<plan>`); those entries cannot be
// attributed to anyone, so they are left untouched and never read or replayed.
function cacheKey(owner: string, base: string): string {
  return `conflux.judge-cache.${owner}.${base}`;
}

function outboxKey(owner: string, base: string): string {
  return `conflux.judge-outbox.${owner}.${base}`;
}

function readOutbox(owner: string, base: string): BallotPayload[] {
  return owner ? (readJSON<BallotPayload[]>(outboxKey(owner, base)) ?? []) : [];
}

function queueBallot(owner: string, base: string, ballot: BallotPayload): void {
  if (!owner) return;
  const queue = readOutbox(owner, base).filter(
    (item) => item.project !== ballot.project,
  );
  queue.push(ballot);
  writeJSON(outboxKey(owner, base), queue);
}

/** Replays queued ballots in order; stops at the first network failure
 * (still offline) but drops an entry the server actually rejects (e.g. a
 * peer already submitted one first) since re-sending it can never help.
 * Returns how many entries are left in the queue.
 */
async function flushOutbox(owner: string, base: string): Promise<number> {
  const queue = readOutbox(owner, base);
  const remaining: BallotPayload[] = [];
  for (const [index, ballot] of queue.entries()) {
    try {
      await apiJson(`${base}ballots/`, "POST", ballot);
    } catch (cause) {
      if (isNetworkFailure(cause)) {
        remaining.push(...queue.slice(index));
        break;
      }
      // A real rejection (validation error, duplicate submission): drop it,
      // there is nothing further offline retry can do about it.
    }
  }
  writeJSON(outboxKey(owner, base), remaining);
  return remaining.length;
}

function BallotForm({
  owner,
  base,
  candidate,
  rubric,
  position,
  onPrevious,
  onNext,
  onRecuse,
  onSubmitted,
  onQueued,
}: {
  owner: string;
  base: string;
  candidate: Candidate;
  rubric: RubricVersion;
  position: string;
  onPrevious: (() => void) | null;
  onNext: (() => void) | null;
  onRecuse: () => void;
  onSubmitted: (continueToNext: boolean) => void;
  onQueued: (continueToNext: boolean) => void;
}) {
  const advance = useRef(false);
  const [scores, setScores] = useState<Record<string, string>>({});
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState("");
  const draftUrl = `${base}ballots/${candidate.project}/draft/`;
  const latest = useRef({ scores: {} as Record<string, string>, comment: "" });
  const pending = useRef<Promise<void>>(Promise.resolve());

  useEffect(() => {
    let active = true;
    apiJson<Draft>(draftUrl)
      .then((draft) => {
        if (!active) return;
        if (!draft) {
          setLoaded(true);
          return;
        }
        const loaded = Object.fromEntries(
          Object.entries(draft.responses).map(([id, score]) => [
            id,
            String(score),
          ]),
        );
        setScores(loaded);
        setComment(draft.comment);
        latest.current = { scores: loaded, comment: draft.comment };
        setLoaded(true);
      })
      .catch((cause: unknown) => {
        if (active) setError(message(cause));
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draftUrl]);

  function saveDraft() {
    const snapshot = {
      ...latest.current,
      scores: { ...latest.current.scores },
    };
    const numeric = Object.fromEntries(
      Object.entries(snapshot.scores)
        .filter(([, value]) => value !== "")
        .map(([id, value]) => [id, Number(value)]),
    );
    setSaving(true);
    const work = pending.current
      .catch(() => undefined)
      .then(async () => {
        await apiJson(draftUrl, "PUT", {
          responses: numeric,
          comment: snapshot.comment,
        });
        if (JSON.stringify(latest.current) === JSON.stringify(snapshot))
          setDirty(false);
        setError("");
      });
    pending.current = work;
    return work
      .catch((cause: unknown) => {
        setError(`Draft not saved: ${message(cause)}`);
        throw cause;
      })
      .finally(() => {
        if (pending.current === work) setSaving(false);
      });
  }

  useEffect(() => {
    if (!dirty) return;
    const timer = window.setTimeout(() => {
      void saveDraft().catch(() => undefined);
    }, 700);
    return () => window.clearTimeout(timer);
  }, [scores, comment, dirty, draftUrl]);

  function setScore(criterionId: string, value: string) {
    const next = { ...scores, [criterionId]: value };
    setScores(next);
    latest.current = { ...latest.current, scores: next };
    setDirty(true);
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const continueToNext = advance.current;
    advance.current = false;
    setSubmitting(true);
    setError("");
    const responses = rubric.criteria.map((criterion) => ({
      criterion_id: criterion.id,
      score: Number(scores[criterion.id]),
    }));
    const missing = rubric.criteria.some(
      (criterion) =>
        scores[criterion.id] === "" || scores[criterion.id] === undefined,
    );
    if (missing) {
      setError("Every criterion needs a score before you can submit.");
      setSubmitting(false);
      return;
    }
    try {
      if (!loaded) throw new Error("Draft has not loaded.");
      try {
        if (dirty) await saveDraft();
        else await pending.current;
      } catch (draftCause) {
        // Offline: the draft PUT can't reach the server either, but the
        // ballot POST below carries the same responses/comment, so the
        // draft step is skippable rather than fatal here.
        if (!isNetworkFailure(draftCause)) throw draftCause;
      }
      await apiJson(`${base}ballots/`, "POST", {
        project: candidate.project,
        comment,
        responses,
      });
      onSubmitted(continueToNext);
    } catch (cause) {
      if (isNetworkFailure(cause)) {
        queueBallot(owner, base, {
          project: candidate.project,
          comment,
          responses,
        });
        setError("");
        onQueued(continueToNext);
      } else {
        setError(message(cause));
      }
    } finally {
      setSubmitting(false);
    }
  }

  const finalized = candidate.status === "submitted";
  const queued = candidate.status === "queued";

  const scored = rubric.criteria.filter(
    (criterion) => (scores[criterion.id] ?? "") !== "",
  ).length;
  const locked = !loaded || finalized || queued;
  // A submitted ballot's draft is cleared server-side; do not show empty fields as if unscored.
  const recordedOnly = finalized && loaded && scored === 0;

  return (
    <div className="cx-judge-scoring" id="judge-scoring" tabIndex={-1}>
      <Card title={candidate.name}>
        <p className="cx-judge-scoring__meta">
          <span>{position}</span>
          <Status tone={finalized ? "success" : queued ? "warning" : "info"}>
            {candidate.status}
          </Status>
          {!finalized && !queued && (
            <Button type="button" variant="secondary" onClick={onRecuse}>
              Recuse or report a conflict
            </Button>
          )}
        </p>
        {error && <p role="alert">{error}</p>}
        <form onSubmit={submit}>
          {!recordedOnly && (
            <p className="cx-muted">
              {scored} of {rubric.criteria.length} criteria scored
            </p>
          )}
          {recordedOnly && (
            <p className="cx-muted">
              Your scores for this project are recorded and locked. Peer scores
              are never shown.
            </p>
          )}
          {(recordedOnly ? [] : rubric.criteria).map((criterion) => (
            <fieldset
              key={criterion.id}
              className="cx-criterion"
              disabled={locked}
            >
              <legend>
                {criterion.name} ({criterion.min_score}–{criterion.max_score})
              </legend>
              <p className="cx-criterion__weight">Weight {criterion.weight}</p>
              {Object.entries(criterion.anchors).map(([level, text]) => (
                <p key={level} className="cx-criterion__anchor">
                  <strong>{level}:</strong> {text}
                </p>
              ))}
              <label>
                Score{" "}
                <input
                  type="number"
                  inputMode="numeric"
                  min={criterion.min_score}
                  max={criterion.max_score}
                  required
                  value={scores[criterion.id] ?? ""}
                  onChange={(event) =>
                    setScore(criterion.id, event.target.value)
                  }
                />
              </label>
            </fieldset>
          ))}
          <label className="cx-judge-comment" hidden={recordedOnly}>
            Comment{" "}
            <textarea
              disabled={locked}
              rows={4}
              value={comment}
              onChange={(event) => {
                setComment(event.target.value);
                latest.current = {
                  ...latest.current,
                  comment: event.target.value,
                };
                setDirty(true);
              }}
            />
          </label>
          <div className="cx-judge-actions">
            {!finalized && !queued && (
              <p role="status" className="cx-judge-actions__status">
                {!loaded
                  ? "Draft unavailable"
                  : saving
                    ? "Saving draft…"
                    : dirty
                      ? "Unsaved changes"
                      : "Draft saved"}
              </p>
            )}
            {finalized && (
              <p role="status" className="cx-judge-actions__status">
                Ballot submitted.
              </p>
            )}
            {queued && (
              <p role="status" className="cx-judge-actions__status">
                Queued offline — will submit automatically once you're back
                online.
              </p>
            )}
            <Button
              type="button"
              variant="secondary"
              disabled={!onPrevious}
              onClick={() => onPrevious?.()}
            >
              Previous project
            </Button>
            <Button
              type="button"
              variant="secondary"
              disabled={!onNext}
              onClick={() => onNext?.()}
            >
              Next project
            </Button>
            {!finalized && !queued && (
              <>
                {error && dirty && loaded && (
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => void saveDraft().catch(() => undefined)}
                  >
                    Retry draft save
                  </Button>
                )}
                <Button
                  variant="primary"
                  type="submit"
                  disabled={!loaded || submitting || saving}
                  onClick={() => {
                    advance.current = false;
                  }}
                >
                  {submitting ? "Submitting…" : "Submit ballot"}
                </Button>
                <Button
                  type="submit"
                  variant="secondary"
                  disabled={!loaded || submitting || saving}
                  onClick={() => {
                    advance.current = true;
                  }}
                >
                  Submit and continue
                </Button>
              </>
            )}
          </div>
        </form>
      </Card>
    </div>
  );
}

function PlanQueue({
  owner,
  base,
  workspaceId,
  eventId,
}: {
  owner: string;
  base: string;
  workspaceId: string;
  eventId: string;
}) {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [rubric, setRubric] = useState<RubricVersion | null>(null);
  const [selected, setSelected] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [offline, setOffline] = useState(false);
  const [queuedCount, setQueuedCount] = useState(
    () => readOutbox(owner, base).length,
  );

  function refresh() {
    setLoading(true);
    setError("");
    Promise.all([
      apiJson<Candidate[]>(base + "candidates/"),
      apiJson<RubricVersion | null>(base + "publish-rubric/"),
    ])
      .then(async ([nextCandidates, nextRubric]) => {
        setCandidates(nextCandidates);
        setRubric(nextRubric);
        setOffline(false);
        if (owner)
          writeJSON(cacheKey(owner, base), {
            candidates: nextCandidates,
            rubric: nextRubric,
          } satisfies CachedQueue);
        const before = readOutbox(owner, base).length;
        if (before > 0) {
          const left = await flushOutbox(owner, base);
          setQueuedCount(left);
          if (left < before) refresh(); // progress was made: re-fetch statuses
        } else {
          setQueuedCount(0);
        }
      })
      .catch((cause: unknown) => {
        const cached = owner
          ? readJSON<CachedQueue>(cacheKey(owner, base))
          : null;
        if (isNetworkFailure(cause) && cached) {
          setCandidates(cached.candidates);
          setRubric(cached.rubric);
          setOffline(true);
          setQueuedCount(readOutbox(owner, base).length);
        } else {
          setError(message(cause));
        }
      })
      .finally(() => setLoading(false));
  }

  useEffect(refresh, [base, owner]);

  useEffect(() => {
    window.addEventListener("online", refresh);
    return () => window.removeEventListener("online", refresh);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [base, owner]);

  if (loading) return <LoadingState label="Loading your review queue…" />;
  if (error)
    return <ErrorState kind="read" message={error} onRetry={refresh} />;
  if (!rubric)
    return (
      <EmptyState
        title="This plan has no published rubric yet."
        why="Scoring starts once the organizer publishes the rubric; it will appear here."
      />
    );
  if (candidates.length === 0)
    return (
      <EmptyState
        title="You have no projects assigned to review right now."
        why="Assignments appear here once the organizer publishes them. Ask the organizer if you expected some."
      />
    );

  const outboxProjects = new Set(
    readOutbox(owner, base).map((item) => item.project),
  );
  const displayCandidates = candidates.map((candidate) =>
    outboxProjects.has(candidate.project)
      ? { ...candidate, status: "queued" as const }
      : candidate,
  );
  const currentIndex = displayCandidates.findIndex(
    (c) => c.project === selected,
  );
  const current = currentIndex >= 0 ? displayCandidates[currentIndex] : null;
  const progress = progressOf(displayCandidates);

  function choose(project: string) {
    setSelected(project);
    window.setTimeout(
      () =>
        document
          .getElementById("judge-scoring")
          ?.scrollIntoView?.({ block: "start" }),
      0,
    );
  }

  function afterSubmit(continueToNext: boolean) {
    if (continueToNext) {
      const following = [
        ...displayCandidates.slice(currentIndex + 1),
        ...displayCandidates.slice(0, currentIndex),
      ].find((c) => c.status !== "submitted" && c.status !== "queued");
      if (following) choose(following.project);
    }
  }

  function recuse() {
    const target = document.getElementById("judge-assignments");
    target?.scrollIntoView?.({ block: "start" });
    target?.focus();
  }

  return (
    <section aria-label="Review queue" className="cx-judge-desk">
      {offline && (
        <p role="status">
          You're offline — showing your last cached assignments and rubric.
        </p>
      )}
      {queuedCount > 0 && (
        <p role="status">
          {queuedCount} ballot{queuedCount === 1 ? "" : "s"} queued, waiting to
          sync.
        </p>
      )}
      <ProgressMeter progress={progress} />
      <div className="cx-judge-desk__layout">
        <ul className="cx-judge-list" aria-label="Assigned projects">
          {displayCandidates.map((candidate) => (
            <li
              key={candidate.project}
              data-current={candidate.project === selected || undefined}
            >
              <button
                className="cx-judge-list__button"
                type="button"
                onClick={() => choose(candidate.project)}
              >
                {candidate.name}
              </button>
              {progress.next?.project === candidate.project && (
                <Status tone="info">Next</Status>
              )}
              <Status
                tone={
                  candidate.status === "submitted"
                    ? "success"
                    : candidate.status === "queued"
                      ? "warning"
                      : candidate.status === "drafted"
                        ? "info"
                        : "neutral"
                }
              >
                {candidate.status}
              </Status>
            </li>
          ))}
        </ul>
        {current ? (
          <div className="cx-judge-workarea">
            <a className="cx-judge-jump" href="#judge-scoring">
              Jump to scoring
            </a>
            <div className="cx-judge-evidence">
              <ArtifactInspector
                key={`inspect-${current.project}`}
                workspaceId={workspaceId}
                eventId={eventId}
                projectId={current.project}
              />
            </div>
            <BallotForm
              key={current.project}
              owner={owner}
              base={base}
              candidate={current}
              rubric={rubric}
              position={`Project ${currentIndex + 1} of ${displayCandidates.length}`}
              onPrevious={
                currentIndex > 0
                  ? () => choose(displayCandidates[currentIndex - 1].project)
                  : null
              }
              onNext={
                currentIndex < displayCandidates.length - 1
                  ? () => choose(displayCandidates[currentIndex + 1].project)
                  : null
              }
              onRecuse={recuse}
              onSubmitted={(next) => {
                refresh();
                afterSubmit(next);
              }}
              onQueued={(next) => {
                setQueuedCount(readOutbox(owner, base).length);
                afterSubmit(next);
              }}
            />
          </div>
        ) : (
          <p className="cx-muted">
            {progress.next
              ? `Choose a project to begin — ${progress.next.name} is next.`
              : "Choose a project to review."}
          </p>
        )}
      </div>
    </section>
  );
}

export function JudgeWorkspace({ workspaceId }: { workspaceId: string }) {
  // Whose offline queue and cache this is (see the storage notes above).
  const owner = useMe().data?.public_id ?? "";
  // Event, stage and plan are context (lib/urlState.ts): a refresh or a shared link reopens the
  // same review queue. Each level clears the ones below it. The URL is only a request: a value is
  // honoured once it appears in what the server lists for this judge, otherwise it is dropped.
  const [requestedEvent, setEventParam] = useUrlParam("event", {
    clears: ["stage", "plan"],
  });
  const [requestedStage, setStageParam] = useUrlParam("stage", {
    clears: ["plan"],
  });
  const [requestedPlan, setPlanParam] = useUrlParam("plan");
  const eventsLoad = useLoad<Event[]>(
    `/api/v1/workspaces/${workspaceId}/judge-events/`,
    { describe: describeProblem },
  );
  const events = eventsLoad.data ?? [];
  const loadingEvents = eventsLoad.data === null && eventsLoad.error === null;
  const eventId =
    !loadingEvents && events.some((item) => item.public_id === requestedEvent)
      ? requestedEvent
      : "";
  // Each list is a query keyed by its URL, so it always belongs to the event/stage in the URL.
  const stagesLoad = useLoad<Stage[]>(
    eventId
      ? `/api/v1/workspaces/${workspaceId}/events/${eventId}/stages/`
      : null,
    { describe: describeProblem },
  );
  const stages = stagesLoad.data ?? [];
  const loadingStages =
    eventId !== "" && stagesLoad.data === null && stagesLoad.error === null;
  const stageId =
    eventId && stages.some((item) => item.public_id === requestedStage)
      ? requestedStage
      : "";
  const plansLoad = useLoad<Plan[]>(
    stageId
      ? `/api/v1/workspaces/${workspaceId}/events/${eventId}/stages/${stageId}/evaluation-plans/`
      : null,
    { describe: describeProblem },
  );
  const plans = plansLoad.data ?? [];
  const loadingPlans =
    stageId !== "" && plansLoad.data === null && plansLoad.error === null;
  const planId =
    stageId && plans.some((item) => item.public_id === requestedPlan)
      ? requestedPlan
      : "";
  const error =
    eventsLoad.error?.message ||
    stagesLoad.error?.message ||
    plansLoad.error?.message ||
    "";

  // Normalize the URL to what is actually valid. This is derived from rendered state (not done in
  // the fetch callbacks) so a correction can never act on a location the user has already left.
  useEffect(() => {
    if (!loadingEvents && requestedEvent && !eventId)
      setEventParam("", { replace: true });
  }, [loadingEvents, requestedEvent, eventId, setEventParam]);
  useEffect(() => {
    if (eventId && stagesLoad.data && requestedStage && !stageId)
      setStageParam("", { replace: true });
  }, [eventId, stagesLoad.data, requestedStage, stageId, setStageParam]);
  useEffect(() => {
    if (!stageId || !plansLoad.data) return;
    if (requestedPlan && !planId) setPlanParam("", { replace: true });
    else if (!requestedPlan && plansLoad.data.length === 1)
      setPlanParam(plansLoad.data[0].public_id, { replace: true });
  }, [stageId, plansLoad.data, requestedPlan, planId, setPlanParam]);

  const chooseEvent = (id: string) => setEventParam(id);
  const chooseStage = (id: string) => setStageParam(id);

  const planBase = planId
    ? `/api/v1/workspaces/${workspaceId}/events/${eventId}/stages/${stageId}/evaluation-plans/${planId}/`
    : "";

  return (
    <section aria-label="Judging">
      <PageHeader
        as="h1"
        title="Judging"
        eyebrow={
          events.find((event) => event.public_id === eventId)?.name ||
          "Your judging workspace"
        }
      />
      <WorkspaceViewTitle role="judge" />
      <Destination id="messages">
        <Inbox workspaceId={workspaceId} />
      </Destination>
      <Destination id="profile" lazy>
        <ProfilePanel workspaceId={workspaceId} />
        <JudgeInvitationInbox workspaceId={workspaceId} />
      </Destination>
      <Destination id="profile" lazy>
        <JudgeExpertisePanel workspaceId={workspaceId} />
      </Destination>
      {error && <p role="alert">{error}</p>}
      {loadingEvents && <LoadingState label="Loading judging events…" />}
      {!loadingEvents && !error && events.length === 0 && (
        <EmptyState
          title="No events are available for judging."
          why="Events appear here when you are invited as a judge and judging is open."
        />
      )}
      <div
        className="cx-judge-context"
        role="group"
        aria-label="Judging context"
      >
        <label>
          Event{" "}
          <select value={eventId} onChange={(e) => chooseEvent(e.target.value)}>
            <option value="">Choose an event</option>
            {events.map((event) => (
              <option key={event.public_id} value={event.public_id}>
                {event.name}
              </option>
            ))}
          </select>
        </label>
        {stages.length > 0 && (
          <label>
            Stage{" "}
            <select
              value={stageId}
              onChange={(e) => chooseStage(e.target.value)}
            >
              <option value="">Choose a stage</option>
              {stages.map((stage) => (
                <option key={stage.public_id} value={stage.public_id}>
                  {stage.name}
                </option>
              ))}
            </select>
          </label>
        )}
        {plans.length > 1 && (
          <label>
            Plan{" "}
            <select
              value={planId}
              onChange={(e) => setPlanParam(e.target.value)}
            >
              <option value="">Choose a plan</option>
              {plans.map((plan) => (
                <option key={plan.public_id} value={plan.public_id}>
                  {plan.name}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
      {eventId && loadingStages && <LoadingState label="Loading stages…" />}
      {eventId && !loadingStages && !error && stages.length === 0 && (
        <EmptyState
          title="This event has no stages yet."
          why="The organizer has not added a stage; judging cannot start until they do."
        />
      )}
      {stageId && loadingPlans && (
        <LoadingState label="Loading evaluation plans…" />
      )}
      {stageId && !loadingPlans && !error && plans.length === 0 && (
        <EmptyState
          title="This stage has no evaluation plans yet."
          why="The organizer has not created an evaluation plan for this stage; scoring waits for one."
        />
      )}
      {eventId && (
        <Destination id={["overview", "schedule"]}>
          <JudgeCalendarPanel
            key={`calendar-${eventId}`}
            workspaceId={workspaceId}
            eventId={eventId}
          />
        </Destination>
      )}
      <Destination id="overview">
        <section className="cx-workspace-overview" aria-label="Judge overview">
          <h2>Your judging</h2>
          {planBase ? (
            <JudgeSummary key={`summary-${planBase}`} planBase={planBase} />
          ) : (
            <p className="cx-muted">
              Choose an event, stage and plan to see what is assigned, what
              remains and what is next.
            </p>
          )}
          <Grid>
            <DestinationLink id="queue">
              <strong>Open your review queue</strong>
              <span>
                Assignments, rubric scoring, and safe artifact inspection.
              </span>
            </DestinationLink>
            <DestinationLink id="schedule">
              <strong>Plan your next stop</strong>
              <span>See your event schedule and remaining judging route.</span>
            </DestinationLink>
            <DestinationLink id="profile">
              <strong>Keep your expertise current</strong>
              <span>
                Respond to invitations and update your judging expertise.
              </span>
            </DestinationLink>
          </Grid>
        </section>
      </Destination>
      {planBase && (
        <>
          <Destination id="queue">
            <JudgeAssignmentsPanel
              key={`assign-${planBase}`}
              planBase={planBase}
            />
          </Destination>
          <Destination id="schedule">
            <JudgeRoutePanel key={`route-${planBase}`} planBase={planBase} />
          </Destination>
          <Destination id="queue">
            <PlanQueue
              key={`${owner}:${planBase}`}
              owner={owner}
              base={planBase}
              workspaceId={workspaceId}
              eventId={eventId}
            />
          </Destination>
        </>
      )}
    </section>
  );
}
