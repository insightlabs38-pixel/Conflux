import { useEffect, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { JudgeDirectoryPanel } from "./JudgeDirectoryPanel";

type Stage = { public_id: string; name: string };
type Pool = { public_id: string; name: string };
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
  pool: string | null;
  prize_judging: boolean;
  results_visible_to_participants: boolean;
  feedback_visible_to_participants: boolean;
  feedback_anonymous: boolean;
  draft_criteria: Criterion[];
  current_rubric_version: number | null;
  published_normalization_run: number | null;
};
type Progress = {
  candidate_count: number;
  submitted_ballots: number;
  expected_ballots: number | null;
  completion_ratio: number | null;
  latest_normalization_run: { number: number; converged: boolean } | null;
  results_published: boolean;
};
type RankedProject = {
  rank: number;
  project: string | null;
  project_name: string | null;
};
type Provenance = {
  project_name: string;
  rank: number;
  raw_score: number | null;
  final_score: number;
  tie_break: number | null;
  normalization_run: string;
  ridge_lambda: number;
  converged: boolean;
  grand_mean: number;
  ballot_snapshot_available: boolean;
  ballots:
    | {
        ballot: string;
        judge: string;
        rubric_version: string;
        responses: {
          criterion_id: string;
          criterion_name: string;
          weight: number;
          score: number;
        }[];
        weighted_score: number;
        judge_effect: number;
        adjusted_score: number;
      }[]
    | null;
  awards: {
    award: string;
    name: string;
    rank_at_selection: number | null;
    override_reason: string;
    published: boolean;
  }[];
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

function newCriterion(n: number): Criterion {
  return {
    id: `criterion-${n}`,
    name: "",
    weight: 1,
    min_score: 0,
    max_score: 10,
  };
}

function CriteriaEditor({
  criteria,
  onChange,
}: {
  criteria: Criterion[];
  onChange: (criteria: Criterion[]) => void;
}) {
  return (
    <div
      className="cx-scroll-region"
      role="region"
      aria-label="Rubric criteria table"
      tabIndex={0}
    >
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
                    next[index] = {
                      ...criterion,
                      weight: Number(e.target.value),
                    };
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
                    next[index] = {
                      ...criterion,
                      min_score: Number(e.target.value),
                    };
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
                    next[index] = {
                      ...criterion,
                      max_score: Number(e.target.value),
                    };
                    onChange(next);
                  }}
                />
              </td>
              <td>
                <Button
                  variant="secondary"
                  onClick={() =>
                    onChange(criteria.filter((_, i) => i !== index))
                  }
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
                onClick={() =>
                  onChange([...criteria, newCriterion(criteria.length + 1)])
                }
              >
                Add criterion
              </Button>
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}

function ProgressPanel({ planUrl }: { planUrl: string }) {
  const [progress, setProgress] = useState<Progress | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function refresh() {
    request<Progress>(planUrl + "progress/")
      .then(setProgress)
      .catch((cause: unknown) => setError(message(cause)));
  }

  useEffect(refresh, [planUrl]);

  async function computeAndPublish() {
    setBusy(true);
    setError("");
    try {
      const run = await request<{ public_id: string }>(
        planUrl + "normalization-runs/",
        "POST",
        {},
      );
      await request(planUrl + "publish-results/", "POST", {
        normalization_run: run.public_id,
      });
      refresh();
    } catch (cause) {
      setError(message(cause));
    } finally {
      setBusy(false);
    }
  }

  if (!progress) return null;
  return (
    <div aria-label="Judging progress">
      {error && <p role="alert">{error}</p>}
      <p>
        {progress.submitted_ballots}
        {progress.expected_ballots !== null
          ? ` / ${progress.expected_ballots}`
          : ""}{" "}
        ballots submitted{" "}
        {progress.completion_ratio !== null && (
          <Badge tone={progress.completion_ratio >= 1 ? "success" : "info"}>
            {Math.round(progress.completion_ratio * 100)}%
          </Badge>
        )}
      </p>
      <Button disabled={busy} onClick={() => void computeAndPublish()}>
        {busy ? "Computing…" : "Compute normalization and publish results"}
      </Button>
      {progress.results_published && (
        <>
          <p>
            Results published.{" "}
            <a href={planUrl + "results.csv"}>Download CSV</a>
          </p>
          <ProvenanceExplorer planUrl={planUrl} />
        </>
      )}
    </div>
  );
}

