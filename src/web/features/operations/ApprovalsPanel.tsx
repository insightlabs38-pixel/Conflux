import { useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { useLoad } from "../../hooks/useLoad";
import { describeProblem } from "../../lib/api";
import {
  approvalsUrl,
  cancelApproval,
  decideApproval,
  gatesUrl,
  setGate,
  statusWords,
  type Approval,
  type ApprovalStatus,
  type Gate,
} from "../../lib/approvals";

const TONE: Record<ApprovalStatus, "neutral" | "info" | "success" | "danger"> =
  {
    pending: "info",
    approved: "success",
    executed: "success",
    rejected: "danger",
    cancelled: "neutral",
    expired: "neutral",
  };
const FILTERS = [
  { value: "pending", label: "Waiting" },
  { value: "", label: "All" },
  { value: "executed", label: "Done" },
  { value: "rejected", label: "Rejected" },
];

/**
 * Approval gates of the event (PD-F002-B01-T06): choose which operations need a second person, and
 * answer the requests that are waiting. Rules (who may decide, expiry, single use) are the
 * server's; this shows what the server says is allowed.
 */
export function ApprovalsPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const [filter, setFilter] = useState("pending");
  const [problem, setProblem] = useState("");
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const gates = useLoad<Gate[]>(gatesUrl(workspaceId, eventId), {
    describe: describeProblem,
  });
  const list = useLoad<Approval[]>(
    `${approvalsUrl(workspaceId, eventId)}?limit=25${filter ? `&status=${filter}` : ""}`,
    { describe: describeProblem },
  );

  async function act(work: () => Promise<unknown>) {
    setBusy(true);
    setProblem("");
    try {
      await work();
    } catch (error) {
      setProblem(error instanceof Error ? error.message : "That did not work.");
    }
    setBusy(false);
    void list.reload();
    void gates.reload();
  }

  return (
    <Card title="Approvals">
      <h4>Operations that need a second person</h4>
      {gates.error && (
        <ErrorState message={gates.error.message} onRetry={gates.reload} />
      )}
      {gates.loading && !gates.data && <LoadingState label="Loading…" />}
      <ul className="cx-plain-list">
        {(gates.data ?? []).map((gate) => (
          <li key={gate.action}>
            <label>
              <input
                type="checkbox"
                checked={gate.enabled}
                disabled={busy}
                onChange={(e) =>
                  void act(() =>
                    setGate(
                      workspaceId,
                      eventId,
                      gate.action,
                      e.target.checked,
                    ),
                  )
                }
              />{" "}
              {gate.label}
            </label>
            <p className="cx-muted">
              {gate.description} Decided by {gate.deciders.join(" or ")}
              {gate.min_approvals > 1
                ? `, ${gate.min_approvals} approvals needed`
                : ""}
              . Off by default.
            </p>
          </li>
        ))}
      </ul>

      <h4>Requests</h4>
      <label>
        Show{" "}
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          {FILTERS.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
      </label>
      {problem && <p role="alert">{problem}</p>}
      {list.loading && !list.data && <LoadingState label="Loading requests…" />}
      {list.error && (
        <ErrorState message={list.error.message} onRetry={list.reload} />
      )}
      {list.data && list.data.length === 0 && (
        <EmptyState title="Nothing here">
          Requests appear when a gated operation is attempted.
        </EmptyState>
      )}
      <ul aria-label="Approval requests" className="cx-plain-list">
        {(list.data ?? []).map((item) => (
          <li key={item.public_id}>
            <p>
              <strong>{item.label}</strong>{" "}
              <Badge tone={TONE[item.status]}>{statusWords(item.status)}</Badge>
            </p>
            <ul>
              {item.summary.map((line, index) => (
                <li key={index}>{line}</li>
              ))}
            </ul>
            <p className="cx-muted">
              Asked by {item.requested_by}
              {" · "}
              {item.approvals}/{item.required_approvals} approvals
              {" · "}
              {item.status === "pending" || item.status === "approved"
                ? `valid until ${new Date(item.expires_at).toLocaleString()}`
                : null}
            </p>
            {item.decisions.map((d) => (
              <p key={d.actor} className="cx-muted">
                {d.actor} {d.decision === "approve" ? "approved" : "rejected"}
                {d.note ? `: ${d.note}` : ""}
              </p>
            ))}
            {item.status === "pending" && !item.can_decide && (
              <p className="cx-muted">
                Waiting for another person with a deciding role.
              </p>
            )}
            {item.can_decide && (
              <div role="group" aria-label={`Answer ${item.label}`}>
                <label>
                  Note (optional){" "}
                  <input
                    value={notes[item.public_id] ?? ""}
                    maxLength={500}
                    onChange={(e) =>
                      setNotes({ ...notes, [item.public_id]: e.target.value })
                    }
                  />
                </label>{" "}
                <Button
                  variant="primary"
                  disabled={busy}
                  onClick={() =>
                    void act(() =>
                      decideApproval(
                        workspaceId,
                        eventId,
                        item.public_id,
                        "approve",
                        notes[item.public_id] ?? "",
                      ),
                    )
                  }
                >
                  Approve
                </Button>{" "}
                <Button
                  variant="secondary"
                  disabled={busy}
                  onClick={() =>
                    void act(() =>
                      decideApproval(
                        workspaceId,
                        eventId,
                        item.public_id,
                        "reject",
                        notes[item.public_id] ?? "",
                      ),
                    )
                  }
                >
                  Reject
                </Button>
              </div>
            )}
            {item.can_cancel && (
              <Button
                variant="secondary"
                disabled={busy}
                onClick={() =>
                  void act(() =>
                    cancelApproval(workspaceId, eventId, item.public_id),
                  )
                }
              >
                Withdraw
              </Button>
            )}
          </li>
        ))}
      </ul>
    </Card>
  );
}
