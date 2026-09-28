import { useEffect, useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { api, eventBase, messageOf, useLoad } from "./http";

type Stop = {
  project: string;
  project_name: string;
  location_name: string;
  room: string | null;
};
type Route = {
  stops: Stop[];
  total_distance: number;
  baseline_distance: number;
  unplaced: (string | { project_name?: string; name?: string })[];
  already_evaluated: number;
};
type JudgeRoute = Route & { judge: string; username: string };
type Routes = {
  judges: JudgeRoute[];
  total_distance: number;
  baseline_distance: number;
};
type Assignment = {
  project: string;
  name: string;
  status: "pending" | "accepted" | "declined";
  reason: string;
};
type ResponseSummary = {
  counts: { pending: number; accepted: number; declined: number };
  declined: { judge: string; name: string; reason: string }[];
};
type Named = { public_id: string; name: string };

const unplacedLabel = (item: Route["unplaced"][number]) =>
  typeof item === "string" ? item : (item.project_name ?? item.name ?? "?");

function saving(route: {
  total_distance: number;
  baseline_distance: number;
}): string {
  if (route.baseline_distance <= 0) return "";
  const saved = 1 - route.total_distance / route.baseline_distance;
  return saved > 0.005
    ? ` (${Math.round(saved * 100)}% shorter than list order)`
    : "";
}

function StopList({ route }: { route: Route }) {
  if (route.stops.length === 0)
    return (
      <p>
        No stops remain
        {route.already_evaluated > 0
          ? ` — you have already scored ${route.already_evaluated} project${route.already_evaluated === 1 ? "" : "s"}`
          : ""}
        .
      </p>
    );
  return (
    <ol>
      {route.stops.map((stop) => (
        <li key={stop.project}>
          {stop.project_name} — {stop.room ? `${stop.room} / ` : ""}
          {stop.location_name}
        </li>
      ))}
    </ol>
  );
}

/** Judge: assigned projects with accept/decline. */
export function JudgeAssignmentsPanel({ planBase }: { planBase: string }) {
  const rows = useLoad<Assignment[]>(`${planBase}my-assignments/`);
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [problem, setProblem] = useState("");

  async function respond(row: Assignment, status: "accepted" | "declined") {
    setProblem("");
    try {
      await api(`${planBase}my-assignments/${row.project}/respond/`, "POST", {
        status,
        reason: reasons[row.project] ?? "",
      });
      rows.reload();
    } catch (cause) {
      setProblem(messageOf(cause));
    }
  }

  return (
    <section aria-label="Your assignments">
      <h3>Your assignments</h3>
      {rows.loading && <LoadingState label="Loading assignments…" />}
      {rows.error && (
        <ErrorState message={rows.error.message} onRetry={rows.reload} />
      )}
      {problem && <p role="alert">{problem}</p>}
      {rows.data && rows.data.length === 0 && (
        <EmptyState title="No projects are assigned to you for this plan." />
      )}
      {rows.data && rows.data.length > 0 && (
        <ul>
          {rows.data.map((row) => (
            <li key={row.project}>
              {row.name}{" "}
              <Badge
                tone={
                  row.status === "accepted"
                    ? "success"
                    : row.status === "declined"
                      ? "danger"
                      : "info"
                }
              >
                {row.status}
              </Badge>
              {row.reason && <> · {row.reason}</>}{" "}
              <label>
                <span className="cx-visually-hidden">
                  Reason for {row.name}
                </span>
                <input
                  placeholder="Reason (optional)"
                  value={reasons[row.project] ?? ""}
                  onChange={(event) =>
                    setReasons((current) => ({
                      ...current,
                      [row.project]: event.target.value,
                    }))
                  }
                />
              </label>{" "}
              <Button
                variant="secondary"
                onClick={() => void respond(row, "accepted")}
                aria-label={`Accept ${row.name}`}
              >
                Accept
              </Button>{" "}
              <Button
                variant="danger"
                onClick={() => void respond(row, "declined")}
                aria-label={`Decline ${row.name}`}
              >
                Decline
              </Button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/** Judge: their in-person route through the projects still to score. */
export function JudgeRoutePanel({ planBase }: { planBase: string }) {
  const route = useLoad<Route>(`${planBase}my-route/?remaining_only=true`);
  return (
    <section aria-label="Your judging route">
      <h3>Your judging route</h3>
      {route.loading && <LoadingState label="Loading your route…" />}
      {route.error && (
        <ErrorState message={route.error.message} onRetry={route.reload} />
      )}
      {route.data && (
        <>
          <StopList route={route.data} />
          {route.data.stops.length > 1 && (
            <p>
              Walking order minimizes distance
              {saving(route.data)}.
            </p>
          )}
          {route.data.unplaced.length > 0 && (
            <p role="status">
              Not on the route yet (no table assigned):{" "}
              {route.data.unplaced.map(unplacedLabel).join(", ")}.
            </p>
          )}
        </>
      )}
    </section>
  );
}

function usePlanPicker(base: string) {
  const stages = useLoad<Named[]>(`${base}stages/`);
  const [stageId, setStageId] = useState("");
  const plans = useLoad<Named[]>(
    stageId ? `${base}stages/${stageId}/evaluation-plans/` : null,
  );
  const [planId, setPlanId] = useState("");
  useEffect(() => {
    setPlanId(plans.data?.length === 1 ? plans.data[0].public_id : "");
  }, [plans.data]);
  return { stages, stageId, setStageId, plans, planId, setPlanId };
}

/** Organizer: route feasibility per judge and assignment-response state. */
export function OrganizerJudgingLogisticsPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = eventBase(workspaceId, eventId);
  const picker = usePlanPicker(base);
  const planBase = picker.planId
    ? `${base}stages/${picker.stageId}/evaluation-plans/${picker.planId}/`
    : null;
  const routes = useLoad<Routes>(planBase ? `${planBase}routes/` : null);
  const responses = useLoad<ResponseSummary>(
    planBase ? `${planBase}assignment-responses/` : null,
  );

  return (
    <section aria-label="Judging logistics">
      <h3>Judging logistics</h3>
      {picker.stages.data && picker.stages.data.length === 0 && (
        <EmptyState title="This event has no stages yet." />
      )}
      {picker.stages.data && picker.stages.data.length > 0 && (
        <label>
          Stage{" "}
          <select
            value={picker.stageId}
            onChange={(event) => picker.setStageId(event.target.value)}
          >
            <option value="">Choose a stage</option>
            {picker.stages.data.map((stage) => (
              <option key={stage.public_id} value={stage.public_id}>
                {stage.name}
              </option>
            ))}
          </select>
        </label>
      )}
      {picker.plans.data && picker.plans.data.length > 1 && (
        <label>
          Plan{" "}
          <select
            value={picker.planId}
            onChange={(event) => picker.setPlanId(event.target.value)}
          >
            <option value="">Choose a plan</option>
            {picker.plans.data.map((plan) => (
              <option key={plan.public_id} value={plan.public_id}>
                {plan.name}
              </option>
            ))}
          </select>
        </label>
      )}
      {responses.data && (
        <p>
          Assignment responses: {responses.data.counts.accepted} accepted,{" "}
          {responses.data.counts.pending} pending,{" "}
          {responses.data.counts.declined} declined.
        </p>
      )}
      {responses.data && responses.data.declined.length > 0 && (
        <ul aria-label="Declined assignments">
          {responses.data.declined.map((item) => (
            <li key={`${item.judge}-${item.name}`}>
              {item.judge} declined {item.name}
              {item.reason ? `: ${item.reason}` : ""}
            </li>
          ))}
        </ul>
      )}
      {routes.loading && <LoadingState label="Loading routes…" />}
      {routes.error && (
        <ErrorState message={routes.error.message} onRetry={routes.reload} />
      )}
      {routes.data && routes.data.judges.length === 0 && (
        <EmptyState title="No judges have routes for this plan." />
      )}
      {routes.data && routes.data.judges.length > 0 && (
        <div
          className="cx-scroll-region"
          role="region"
          aria-label="Judge routes table"
          tabIndex={0}
        >
          <table>
            <caption>
              Route feasibility — total {routes.data.total_distance.toFixed(1)}{" "}
              vs {routes.data.baseline_distance.toFixed(1)} in list order
            </caption>
            <thead>
              <tr>
                <th scope="col">Judge</th>
                <th scope="col">Stops left</th>
                <th scope="col">Already scored</th>
                <th scope="col">Unplaced projects</th>
                <th scope="col">Distance</th>
              </tr>
            </thead>
            <tbody>
              {routes.data.judges.map((judge) => (
                <tr key={judge.judge}>
                  <th scope="row">{judge.username}</th>
                  <td>{judge.stops.length}</td>
                  <td>{judge.already_evaluated}</td>
                  <td>
                    {judge.unplaced.length > 0 ? (
                      <Badge tone="warning">{judge.unplaced.length}</Badge>
                    ) : (
                      0
                    )}
                  </td>
                  <td>
                    {judge.total_distance.toFixed(1)}
                    {saving(judge)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

type Inspection = {
  verdict: string;
  detected_type: string;
  findings: { severity: string; code: string; detail: string }[];
  facts: Record<string, unknown>;
  preview: string;
  inspected_at: string;
};
type ReviewArtifact = {
  public_id: string;
  kind: string;
  visibility: string;
  title: string;
  external_url: string;
  status: string;
  byte_size: number | null;
  inspection: Inspection | null;
  download_url: string | null;
};

const VERDICT_TONE: Record<string, "success" | "warning" | "danger"> = {
  clean: "success",
  warnings: "warning",
  blocked: "danger",
};
const isWebUrl = (url: string) => /^https?:\/\//i.test(url);

/** Judge/organizer: the safe, static artifact inspector for one project. */
export function ArtifactInspector({
  workspaceId,
  eventId,
  projectId,
}: {
  workspaceId: string;
  eventId: string;
  projectId: string;
}) {
  const base = `${eventBase(workspaceId, eventId)}projects/${projectId}/review-artifacts/`;
  const artifacts = useLoad<ReviewArtifact[]>(base);
  const [problem, setProblem] = useState("");
  const [running, setRunning] = useState("");

  async function inspect(id: string) {
    setProblem("");
    setRunning(id);
    try {
      await api(`${base}${id}/inspection/`, "POST");
      artifacts.reload();
    } catch (cause) {
      setProblem(messageOf(cause));
    } finally {
      setRunning("");
    }
  }

  return (
    <section aria-label="Submitted artifacts">
      <Card title="Submitted artifacts" as="h4">
        {artifacts.loading && <LoadingState label="Loading artifacts…" />}
        {artifacts.error && artifacts.error.status !== 404 && (
          <ErrorState
            message={artifacts.error.message}
            onRetry={artifacts.reload}
          />
        )}
        {artifacts.error?.status === 404 && (
          <p>You do not have access to this project's artifacts.</p>
        )}
        {problem && <p role="alert">{problem}</p>}
        {artifacts.data && artifacts.data.length === 0 && (
          <p>No artifacts have been shared with reviewers.</p>
        )}
        {artifacts.data?.map((artifact) => (
          <div key={artifact.public_id}>
            <h5>
              {artifact.title} <Badge>{artifact.kind}</Badge>{" "}
              {artifact.inspection && (
                <Badge
                  tone={VERDICT_TONE[artifact.inspection.verdict] ?? "info"}
                >
                  {artifact.inspection.verdict}
                </Badge>
              )}
            </h5>
            {artifact.external_url && isWebUrl(artifact.external_url) && (
              <p>
                <a
                  href={artifact.external_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Open {artifact.external_url}
                </a>
              </p>
            )}
            {artifact.download_url && (
              <p>
                <a href={artifact.download_url} rel="noopener noreferrer">
                  Download file
                </a>{" "}
                (inspected as untrusted content — open with care)
              </p>
            )}
            {artifact.inspection ? (
              <>
                <p>
                  Detected type:{" "}
                  {artifact.inspection.detected_type || "unknown"}
                </p>
                {artifact.inspection.findings.length > 0 && (
                  <ul aria-label={`Findings for ${artifact.title}`}>
                    {artifact.inspection.findings.map((finding, index) => (
                      <li key={`${finding.code}-${index}`}>
                        <Badge
                          tone={
                            finding.severity === "blocked"
                              ? "danger"
                              : finding.severity === "warning"
                                ? "warning"
                                : "neutral"
                          }
                        >
                          {finding.severity}
                        </Badge>{" "}
                        {finding.detail || finding.code}
                      </li>
                    ))}
                  </ul>
                )}
                {Object.keys(artifact.inspection.facts).length > 0 && (
                  <dl>
                    {Object.entries(artifact.inspection.facts).map(
                      ([key, value]) => (
                        <div key={key}>
                          <dt>{key}</dt>
                          <dd>
                            {typeof value === "string" ||
                            typeof value === "number"
                              ? String(value)
                              : JSON.stringify(value)}
                          </dd>
                        </div>
                      ),
                    )}
                  </dl>
                )}
                {artifact.inspection.preview && (
                  <pre
                    className="cx-scroll-region"
                    aria-label={`Preview of ${artifact.title}`}
                    tabIndex={0}
                  >
                    {artifact.inspection.preview}
                  </pre>
                )}
              </>
            ) : (
              <p>Not inspected yet.</p>
            )}
            <Button
              variant="secondary"
              disabled={running === artifact.public_id}
              onClick={() => void inspect(artifact.public_id)}
            >
              {artifact.inspection ? "Re-run inspection" : "Inspect safely"}
            </Button>
          </div>
        ))}
      </Card>
    </section>
  );
}
