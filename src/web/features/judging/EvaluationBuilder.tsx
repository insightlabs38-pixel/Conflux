import { useEffect, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";

type Stage = { public_id: string; name: string };
type Criterion = {
  id: string;
  name: string;
  weight: number;
  min_score: number;
  max_score: number;
};
type Plan = {
  public_id: string;
  name: string;
  candidate_type: "project";
  pool_strategy: "all_judges" | "assigned_subset";
  results_visible_to_participants: boolean;
  draft_criteria: Criterion[];
  current_rubric_version: number | null;
};

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

function newCriterion(n: number): Criterion {
  return { id: `criterion-${n}`, name: "", weight: 1, min_score: 0, max_score: 10 };
}

function CriteriaEditor({
  criteria,
  onChange,
}: {
  criteria: Criterion[];
  onChange: (criteria: Criterion[]) => void;
}) {
  return (
    <table>
      <thead>
        <tr>
          <th>Name</th>
          <th>Weight</th>
          <th>Min</th>
          <th>Max</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {criteria.map((criterion, index) => (
          <tr key={criterion.id}>
            <td>
              <input
                aria-label="Criterion name"
                value={criterion.name}
                onChange={(e) => {
                  const next = criteria.slice();
                  next[index] = { ...criterion, name: e.target.value };
                  onChange(next);
                }}
              />
            </td>
            <td>
              <input
                aria-label="Weight"
                type="number"
                min={0}
                value={criterion.weight}
                onChange={(e) => {
                  const next = criteria.slice();
                  next[index] = { ...criterion, weight: Number(e.target.value) };
                  onChange(next);
                }}
              />
            </td>
            <td>
              <input
                aria-label="Minimum score"
                type="number"
                value={criterion.min_score}
                onChange={(e) => {
                  const next = criteria.slice();
                  next[index] = { ...criterion, min_score: Number(e.target.value) };
                  onChange(next);
                }}
              />
            </td>
            <td>
              <input
                aria-label="Maximum score"
                type="number"
                value={criterion.max_score}
                onChange={(e) => {
                  const next = criteria.slice();
                  next[index] = { ...criterion, max_score: Number(e.target.value) };
                  onChange(next);
                }}
              />
            </td>
            <td>
              <Button
                variant="secondary"
                onClick={() => onChange(criteria.filter((_, i) => i !== index))}
              >
                Remove
              </Button>
            </td>
          </tr>
        ))}
      </tbody>
      <tfoot>
        <tr>
          <td colSpan={5}>
            <Button
              variant="secondary"
              onClick={() => onChange([...criteria, newCriterion(criteria.length + 1)])}
            >
              Add criterion
            </Button>
          </td>
        </tr>
      </tfoot>
    </table>
  );
}

function PlanEditor({ base, plan, onChange }: { base: string; plan: Plan; onChange: (plan: Plan) => void }) {
  const [criteria, setCriteria] = useState(plan.draft_criteria);
  const [error, setError] = useState("");
  const planUrl = `${base}${plan.public_id}/`;

  async function patch(fields: Partial<Plan>) {
    setError("");
    try {
      const updated = await request<Plan>(planUrl, "PATCH", fields);
      onChange(updated);
      setCriteria(updated.draft_criteria);
    } catch (cause) {
      setError(message(cause));
    }
  }

  async function publish() {
    setError("");
    try {
      await request(planUrl + "publish-rubric/", "POST");
      onChange(await request<Plan>(planUrl));
    } catch (cause) {
      setError(message(cause));
    }
  }

  return (
    <Card title={plan.name}>
      {error && <p role="alert">{error}</p>}
      <p>
        Published rubric version:{" "}
        <Badge tone={plan.current_rubric_version ? "success" : "neutral"}>
          {plan.current_rubric_version ?? "none yet"}
        </Badge>
      </p>
      <label>
        Pool strategy{" "}
        <select
          value={plan.pool_strategy}
          onChange={(e) => void patch({ pool_strategy: e.target.value as Plan["pool_strategy"] })}
        >
          <option value="all_judges">All judges score every candidate</option>
          <option value="assigned_subset">Judges score an assigned subset</option>
        </select>
      </label>
      <label>
        <input
          type="checkbox"
          checked={plan.results_visible_to_participants}
          onChange={(e) => void patch({ results_visible_to_participants: e.target.checked })}
        />{" "}
        Results visible to participants
      </label>
      <CriteriaEditor criteria={criteria} onChange={setCriteria} />
      <Button onClick={() => void patch({ draft_criteria: criteria })}>Save criteria</Button>
      <Button variant="secondary" onClick={() => void publish()}>
        Publish rubric
      </Button>
    </Card>
  );
}

export function EvaluationBuilder({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const eventBase = `/api/v1/workspaces/${workspaceId}/events/${eventId}/`;
  const [stages, setStages] = useState<Stage[]>([]);
  const [stageId, setStageId] = useState("");
  const [plans, setPlans] = useState<Plan[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    request<Stage[]>(eventBase + "stages/")
      .then(setStages)
      .catch((cause: unknown) => setError(message(cause)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId, eventId]);

  const plansBase = stageId ? `${eventBase}stages/${stageId}/evaluation-plans/` : "";

  useEffect(() => {
    if (!plansBase) return;
    request<Plan[]>(plansBase)
      .then(setPlans)
      .catch((cause: unknown) => setError(message(cause)));
  }, [plansBase]);

  async function createPlan() {
    setError("");
    try {
      const plan = await request<Plan>(plansBase, "POST", {
        name,
        draft_criteria: [newCriterion(1)],
      });
      setPlans((items) => [...items, plan]);
      setName("");
    } catch (cause) {
      setError(message(cause));
    }
  }

  return (
    <Card title="Judging">
      {error && <p role="alert">{error}</p>}
      {stages.length === 0 ? (
        <EmptyState title="Add a stage first to configure judging for it." />
      ) : (
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
      {stageId && (
        <>
          {plans.map((plan) => (
            <PlanEditor
              key={plan.public_id}
              base={plansBase}
              plan={plan}
              onChange={(updated) =>
                setPlans((items) =>
                  items.map((item) => (item.public_id === updated.public_id ? updated : item)),
                )
              }
            />
          ))}
          <label>
            New plan name{" "}
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <Button disabled={!name} onClick={() => void createPlan()}>
            Create evaluation plan
          </Button>
        </>
      )}
    </Card>
  );
}
