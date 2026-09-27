import { useEffect, useRef, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { Inbox } from "../communications/Inbox";
import { JudgeCalendarPanel } from "./JudgeCalendarPanel";
import { JudgeExpertisePanel } from "./JudgeExpertisePanel";
import { JudgeInvitationInbox } from "./JudgeInvitationInbox";

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
  status: "pending" | "drafted" | "submitted";
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
      /* Retain status message. */
    }
    throw new Error(message(detail));
  }
  return response.status === 204
    ? (undefined as T)
    : (response.json() as Promise<T>);
}

function BallotForm({
  base,
  candidate,
  rubric,
  onSubmitted,
}: {
  base: string;
  candidate: Candidate;
  rubric: RubricVersion;
  onSubmitted: () => void;
}) {
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
    request<Draft>(draftUrl)
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
        await request(draftUrl, "PUT", {
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
      if (dirty) await saveDraft();
      else await pending.current;
      await request(`${base}ballots/`, "POST", {
        project: candidate.project,
        comment,
        responses,
      });
      onSubmitted();
    } catch (cause) {
      setError(message(cause));
    } finally {
      setSubmitting(false);
    }
  }

  const finalized = candidate.status === "submitted";

  return (
    <Card title={candidate.name}>
      {error && <p role="alert">{error}</p>}
      <form onSubmit={submit}>
        {rubric.criteria.map((criterion) => (
          <fieldset key={criterion.id} disabled={!loaded || finalized}>
            <legend>
              {criterion.name} ({criterion.min_score}–{criterion.max_score})
            </legend>
            <label>
              Score{" "}
              <input
                type="number"
                min={criterion.min_score}
                max={criterion.max_score}
                required
                value={scores[criterion.id] ?? ""}
                onChange={(event) => setScore(criterion.id, event.target.value)}
              />
            </label>
            {Object.entries(criterion.anchors).map(([level, text]) => (
              <p key={level}>
                <strong>{level}:</strong> {text}
              </p>
            ))}
          </fieldset>
        ))}
        <label>
          Comment{" "}
          <textarea
            disabled={!loaded || finalized}
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
        {!finalized && (
          <>
            <p role="status">
              {!loaded
                ? "Draft unavailable"
                : saving
                  ? "Saving draft…"
                  : dirty
                    ? "Unsaved changes"
                    : "Draft saved"}
            </p>
            {error && dirty && loaded && (
              <Button
                type="button"
                variant="secondary"
                onClick={() => void saveDraft().catch(() => undefined)}
              >
                Retry draft save
              </Button>
            )}
            <Button type="submit" disabled={!loaded || submitting || saving}>
              {submitting ? "Submitting…" : "Submit ballot"}
            </Button>
          </>
        )}
        {finalized && <p role="status">Ballot submitted.</p>}
      </form>
    </Card>
  );
}

function PlanQueue({ base }: { base: string }) {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [rubric, setRubric] = useState<RubricVersion | null>(null);
  const [selected, setSelected] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  function refresh() {
    setLoading(true);
    setError("");
    Promise.all([
      request<Candidate[]>(base + "candidates/"),
      request<RubricVersion | null>(base + "publish-rubric/"),
    ])
      .then(([nextCandidates, nextRubric]) => {
        setCandidates(nextCandidates);
        setRubric(nextRubric);
      })
      .catch((cause: unknown) => setError(message(cause)))
      .finally(() => setLoading(false));
  }

  useEffect(refresh, [base]);

  if (loading) return <LoadingState label="Loading your review queue…" />;
  if (error) return <ErrorState message={error} onRetry={refresh} />;
  if (!rubric)
    return <EmptyState title="This plan has no published rubric yet." />;
  if (candidates.length === 0)
    return (
      <EmptyState title="You have no projects assigned to review right now." />
    );

  const current = candidates.find((c) => c.project === selected);

  return (
    <section aria-label="Review queue">
      <ul>
        {candidates.map((candidate) => (
          <li key={candidate.project}>
            <button
              type="button"
              onClick={() => setSelected(candidate.project)}
            >
              {candidate.name}
            </button>{" "}
            <Badge
              tone={
                candidate.status === "submitted"
                  ? "success"
                  : candidate.status === "drafted"
                    ? "info"
                    : "neutral"
              }
            >
              {candidate.status}
            </Badge>
          </li>
        ))}
      </ul>
      {current && (
        <BallotForm
          key={current.project}
          base={base}
          candidate={current}
          rubric={rubric}
          onSubmitted={refresh}
        />
      )}
    </section>
  );
}

