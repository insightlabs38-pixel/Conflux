import { useEffect, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { api, eventBase, messageOf, useLoad } from "./http";

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

function EvidencePanel({
  planBase,
  selectable,
  winners,
  onToggle,
}: {
  planBase: string;
  selectable: boolean;
  winners: string[];
  onToggle: (project: string, chosen: boolean) => void;
}) {
  const results = useLoad<Result[]>(`${planBase}results/`);
  const agreement = useLoad<Agreement>(`${planBase}agreement/`);
  const closeCalls = useLoad<CloseCalls>(`${planBase}close-calls/`);
  const progress = useLoad<Progress>(`${planBase}progress/`);
  const close = new Set(closeCalls.data?.projects ?? []);
  const spread = new Map<string, number>();
  for (const row of agreement.data?.criteria ?? [])
    spread.set(
      row.project,
      Math.max(spread.get(row.project) ?? 0, row.range ?? 0),
    );

  return (
    <Card title="Evidence" as="h4">
      {progress.data && (
        <p>
          Coverage: {progress.data.submitted_ballots} of{" "}
          {progress.data.expected_ballots ?? "?"} expected ballots from{" "}
          {progress.data.pool_judge_count} judges across{" "}
          {progress.data.candidate_count} candidates. Conflicts excluded:{" "}
          {progress.data.conflict_count}.
        </p>
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
          <table>
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
                <th scope="col">Flags</th>
                {selectable && <th scope="col">Winner</th>}
              </tr>
            </thead>
            <tbody>
              {results.data.map((row) => (
                <tr key={`${row.rank}-${row.project}`}>
                  <td>{row.rank}</td>
                  <th scope="row">{row.project_name ?? row.project}</th>
                  <td>{fixed(row.raw_score)}</td>
                  <td>{fixed(row.final_score)}</td>
                  <td>{row.project ? fixed(spread.get(row.project)) : "–"}</td>
                  <td>
                    {row.project && close.has(row.project) && (
                      <Badge tone="warning">Close call</Badge>
                    )}
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
              ))}
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
  for (const row of data?.tally ?? [])
    evaluated.set(row.project, row.project_name);

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
      {problem && <p role="alert">{problem}</p>}
      {award && planBase && (
        <EvidencePanel
          planBase={planBase}
          selectable={data?.status === "open" || data?.status === "closed"}
          winners={winners}
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
            <ul aria-label="Stances">
              {data.stances.map((stance) => (
                <li key={`${stance.project}-${stance.judge}`}>
                  {evaluated.get(stance.project) ?? stance.project} ·{" "}
                  {stance.judge}: {stance.stance}
                  {stance.rationale && ` — ${stance.rationale}`}
                </li>
              ))}
            </ul>
          )}
          {data.notes.length > 0 && (
            <ul aria-label="Discussion notes">
              {data.notes.map((item) => (
                <li key={item.public_id}>
                  <strong>{item.author}</strong>: {item.body}
                </li>
              ))}
            </ul>
          )}
          {data.status === "finalized" && (
            <p role="status">
              Finalized
              {data.finalization.override_reason
                ? ` (override: ${data.finalization.override_reason})`
                : ""}
              .
            </p>
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
