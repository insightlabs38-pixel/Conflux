import { useEffect, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { api, eventBase, messageOf, useLoad, type Loaded } from "./http";

type Award = {
  public_id: string;
  name: string;
  evaluation_plan: string | null;
  winner_count: number;
  published_at: string | null;
  winners: { project: string }[];
};
type Tally = {
  project: string;
  project_name: string;
  endorse: number;
  object: number;
  abstain: number;
  recommended: boolean;
};
type Room = {
  public_id: string;
  status: "open" | "closed" | "finalized";
  quorum: number;
  notes: {
    public_id: string;
    project: string | null;
    author: string;
    body: string;
    created_at: string;
  }[];
  stances: {
    project: string;
    judge: string;
    stance: string;
    rationale: string;
  }[];
  tally: Tally[];
  finalization: { winners?: string[]; override_reason?: string };
};
type Stage = { public_id: string };
type Plan = { public_id: string };
type Result = {
  rank: number;
  project: string | null;
  project_name: string | null;
  raw_score: number | null;
  final_score: number;
};
type Agreement = {
  criteria: {
    project: string;
    project_name: string;
    criterion_id: string;
    mean: number;
    range: number;
    stdev: number;
  }[];
};
type CloseCalls = { projects: string[] };
type Progress = {
  candidate_count: number;
  pool_judge_count: number;
  conflict_count: number;
  expected_ballots: number | null;
  submitted_ballots: number;
  completion_ratio: number | null;
};

const fixed = (value: number | null | undefined) =>
  value === null || value === undefined ? "–" : value.toFixed(2);

/** Locate the stage that owns `planId` (plan URLs are stage-scoped). */
function usePlanBase(base: string, planId: string | null) {
  const [path, setPath] = useState<string | null>(null);
  useEffect(() => {
    setPath(null);
    if (!planId) return;
    let active = true;
    (async () => {
      const stages = await api<Stage[]>(`${base}stages/`);
      for (const stage of stages) {
        const plans = await api<Plan[]>(
          `${base}stages/${stage.public_id}/evaluation-plans/`,
        );
        if (plans.some((plan) => plan.public_id === planId)) {
          if (active)
            setPath(
              `${base}stages/${stage.public_id}/evaluation-plans/${planId}/`,
            );
          return;
        }
      }
    })().catch(() => undefined);
    return () => {
      active = false;
    };
  }, [base, planId]);
  return path;
}

const STEPS = [
  "Evidence",
  "Panel discussion",
  "Discussion closed",
  "Decision final",
];

function DecisionSteps({ status }: { status: Room["status"] | null }) {
  const current =
    status === null ? 0 : { open: 1, closed: 2, finalized: 3 }[status];
  return (
    <ol className="cx-steps" aria-label="Deliberation progress">
      {STEPS.map((label, index) => (
        <li
          key={label}
          aria-current={index === current ? "step" : undefined}
          data-state={
            index < current ? "done" : index === current ? "current" : "todo"
          }
        >
          <span className="cx-steps__mark" aria-hidden="true">
            {index < current ? "✓" : index + 1}
          </span>
          {label}
        </li>
      ))}
    </ol>
  );
}

function EvidencePanel({
  planBase,
  results,
  selectable,
  winners,
  tally,
  otherAwards,
  onToggle,
}: {
  planBase: string;
  results: Loaded<Result[]>;
  selectable: boolean;
  winners: string[];
  tally: Tally[];
  otherAwards: Map<string, string[]>;
  onToggle: (project: string, chosen: boolean) => void;
}) {
  const agreement = useLoad<Agreement>(`${planBase}agreement/`);
  const closeCalls = useLoad<CloseCalls>(`${planBase}close-calls/`);
  const progress = useLoad<Progress>(`${planBase}progress/`);
  const close = new Set(closeCalls.data?.projects ?? []);
  const panel = new Map(tally.map((row) => [row.project, row]));
  const spread = new Map<string, number>();
  for (const row of agreement.data?.criteria ?? [])
    spread.set(
      row.project,
      Math.max(spread.get(row.project) ?? 0, row.range ?? 0),
    );
  const widest = Math.max(1, ...spread.values());

  return (
    <Card title="Evidence" as="h4">
      {progress.data && (
        <dl className="cx-decision-facts">
          <div>
            <dt>Ballots</dt>
            <dd>
              {progress.data.submitted_ballots}
              {progress.data.expected_ballots == null
                ? ""
                : ` of ${progress.data.expected_ballots}`}
            </dd>
          </div>
          <div>
            <dt>Judges</dt>
            <dd>{progress.data.pool_judge_count}</dd>
          </div>
          <div>
            <dt>Candidates</dt>
            <dd>{progress.data.candidate_count}</dd>
          </div>
          <div>
            <dt>Conflicts excluded</dt>
            <dd>
              {progress.data.conflict_count > 0 ? (
                <Badge tone="warning">{progress.data.conflict_count}</Badge>
              ) : (
                0
              )}
            </dd>
          </div>
        </dl>
      )}
      {results.loading && <LoadingState label="Loading results…" />}
      {results.error && (
        <p>
          Published results are not available yet ({results.error.message}).
        </p>
      )}
      {results.data && results.data.length === 0 && (
        <EmptyState title="No ranked results yet." />
      )}
      {results.data && results.data.length > 0 && (
        <div
          className="cx-scroll-region"
          role="region"
          aria-label="Finalist comparison table"
          tabIndex={0}
        >
          <table className="cx-decision-table">
            <caption>
              Finalist comparison (raw mean vs. normalized score)
            </caption>
            <thead>
              <tr>
                <th scope="col">Rank</th>
                <th scope="col">Project</th>
                <th scope="col">Raw</th>
                <th scope="col">Normalized</th>
                <th scope="col">Max judge disagreement</th>
                <th scope="col">Panel</th>
                <th scope="col">Flags</th>
                {selectable && <th scope="col">Winner</th>}
              </tr>
            </thead>
            <tbody>
              {results.data.map((row) => {
                const stance = row.project ? panel.get(row.project) : undefined;
                const other = row.project
                  ? (otherAwards.get(row.project) ?? [])
                  : [];
                const gap = row.project ? spread.get(row.project) : undefined;
                return (
                  <tr
                    key={`${row.rank}-${row.project}`}
                    data-selected={
                      (row.project && winners.includes(row.project)) ||
                      undefined
                    }
                  >
                    <td>{row.rank}</td>
                    <th scope="row">{row.project_name ?? row.project}</th>
                    <td>{fixed(row.raw_score)}</td>
                    <td>{fixed(row.final_score)}</td>
                    <td>
                      {fixed(gap)}
                      {gap !== undefined && (
                        <span
                          className="cx-meter"
                          aria-hidden="true"
                          style={{ width: `${(gap / widest) * 100}%` }}
                        />
                      )}
                    </td>
                    <td>
                      {stance
                        ? `${stance.endorse} endorse · ${stance.object} object · ${stance.abstain} abstain`
                        : "–"}
                    </td>
                    <td>
                      <div className="cx-flags">
                        {row.project && close.has(row.project) && (
                          <Badge tone="warning">Close call</Badge>
                        )}
                        {stance?.recommended && (
                          <Badge tone="success">Recommended</Badge>
                        )}
                        {stance && !stance.recommended && (
                          <Badge>Not recommended</Badge>
                        )}
                        {other.map((name) => (
                          <Badge key={name} tone="warning">
                            Also wins {name}
                          </Badge>
                        ))}
                      </div>
                    </td>
                    {selectable && (
                      <td>
                        {row.project && (
                          <input
                            type="checkbox"
                            aria-label={`Select ${row.project_name ?? row.project} as winner`}
                            checked={winners.includes(row.project)}
                            onChange={(event) =>
                              onToggle(
                                row.project as string,
                                event.target.checked,
                              )
                            }
                          />
                        )}
                      </td>
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}

/** Organizer view of an award's deliberation room, supporting evidence and finalization.
 * Panelist stances/notes are judge-facing API calls (docs/operations/PVS.md). */
export function DeliberationPanel({
  workspaceId,
  eventId,
  onFinalized,
}: {
  workspaceId: string;
  eventId: string;
  onFinalized?: () => void;
}) {
  const base = eventBase(workspaceId, eventId);
  const awards = useLoad<Award[]>(`${base}awards/`);
  const [awardId, setAwardId] = useState("");
  const award = awards.data?.find((item) => item.public_id === awardId);
  const roomUrl = awardId ? `${base}awards/${awardId}/deliberation/` : null;
  const room = useLoad<Room>(roomUrl);
  const planBase = usePlanBase(base, award?.evaluation_plan ?? null);
  const results = useLoad<Result[]>(planBase ? `${planBase}results/` : null);
  const [quorum, setQuorum] = useState("2");
  const [problem, setProblem] = useState("");
  const [winners, setWinners] = useState<string[]>([]);
  const [reason, setReason] = useState("");

  async function act(
    path: string,
    method: string,
    body?: object,
    after?: () => void,
  ) {
    setProblem("");
    try {
      await api(`${roomUrl}${path}`, method, body);
      after?.();
      room.reload();
      awards.reload();
    } catch (cause) {
      setProblem(messageOf(cause));
    }
  }

  const data = room.data;
  const evaluated = new Map<string, string>();
  for (const row of results.data ?? [])
    if (row.project)
      evaluated.set(row.project, row.project_name ?? row.project);
  for (const row of data?.tally ?? [])
    evaluated.set(row.project, row.project_name);
  const otherAwards = new Map<string, string[]>();
  for (const other of awards.data ?? [])
    if (other.public_id !== awardId)
      for (const winner of other.winners)
        otherAwards.set(winner.project, [
          ...(otherAwards.get(winner.project) ?? []),
          other.name,
        ]);
  const recommended = new Set(
    (data?.tally ?? []).filter((r) => r.recommended).map((r) => r.project),
  );
  const needsReason = winners.some((project) => !recommended.has(project));
  const wanted = award?.winner_count ?? 0;
  const finalNames = (data?.finalization.winners ?? []).map(
    (project) => evaluated.get(project) ?? project,
  );

  return (
    <section aria-label="Deliberation and finalization">
      <h3>Deliberation and finalization</h3>
      <>
        {awards.loading && <LoadingState label="Loading awards…" />}
        {awards.error && (
          <ErrorState message={awards.error.message} onRetry={awards.reload} />
        )}
        {awards.data && awards.data.length === 0 && (
          <EmptyState title="No awards are configured for this event." />
        )}
        {awards.data && awards.data.length > 0 && (
          <label>
            Award{" "}
            <select
              value={awardId}
              onChange={(event) => {
                setAwardId(event.target.value);
                setWinners([]);
                setProblem("");
              }}
            >
              <option value="">Choose an award</option>
              {awards.data.map((item) => (
                <option key={item.public_id} value={item.public_id}>
                  {item.name}
                  {item.winners.length > 0 ? " (decided)" : ""}
                </option>
              ))}
            </select>
          </label>
        )}
      </>
      {award && (
        <>
          <p className="cx-muted">
            {award.name}: {award.winner_count} winner
            {award.winner_count === 1 ? "" : "s"}
            {award.published_at ? " · published" : ""}
          </p>
          <DecisionSteps status={data?.status ?? null} />
        </>
      )}
      {problem && <p role="alert">{problem}</p>}
      {award && planBase && (
        <EvidencePanel
          planBase={planBase}
          results={results}
          selectable={data?.status === "open" || data?.status === "closed"}
          winners={winners}
          tally={data?.tally ?? []}
          otherAwards={otherAwards}
          onToggle={(project, chosen) =>
            setWinners((current) =>
              chosen
                ? [...current, project]
                : current.filter((id) => id !== project),
            )
          }
        />
      )}
      {room.loading && awardId && <LoadingState label="Loading room…" />}
      {room.error && room.error.status === 404 && awardId && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void act("", "POST", { quorum: Number(quorum) });
          }}
        >
          <p>No deliberation room is open for this award.</p>
          <label>
            Quorum (endorsements needed){" "}
            <input
              type="number"
              min={1}
              max={200}
              value={quorum}
              onChange={(event) => setQuorum(event.target.value)}
            />
          </label>{" "}
          <button>Open deliberation room</button>
        </form>
      )}
      {room.error && room.error.status !== 404 && (
        <ErrorState message={room.error.message} onRetry={room.reload} />
      )}
      {data && (
        <Card title="Deliberation room" as="h4">
          <p>
            <Badge
              tone={
                data.status === "open"
                  ? "info"
                  : data.status === "closed"
                    ? "warning"
                    : "success"
              }
            >
              {data.status}
            </Badge>{" "}
            Quorum {data.quorum}
          </p>
          {data.tally.length === 0 ? (
            <p>No stances recorded yet.</p>
          ) : (
            <div
              className="cx-scroll-region"
              role="region"
              aria-label="Panel tally table"
              tabIndex={0}
            >
              <table>
                <caption>Panel tally</caption>
                <thead>
                  <tr>
                    <th scope="col">Project</th>
                    <th scope="col">Endorse</th>
                    <th scope="col">Object</th>
                    <th scope="col">Abstain</th>
                    <th scope="col">Panel</th>
                  </tr>
                </thead>
                <tbody>
                  {data.tally.map((row) => (
                    <tr key={row.project}>
                      <th scope="row">{row.project_name}</th>
                      <td>{row.endorse}</td>
                      <td>{row.object}</td>
                      <td>{row.abstain}</td>
                      <td>
                        {row.recommended ? (
                          <Badge tone="success">Recommended</Badge>
                        ) : (
                          <Badge>Not recommended</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {data.stances.length > 0 && (
            <ul aria-label="Stances" className="cx-evidence-list">
              {data.stances.map((stance) => (
                <li key={`${stance.project}-${stance.judge}`}>
                  <strong>
                    {evaluated.get(stance.project) ?? stance.project}
                  </strong>{" "}
                  · {stance.judge}: <Badge>{stance.stance}</Badge>
                  {stance.rationale && <p>{stance.rationale}</p>}
                </li>
              ))}
            </ul>
          )}
          {data.notes.length > 0 && (
            <ul aria-label="Discussion notes" className="cx-evidence-list">
              {data.notes.map((item) => (
                <li key={item.public_id}>
                  <strong>{item.author}</strong>: {item.body}
                </li>
              ))}
            </ul>
          )}
          {data.status === "finalized" && (
            <div className="cx-final-banner" role="status">
              <p>
                <strong>Finalized</strong> — this decision is immutable
                {data.finalization.override_reason
                  ? ` (override: ${data.finalization.override_reason})`
                  : ""}
                .
              </p>
              {finalNames.length > 0 && <p>Winners: {finalNames.join(", ")}</p>}
            </div>
          )}
          {data.status === "open" && (
            <Button
              variant="secondary"
              onClick={() => void act("close/", "POST")}
            >
              Close discussion
            </Button>
          )}
          {data.status !== "finalized" && (
            <form
              className="cx-decision-form"
              onSubmit={(event) => {
                event.preventDefault();
                void act(
                  "finalize/",
                  "POST",
                  { winners, override_reason: reason },
                  () => {
                    setWinners([]);
                    onFinalized?.();
                  },
                );
              }}
            >
              <h5>Finalize winners</h5>
              <p>
                Select {award?.winner_count ?? "the"} winner
                {award?.winner_count === 1 ? "" : "s"} in the finalist
                comparison table above. Choosing a project the panel did not
                recommend requires a reason.
              </p>
              <p role="status">
                Selected {winners.length}
                {wanted ? ` of ${wanted}` : ""}:{" "}
                {winners.length === 0
                  ? "none yet"
                  : winners
                      .map((project) => evaluated.get(project) ?? project)
                      .join(", ")}
                {winners.length > 0 && !needsReason
                  ? " · all recommended by the panel"
                  : ""}
              </p>
              {needsReason && (
                <p className="cx-warning-text">
                  A selected project was not recommended by the panel — give an
                  override reason.
                </p>
              )}
              <label>
                Override reason{" "}
                <input
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                />
              </label>{" "}
              <button disabled={winners.length === 0}>Finalize</button>
            </form>
          )}
        </Card>
      )}
    </section>
  );
}