export function JudgeWorkspace({ workspaceId }: { workspaceId: string }) {
  const [events, setEvents] = useState<Event[]>([]);
  const [eventId, setEventId] = useState("");
  const [stages, setStages] = useState<Stage[]>([]);
  const [stageId, setStageId] = useState("");
  const [plans, setPlans] = useState<Plan[]>([]);
  const [planId, setPlanId] = useState("");
  const [error, setError] = useState("");
  const [loadingEvents, setLoadingEvents] = useState(true);
  const [loadingStages, setLoadingStages] = useState(false);
  const [loadingPlans, setLoadingPlans] = useState(false);

  useEffect(() => {
    let active = true;
    request<Event[]>(`/api/v1/workspaces/${workspaceId}/judge-events/`)
      .then((items) => {
        if (active) setEvents(items);
      })
      .catch((cause: unknown) => {
        if (active) setError(message(cause));
      })
      .finally(() => {
        if (active) setLoadingEvents(false);
      });
    return () => {
      active = false;
    };
  }, [workspaceId]);

  useEffect(() => {
    if (!eventId) return;
    let active = true;
    request<Stage[]>(
      `/api/v1/workspaces/${workspaceId}/events/${eventId}/stages/`,
    )
      .then((items) => {
        if (active) setStages(items);
      })
      .catch((cause: unknown) => {
        if (active) setError(message(cause));
      })
      .finally(() => {
        if (active) setLoadingStages(false);
      });
    return () => {
      active = false;
    };
  }, [workspaceId, eventId]);

  useEffect(() => {
    if (!stageId) return;
    let active = true;
    request<Plan[]>(
      `/api/v1/workspaces/${workspaceId}/events/${eventId}/stages/${stageId}/evaluation-plans/`,
    )
      .then((items) => {
        if (!active) return;
        setPlans(items);
        if (items.length === 1) setPlanId(items[0].public_id);
      })
      .catch((cause: unknown) => {
        if (active) setError(message(cause));
      })
      .finally(() => {
        if (active) setLoadingPlans(false);
      });
    return () => {
      active = false;
    };
  }, [workspaceId, eventId, stageId]);

  function chooseEvent(id: string) {
    setEventId(id);
    setStages([]);
    setStageId("");
    setLoadingStages(!!id);
    setPlans([]);
    setPlanId("");
    setLoadingPlans(false);
    setError("");
  }

  function chooseStage(id: string) {
    setStageId(id);
    setLoadingPlans(!!id);
    setPlans([]);
    setPlanId("");
    setError("");
  }

  const planBase = planId
    ? `/api/v1/workspaces/${workspaceId}/events/${eventId}/stages/${stageId}/evaluation-plans/${planId}/`
    : "";

  return (
    <section aria-label="Judging">
      <h2>Judging</h2>
      <Inbox workspaceId={workspaceId} />
      <JudgeInvitationInbox workspaceId={workspaceId} />
      <JudgeExpertisePanel workspaceId={workspaceId} />
      {error && <p role="alert">{error}</p>}
      {loadingEvents && <LoadingState label="Loading judging events…" />}
      {!loadingEvents && !error && events.length === 0 && (
        <EmptyState title="No events are available for judging." />
      )}
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
      {eventId && (
        <JudgeCalendarPanel
          key={`calendar-${eventId}`}
          workspaceId={workspaceId}
          eventId={eventId}
        />
      )}
      {eventId && loadingStages && <LoadingState label="Loading stages…" />}
      {eventId && !loadingStages && !error && stages.length === 0 && (
        <EmptyState title="This event has no stages yet." />
      )}
      {stages.length > 0 && (
        <label>
          Stage{" "}
          <select value={stageId} onChange={(e) => chooseStage(e.target.value)}>
            <option value="">Choose a stage</option>
            {stages.map((stage) => (
              <option key={stage.public_id} value={stage.public_id}>
                {stage.name}
              </option>
            ))}
          </select>
        </label>
      )}
      {stageId && loadingPlans && (
        <LoadingState label="Loading evaluation plans…" />
      )}
      {stageId && !loadingPlans && !error && plans.length === 0 && (
        <EmptyState title="This stage has no evaluation plans yet." />
      )}
      {plans.length > 1 && (
        <label>
          Plan{" "}
          <select value={planId} onChange={(e) => setPlanId(e.target.value)}>
            <option value="">Choose a plan</option>
            {plans.map((plan) => (
              <option key={plan.public_id} value={plan.public_id}>
                {plan.name}
              </option>
            ))}
          </select>
        </label>
      )}
      {planBase && <PlanQueue key={planBase} base={planBase} />}
    </section>
  );
}
