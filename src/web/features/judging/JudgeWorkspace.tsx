import { useEffect, useRef, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";

type Event = { public_id: string; name: string };
type Stage = { public_id: string; name: string };
type Plan = { public_id: string; name: string; current_rubric_version: number | null };
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

async function request<T>(url: string, method = "GET", body?: object): Promise<T> {
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
  return response.status === 204 ? (undefined as T) : (response.json() as Promise<T>);
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
  const [error, setError] = useState("");
  const draftUrl = `${base}ballots/${candidate.project}/draft/`;
  const latest = useRef({ scores: {} as Record<string, string>, comment: "" });

  useEffect(() => {
    let active = true;
    request<Draft>(draftUrl)
      .then((draft) => {
        if (!active || !draft) return;
        const loaded = Object.fromEntries(
          Object.entries(draft.responses).map(([id, score]) => [id, String(score)]),
        );
        setScores(loaded);
        setComment(draft.comment);
        latest.current = { scores: loaded, comment: draft.comment };
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draftUrl]);

  useEffect(() => {
    if (!dirty) return;
    const timer = window.setTimeout(() => {
      setSaving(true);
      const numeric = Object.fromEntries(
        Object.entries(latest.current.scores)
          .filter(([, value]) => value !== "")
          .map(([id, value]) => [id, Number(value)]),
      );
      request(draftUrl, "PUT", { responses: numeric, comment: latest.current.comment })
        .catch(() => undefined)
        .finally(() => setSaving(false));
      setDirty(false);
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
    const missing = responses.some((r) => Number.isNaN(r.score));
    if (missing) {
      setError("Every criterion needs a score before you can submit.");
      setSubmitting(false);
      return;
    }
    try {
      await request(`${base}ballots/`, "POST", { project: candidate.project, comment, responses });
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
          <fieldset key={criterion.id} disabled={finalized}>
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
            disabled={finalized}
            value={comment}
            onChange={(event) => {
              setComment(event.target.value);
              latest.current = { ...latest.current, comment: event.target.value };
              setDirty(true);
            }}
          />
        </label>
        {!finalized && (
          <>
            <p role="status">{saving ? "Saving draft…" : dirty ? "Unsaved changes" : "Draft saved"}</p>
            <Button disabled={submitting}>{submitting ? "Submitting…" : "Submit ballot"}</Button>
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
  if (!rubric) return <EmptyState title="This plan has no published rubric yet." />;
  if (candidates.length === 0)
    return <EmptyState title="You have no projects assigned to review right now." />;

  const current = candidates.find((c) => c.project === selected);

  return (
    <section aria-label="Review queue">
      <ul>
        {candidates.map((candidate) => (
          <li key={candidate.project}>
            <button type="button" onClick={() => setSelected(candidate.project)}>
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

  useEffect(() => {
    request<Event[]>(`/api/v1/workspaces/${workspaceId}/participant-events/`)
      .then(setEvents)
      .catch((cause: unknown) => setError(message(cause)));
  }, [workspaceId]);

  useEffect(() => {
    if (!eventId) return;
    request<Stage[]>(`/api/v1/workspaces/${workspaceId}/events/${eventId}/stages/`)
      .then(setStages)
      .catch((cause: unknown) => setError(message(cause)));
  }, [workspaceId, eventId]);

  useEffect(() => {
    if (!stageId) return;
    request<Plan[]>(
      `/api/v1/workspaces/${workspaceId}/events/${eventId}/stages/${stageId}/evaluation-plans/`,
    )
      .then((items) => {
        setPlans(items);
        if (items.length === 1) setPlanId(items[0].public_id);
      })
      .catch((cause: unknown) => setError(message(cause)));
  }, [workspaceId, eventId, stageId]);

  const planBase = planId
    ? `/api/v1/workspaces/${workspaceId}/events/${eventId}/stages/${stageId}/evaluation-plans/${planId}/`
    : "";

  return (
    <section aria-label="Judging">
      <h2>Judging</h2>
      {error && <p role="alert">{error}</p>}
      <label>
        Event{" "}
        <select value={eventId} onChange={(e) => setEventId(e.target.value)}>
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
          <select value={stageId} onChange={(e) => setStageId(e.target.value)}>
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
