import { useState } from "react";
import { FrozenSubmissionPreview } from "../submissions/FrozenSubmissionPreview";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { api, eventBase, formatWhen, messageOf, useLoad } from "./http";

type Rules = {
  current: { number: number; title: string; body: string } | null;
  acknowledged: boolean;
  versions: { number: number; title: string; published_at: string }[];
};
type Acknowledgements = {
  number: number | null;
  acknowledged: { user: string; acknowledged_at: string }[];
  pending: string[];
};

/** Rules: participants acknowledge; organizers publish versions and see who has. */
export function RulesPanel({
  workspaceId,
  eventId,
  canPublish,
}: {
  workspaceId: string;
  eventId: string;
  canPublish: boolean;
}) {
  const base = eventBase(workspaceId, eventId);
  const rules = useLoad<Rules>(`${base}rules/`);
  const acks = useLoad<Acknowledgements>(
    canPublish ? `${base}rules/acknowledgements/` : null,
  );
  const [problem, setProblem] = useState("");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");

  async function run(action: () => Promise<unknown>) {
    setProblem("");
    try {
      await action();
      rules.reload();
      acks.reload();
    } catch (cause) {
      setProblem(messageOf(cause));
    }
  }

  return (
    <section aria-label="Event rules">
      <h3>Event rules</h3>
      {rules.loading && <LoadingState label="Loading rules…" />}
      {rules.error && (
        <ErrorState message={rules.error.message} onRetry={rules.reload} />
      )}
      {problem && <p role="alert">{problem}</p>}
      {rules.data && !rules.data.current && (
        <EmptyState title="No rules have been published for this event." />
      )}
      {rules.data?.current && (
        <Card
          title={`${rules.data.current.title} (v${rules.data.current.number})`}
          as="h4"
        >
          <p style={{ whiteSpace: "pre-wrap" }}>{rules.data.current.body}</p>
          {!canPublish &&
            (rules.data.acknowledged ? (
              <p role="status">
                <Badge tone="success">Acknowledged</Badge> You have accepted
                this version.
              </p>
            ) : (
              <Button
                onClick={() =>
                  void run(() =>
                    api(`${base}rules/acknowledge/`, "POST", {
                      number: rules.data?.current?.number,
                    }),
                  )
                }
              >
                I have read and accept these rules
              </Button>
            ))}
        </Card>
      )}
      {canPublish && acks.data && acks.data.number !== null && (
        <p>
          Version {acks.data.number}: {acks.data.acknowledged.length}{" "}
          acknowledged, {acks.data.pending.length} pending
          {acks.data.pending.length > 0 && ` (${acks.data.pending.join(", ")})`}
          .
        </p>
      )}
      {canPublish && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void run(async () => {
              await api(`${base}rules/`, "POST", { title, body });
              setTitle("");
              setBody("");
            });
          }}
        >
          <h4>Publish a new version</h4>
          <label>
            Title{" "}
            <input
              required
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
          </label>{" "}
          <label>
            Rules text{" "}
            <textarea
              required
              value={body}
              onChange={(event) => setBody(event.target.value)}
            />
          </label>{" "}
          <button>Publish rules</button>
          <p>
            Participants must acknowledge the new version; earlier
            acknowledgements do not carry over.
          </p>
        </form>
      )}
    </section>
  );
}

type PublicationRequest = {
  public_id: string;
  plan: string;
  normalization_run_number: number;
  normalization_run: string;
  status: string;
  reason: string;
  requested_by: string;
  decided_by: string | null;
  decision_note: string;
  created_at: string;
};
type Correction = {
  public_id: string;
  plan: string;
  previous_run: number | null;
  run: number;
  reason: string;
  corrected_at: string;
};
type Named = { public_id: string; name: string };
type Run = { public_id: string; number: number };
const DECISION_MESSAGE = {
  approve: "Request approved.",
  reject: "Request rejected.",
  cancel: "Request cancelled.",
};
const STATUS_TONE: Record<string, "info" | "success" | "danger" | "neutral"> = {
  pending: "info",
  approved: "success",
  rejected: "danger",
  cancelled: "neutral",
};