function ProvenanceExplorer({ planUrl }: { planUrl: string }) {
  const [projects, setProjects] = useState<RankedProject[]>([]);
  const [selected, setSelected] = useState("");
  const [provenance, setProvenance] = useState<Provenance | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    request<RankedProject[]>(planUrl + "results/")
      .then((rows) => {
        if (!active) return;
        setProjects(rows);
        setSelected(rows.find((row) => row.project)?.project ?? "");
      })
      .catch((cause: unknown) => {
        if (active) setError(message(cause));
      });
    return () => {
      active = false;
    };
  }, [planUrl]);

  useEffect(() => {
    if (!selected) return;
    let active = true;
    setProvenance(null);
    request<Provenance>(planUrl + `provenance/${selected}/`)
      .then((entry) => {
        if (active) setProvenance(entry);
      })
      .catch((cause: unknown) => {
        if (active) setError(message(cause));
      });
    return () => {
      active = false;
    };
  }, [planUrl, selected]);

  return (
    <section aria-label="Judging provenance">
      <h4>Judging provenance</h4>
      {error && <p role="alert">{error}</p>}
      {projects.length === 0 ? (
        <p>No scored projects in this published run.</p>
      ) : (
        <label>
          Project{" "}
          <select
            aria-label="Project provenance"
            value={selected}
            onChange={(event) => {
              setError("");
              setSelected(event.target.value);
            }}
          >
            {projects
              .filter((row) => row.project)
              .map((row) => (
                <option key={row.project} value={row.project ?? ""}>
                  #{row.rank} {row.project_name}
                </option>
              ))}
          </select>
        </label>
      )}
      {provenance && (
        <>
          <p>
            #{provenance.rank} {provenance.project_name}: raw{" "}
            {provenance.raw_score?.toFixed(2) ?? "—"}, normalized{" "}
            {provenance.final_score.toFixed(2)}
            {provenance.tie_break !== null &&
              ` · tie-break ${provenance.tie_break}`}
            .
          </p>
          <p>
            Normalization run {provenance.normalization_run} · judge-bias
            strength {provenance.ridge_lambda} · grand mean{" "}
            {provenance.grand_mean.toFixed(2)} ·{" "}
            {provenance.converged ? "converged" : "not converged"}
          </p>
          {!provenance.ballot_snapshot_available ? (
            <p>Authored-ballot snapshot unavailable for this earlier run.</p>
          ) : provenance.ballots?.length ? (
            <div
              className="cx-scroll-region"
              role="region"
              aria-label="Authored ballot evidence"
              tabIndex={0}
            >
              <table>
                <thead>
                  <tr>
                    <th>Judge</th>
                    <th>Authored scores</th>
                    <th>Weighted</th>
                    <th>Judge effect</th>
                    <th>Adjusted</th>
                  </tr>
                </thead>
                <tbody>
                  {provenance.ballots.map((ballot) => (
                    <tr key={ballot.ballot}>
                      <td>
                        <code>{ballot.judge}</code>
                      </td>
                      <td>
                        {ballot.responses
                          .map(
                            (response) =>
                              `${response.criterion_name}: ${response.score} (weight ${response.weight})`,
                          )
                          .join(", ")}
                      </td>
                      <td>{ballot.weighted_score.toFixed(2)}</td>
                      <td>{ballot.judge_effect.toFixed(2)}</td>
                      <td>{ballot.adjusted_score.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>No authored ballots were included in this run.</p>
          )}
          <h5>Award evidence</h5>
          {provenance.awards.length ? (
            <ul>
              {provenance.awards.map((award) => (
                <li key={award.award}>
                  {award.name}: selected from rank{" "}
                  {award.rank_at_selection ?? "—"} ·{" "}
                  {award.published ? "published" : "draft"}
                  {award.override_reason &&
                    ` · Override: ${award.override_reason}`}
                </li>
              ))}
            </ul>
          ) : (
            <p>
              No evaluation award selection references this run and project.
            </p>
          )}
        </>
      )}
    </section>
  );
}

function PlanEditor({
  base,
  plan,
  onChange,
}: {
  base: string;
  plan: Plan;
  onChange: (plan: Plan) => void;
}) {
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
      {plan.prize_judging && (
        <p>
          Prize judging · Plan ID: <code>{plan.public_id}</code>. Link this plan
          to one evaluation award before judging begins.
        </p>
      )}
      <label>
        Pool strategy{" "}
        <select
          value={plan.pool_strategy}
          onChange={(e) =>
            void patch({
              pool_strategy: e.target.value as Plan["pool_strategy"],
            })
          }
        >
          <option value="all_judges">All judges score every candidate</option>
          <option value="assigned_subset">
            Judges score an assigned subset
          </option>
        </select>
      </label>
      <label>
        <input
          type="checkbox"
          checked={plan.results_visible_to_participants}
          onChange={(e) =>
            void patch({ results_visible_to_participants: e.target.checked })
          }
        />{" "}
        Results visible to participants
      </label>
      <label>
        <input
          type="checkbox"
          checked={plan.feedback_visible_to_participants}
          onChange={(e) =>
            void patch({ feedback_visible_to_participants: e.target.checked })
          }
        />{" "}
        Judge feedback visible to participants
      </label>
      <label>
        <input
          type="checkbox"
          checked={plan.feedback_anonymous}
          onChange={(e) => void patch({ feedback_anonymous: e.target.checked })}
        />{" "}
        Keep judge identity anonymous in released feedback
      </label>
      <CriteriaEditor criteria={criteria} onChange={setCriteria} />
      <Button onClick={() => void patch({ draft_criteria: criteria })}>
        Save criteria
      </Button>
      <Button variant="secondary" onClick={() => void publish()}>
        Publish rubric
      </Button>
      <ProgressPanel planUrl={planUrl} />
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
  const [pools, setPools] = useState<Pool[]>([]);
  const [stageId, setStageId] = useState("");
  const [plans, setPlans] = useState<Plan[]>([]);
  const [name, setName] = useState("");
  const [poolName, setPoolName] = useState("");
  const [selectedPool, setSelectedPool] = useState("");
  const [prizeJudging, setPrizeJudging] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      request<Stage[]>(eventBase + "stages/"),
      request<Pool[]>(eventBase + "evaluation-pools/"),
    ])
      .then(([nextStages, nextPools]) => {
        setStages(nextStages);
        setPools(nextPools);
      })
      .catch((cause: unknown) => setError(message(cause)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workspaceId, eventId]);

  const plansBase = stageId
    ? `${eventBase}stages/${stageId}/evaluation-plans/`
    : "";

  useEffect(() => {
    if (!plansBase) return;
    request<Plan[]>(plansBase)
      .then(setPlans)
      .catch((cause: unknown) => setError(message(cause)));
  }, [plansBase]);

  async function createPool() {
    setError("");
    try {
      const pool = await request<Pool>(
        eventBase + "evaluation-pools/",
        "POST",
        {
          name: poolName.trim(),
        },
      );
      setPools((items) => [...items, pool]);
      setSelectedPool(pool.public_id);
      setPoolName("");
    } catch (cause) {
      setError(message(cause));
    }
  }

  async function createPlan() {
    setError("");
    try {
      const plan = await request<Plan>(plansBase, "POST", {
        name,
        pool: selectedPool || null,
        prize_judging: prizeJudging,
        draft_criteria: [newCriterion(1)],
      });
      setPlans((items) => [...items, plan]);
      setName("");
      setPrizeJudging(false);
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
          <h3>Judge pool</h3>
          <label>
            Pool{" "}
            <select
              value={selectedPool}
              onChange={(event) => setSelectedPool(event.target.value)}
            >
              <option value="">No pool</option>
              {pools.map((pool) => (
                <option key={pool.public_id} value={pool.public_id}>
                  {pool.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            New pool name{" "}
            <input
              value={poolName}
              onChange={(event) => setPoolName(event.target.value)}
            />
          </label>
          <Button disabled={!poolName.trim()} onClick={() => void createPool()}>
            Create pool
          </Button>
          {selectedPool && (
            <JudgeDirectoryPanel
              workspaceId={workspaceId}
              eventId={eventId}
              poolId={selectedPool}
            />
          )}
          {plans.map((plan) => (
            <PlanEditor
              key={plan.public_id}
              base={plansBase}
              plan={plan}
              onChange={(updated) =>
                setPlans((items) =>
                  items.map((item) =>
                    item.public_id === updated.public_id ? updated : item,
                  ),
                )
              }
            />
          ))}
          <label>
            New plan name{" "}
            <input value={name} onChange={(e) => setName(e.target.value)} />
          </label>
          <label>
            <input
              type="checkbox"
              checked={prizeJudging}
              onChange={(event) => setPrizeJudging(event.target.checked)}
            />{" "}
            Prize judging plan
          </label>
          <Button
            disabled={!name.trim() || (prizeJudging && !selectedPool)}
            onClick={() => void createPlan()}
          >
            Create evaluation plan
          </Button>
        </>
      )}
    </Card>
  );
}