/** Organizer: publication approval queue, correction history and exceptions. */
export function PublicationGovernancePanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = eventBase(workspaceId, eventId);
  const settings = useLoad<{ require_publication_approval: boolean }>(
    `${base}governance/settings/`,
  );
  const requests = useLoad<PublicationRequest[]>(
    `${base}result-publication-requests/`,
  );
  const corrections = useLoad<Correction[]>(`${base}result-corrections/`);
  const stages = useLoad<Named[]>(`${base}stages/`);
  const [stageId, setStageId] = useState("");
  const plans = useLoad<Named[]>(
    stageId ? `${base}stages/${stageId}/evaluation-plans/` : null,
  );
  const [planId, setPlanId] = useState("");
  const planBase = planId
    ? `${base}stages/${stageId}/evaluation-plans/${planId}/`
    : null;
  const runs = useLoad<Run[]>(
    planBase ? `${planBase}normalization-runs/` : null,
  );
  const [runId, setRunId] = useState("");
  const [reason, setReason] = useState("");
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [problem, setProblem] = useState("");
  const [status, setStatus] = useState("");
  const approval = settings.data?.require_publication_approval ?? false;
  const awards = useLoad<{ published_at: string | null }[]>(`${base}awards/`);
  const published =
    Array.isArray(awards.data) && awards.data.some((a) => a.published_at);
  const requestList = Array.isArray(requests.data) ? requests.data : [];
  const correctionList = Array.isArray(corrections.data)
    ? corrections.data
    : [];
  const calculated =
    (Array.isArray(runs.data) && runs.data.length > 0) ||
    requestList.length > 0 ||
    published;
  const approved =
    published || requestList.some((r) => r.status === "approved");
  const steps = [
    { label: "Results calculated", done: calculated },
    ...(approval ? [{ label: "Approval", done: approved }] : []),
    { label: "Published", done: published },
  ];
  const currentStep = steps.findIndex((step) => !step.done);

  async function run(action: () => Promise<unknown>, message = "") {
    setProblem("");
    setStatus("");
    try {
      await action();
      if (message) setStatus(message);
      requests.reload();
      corrections.reload();
      settings.reload();
    } catch (cause) {
      setProblem(messageOf(cause));
    }
  }

  return (
    <section aria-label="Publication approval and corrections">
      <h3>Publication approval and corrections</h3>
      <ol className="cx-steps" aria-label="Publication pipeline">
        {steps.map((step, index) => (
          <li
            key={step.label}
            aria-current={index === currentStep ? "step" : undefined}
            data-state={
              step.done ? "done" : index === currentStep ? "current" : "todo"
            }
          >
            <span className="cx-steps__mark" aria-hidden="true">
              {step.done ? "✓" : index + 1}
            </span>
            {step.label}
          </li>
        ))}
      </ol>
      <p className="cx-muted">
        Result version {correctionList.length + 1}
        {correctionList.length > 0
          ? ` · corrected ${correctionList.length} time${correctionList.length === 1 ? "" : "s"}`
          : published
            ? " · original publication"
            : " · not yet published"}
        .
      </p>
      {problem && <p role="alert">{problem}</p>}
      {status && <p role="status">{status}</p>}
      {settings.data && (
        <label>
          <input
            type="checkbox"
            checked={approval}
            onChange={(event) =>
              void run(
                () =>
                  api(`${base}governance/settings/`, "PUT", {
                    require_publication_approval: event.target.checked,
                  }),
                "Setting saved.",
              )
            }
          />{" "}
          Require a second organizer to approve result publication
        </label>
      )}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          if (!planBase) return;
          void run(
            () =>
              approval
                ? api(`${base}result-publication-requests/`, "POST", {
                    plan: planId,
                    normalization_run: runId,
                    reason,
                  })
                : api(`${planBase}publish-results/`, "POST", {
                    normalization_run: runId,
                    reason,
                  }),
            approval
              ? "Publication requested; another organizer must approve it."
              : "Results published.",
          );
        }}
      >
        <h4>
          {approval ? "Request publication" : "Publish or correct results"}
        </h4>
        <label>
          Stage{" "}
          <select
            value={stageId}
            onChange={(event) => {
              setStageId(event.target.value);
              setPlanId("");
              setRunId("");
            }}
          >
            <option value="">Choose a stage</option>
            {stages.data?.map((stage) => (
              <option key={stage.public_id} value={stage.public_id}>
                {stage.name}
              </option>
            ))}
          </select>
        </label>{" "}
        <label>
          Plan{" "}
          <select
            value={planId}
            onChange={(event) => {
              setPlanId(event.target.value);
              setRunId("");
            }}
          >
            <option value="">Choose a plan</option>
            {plans.data?.map((plan) => (
              <option key={plan.public_id} value={plan.public_id}>
                {plan.name}
              </option>
            ))}
          </select>
        </label>{" "}
        <label>
          Normalization run{" "}
          <select
            required
            value={runId}
            onChange={(event) => setRunId(event.target.value)}
          >
            <option value="">Choose a run</option>
            {runs.data?.map((item) => (
              <option key={item.public_id} value={item.public_id}>
                Run {item.number}
              </option>
            ))}
          </select>
        </label>{" "}
        <label>
          Reason (shown in the correction notice){" "}
          <input
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        </label>{" "}
        <button disabled={!planBase || !runId}>
          {approval ? "Request approval" : "Publish"}
        </button>
      </form>
      <h4>Approval requests</h4>
      {requests.data && requests.data.length === 0 && (
        <p>No publication requests.</p>
      )}
      {requests.data && requests.data.length > 0 && (
        <ul>
          {requests.data.map((item) => (
            <li key={item.public_id}>
              Run {item.normalization_run_number} requested by{" "}
              {item.requested_by}{" "}
              <Badge tone={STATUS_TONE[item.status] ?? "neutral"}>
                {item.status}
              </Badge>
              {item.reason && <> · {item.reason}</>}
              {item.decision_note && <> · {item.decision_note}</>}
              {item.status === "pending" && (
                <>
                  {" "}
                  <label>
                    <span className="cx-visually-hidden">Decision note</span>
                    <input
                      placeholder="Note"
                      value={notes[item.public_id] ?? ""}
                      onChange={(event) =>
                        setNotes((current) => ({
                          ...current,
                          [item.public_id]: event.target.value,
                        }))
                      }
                    />
                  </label>{" "}
                  {(["approve", "reject", "cancel"] as const).map((action) => (
                    <Button
                      key={action}
                      variant={action === "approve" ? "primary" : "secondary"}
                      onClick={() =>
                        void run(
                          () =>
                            api(
                              `${base}result-publication-requests/${item.public_id}/${action}/`,
                              "POST",
                              { note: notes[item.public_id] ?? "" },
                            ),
                          DECISION_MESSAGE[action],
                        )
                      }
                    >
                      {action[0].toUpperCase() + action.slice(1)}
                    </Button>
                  ))}
                </>
              )}
            </li>
          ))}
        </ul>
      )}
      <h4>Correction history</h4>
      {corrections.data && corrections.data.length === 0 && (
        <p>Results have not been corrected.</p>
      )}
      {corrections.data && corrections.data.length > 0 && (
        <ul aria-label="Correction history">
          {corrections.data.map((item) => (
            <li key={item.public_id}>
              {formatWhen(item.corrected_at)} · {item.plan}: run{" "}
              {item.previous_run ?? "–"} → run {item.run}
              {item.reason && ` — ${item.reason}`}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

type ExceptionRequest = {
  public_id: string;
  project: string;
  action: string;
  reason: string;
  status: string;
  requested_by: string;
  decision_note: string;
  grant_expires_at: string | null;
  created_at: string;
};

/** Organizer: queue of deadline-exception requests. */
export function ExceptionRequestsPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = eventBase(workspaceId, eventId);
  const requests = useLoad<ExceptionRequest[]>(`${base}exception-requests/`);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [expiry, setExpiry] = useState<Record<string, string>>({});
  // Approving grants a time-boxed exception; default it to a day from now.
  const defaultExpiry = () => {
    const at = new Date(Date.now() + 24 * 3600 * 1000);
    return new Date(at.getTime() - at.getTimezoneOffset() * 60000)
      .toISOString()
      .slice(0, 16);
  };
  const [problem, setProblem] = useState("");

  async function decide(item: ExceptionRequest, action: "approve" | "reject") {
    setProblem("");
    try {
      await api(
        `${base}exception-requests/${item.public_id}/${action}/`,
        "POST",
        {
          note: notes[item.public_id] ?? "",
          ...(action === "approve"
            ? {
                expires_at: new Date(
                  expiry[item.public_id] ?? defaultExpiry(),
                ).toISOString(),
              }
            : {}),
        },
      );
      requests.reload();
    } catch (cause) {
      setProblem(messageOf(cause));
    }
  }

  return (
    <section aria-label="Deadline exception requests">
      <h3>Deadline exception requests</h3>
      {requests.loading && <LoadingState label="Loading requests…" />}
      {requests.error && (
        <ErrorState
          message={requests.error.message}
          onRetry={requests.reload}
        />
      )}
      {problem && <p role="alert">{problem}</p>}
      {requests.data && requests.data.length === 0 && (
        <p>No exception requests.</p>
      )}
      {requests.data?.map((item) => (
        <Card
          key={item.public_id}
          title={`${item.requested_by}: ${item.action}`}
          as="h4"
        >
          <p>
            <Badge
              tone={
                item.status === "approved"
                  ? "success"
                  : item.status === "pending"
                    ? "info"
                    : "neutral"
              }
            >
              {item.status}
            </Badge>{" "}
            {item.reason}
            {item.grant_expires_at &&
              ` · grant expires ${formatWhen(item.grant_expires_at)}`}
            {item.decision_note && ` · ${item.decision_note}`}
          </p>
          {item.status === "pending" && (
            <>
              <label>
                Note{" "}
                <input
                  value={notes[item.public_id] ?? ""}
                  onChange={(event) =>
                    setNotes((current) => ({
                      ...current,
                      [item.public_id]: event.target.value,
                    }))
                  }
                />
              </label>{" "}
              <label>
                Grant expires{" "}
                <input
                  type="datetime-local"
                  value={expiry[item.public_id] ?? defaultExpiry()}
                  onChange={(event) =>
                    setExpiry((current) => ({
                      ...current,
                      [item.public_id]: event.target.value,
                    }))
                  }
                />
              </label>{" "}
              <Button onClick={() => void decide(item, "approve")}>
                Approve
              </Button>{" "}
              <Button
                variant="secondary"
                onClick={() => void decide(item, "reject")}
              >
                Reject
              </Button>
            </>
          )}
        </Card>
      ))}
    </section>
  );
}

/** Participant: request a deadline exception for a project and track it. */
export function ProjectExceptionPanel({
  workspaceId,
  eventId,
  projectId,
}: {
  workspaceId: string;
  eventId: string;
  projectId: string;
}) {
  const url = `${eventBase(workspaceId, eventId)}projects/${projectId}/exception-requests/`;
  const requests = useLoad<ExceptionRequest[]>(url);
  const [reason, setReason] = useState("");
  const [problem, setProblem] = useState("");
  const pending = requests.data?.some((item) => item.status === "pending");

  async function submit() {
    setProblem("");
    try {
      await api(url, "POST", { reason });
      setReason("");
      requests.reload();
    } catch (cause) {
      setProblem(messageOf(cause));
    }
  }

  return (
    <section aria-label="Deadline exception">
      <h3>Deadline exception</h3>
      {requests.error && (
        <ErrorState
          message={requests.error.message}
          onRetry={requests.reload}
        />
      )}
      {problem && <p role="alert">{problem}</p>}
      {requests.data && requests.data.length > 0 && (
        <ul>
          {requests.data.map((item) => (
            <li key={item.public_id}>
              <Badge
                tone={
                  item.status === "approved"
                    ? "success"
                    : item.status === "pending"
                      ? "info"
                      : "neutral"
                }
              >
                {item.status}
              </Badge>{" "}
              {item.reason}
              {item.decision_note && ` — ${item.decision_note}`}
              {item.grant_expires_at &&
                ` (valid until ${formatWhen(item.grant_expires_at)})`}
            </li>
          ))}
        </ul>
      )}
      {!pending && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void submit();
          }}
        >
          <label>
            Why do you need more time?{" "}
            <textarea
              required
              value={reason}
              onChange={(event) => setReason(event.target.value)}
            />
          </label>{" "}
          <button>Request exception</button>
        </form>
      )}
    </section>
  );
}

type Receipt = {
  token: string;
  claims: Record<string, unknown>;
  issued_at: string;
};

/** Participant: the signed receipt for a finalized submission. */
export function SubmissionReceipt({
  projectBase,
  stageId,
  stageName,
}: {
  projectBase: string;
  stageId: string;
  stageName?: string;
}) {
  const receipt = useLoad<Receipt>(
    `${projectBase}submissions/${stageId}/receipt/`,
  );
  const [copied, setCopied] = useState("");
  if (receipt.loading) return <LoadingState label="Loading receipt…" />;
  if (receipt.error)
    return (
      <ErrorState message={receipt.error.message} onRetry={receipt.reload} />
    );
  if (!receipt.data) return null;
  const { token, claims, issued_at } = receipt.data;
  const subject =
    claims?.subject && typeof claims.subject === "object"
      ? (claims.subject as Record<string, unknown>)
      : {};
  const event =
    claims?.event && typeof claims.event === "object"
      ? (claims.event as Record<string, unknown>)
      : {};

  async function copy() {
    try {
      await navigator.clipboard.writeText(token);
      setCopied("Receipt copied.");
    } catch {
      setCopied("Copy failed — select the receipt text instead.");
    }
  }

  return (
    <Card title="Signed submission receipt" as="h4">
      <div className="cx-human-receipt">
        <p className="cx-eyebrow">Finalized submission</p>
        <h5>{String(subject.project_name ?? "Your project")}</h5>
        <p>
          {String(event.name ?? "Event")} ·{" "}
          {stageName ?? String(subject.stage ?? "Stage")} · Version{" "}
          {String(subject.version ?? "—")}
        </p>
        <p>
          Finalized{" "}
          {formatWhen(
            typeof subject.finalized_at === "string"
              ? subject.finalized_at
              : issued_at,
          )}
        </p>
        <p>
          Receipt reference:{" "}
          <strong>{String(subject.receipt_id ?? "—")}</strong>
        </p>
        <p>Keep this signed receipt as proof of the submitted version.</p>
      </div>
      <FrozenSubmissionPreview base={projectBase} stageId={stageId} />
      <details className="cx-receipt-proof">
        <summary>Signature and technical proof</summary>
        <dl>
          {Object.entries(claims ?? {}).map(([key, value]) => (
            <div key={key}>
              <dt>{key}</dt>
              <dd>
                {typeof value === "object"
                  ? JSON.stringify(value)
                  : String(value)}
              </dd>
            </div>
          ))}
        </dl>
        <label>
          Receipt token{" "}
          <textarea
            readOnly
            value={token}
            rows={3}
            onFocus={(e) => e.target.select()}
          />
        </label>{" "}
        <Button variant="secondary" onClick={() => void copy()}>
          Copy receipt
        </Button>
        {copied && <p role="status">{copied}</p>}
      </details>
    </Card>
  );
}
