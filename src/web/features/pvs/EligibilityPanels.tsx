import { useState, type FormEvent } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { api, eventBase, messageOf, useLoad } from "./http";

type Finding = {
  public_id: string;
  code: string;
  automated: boolean;
  severity: "blocking" | "advisory";
  message: string;
  state: "open" | "addressed" | "resolved" | "waived";
  participant_response: string;
  resolution_note: string;
};
type Review = {
  project: string;
  status: "pending" | "needs_remediation" | "cleared" | "ineligible";
  decision_note: string;
  revision: number;
  findings: Finding[];
};
type ReviewRow = {
  project: string;
  project_name: string;
  status: Review["status"];
  open_findings: number;
  addressed_findings: number;
  revision: number;
};
type PortfolioProject = { project: string; name: string };
type Page<T> = { results: T[] };

const STATUS_LABEL: Record<Review["status"], string> = {
  pending: "Pending review",
  needs_remediation: "Changes requested",
  cleared: "Cleared",
  ineligible: "Ineligible",
};
const STATUS_TONE = {
  pending: "info",
  needs_remediation: "warning",
  cleared: "success",
  ineligible: "danger",
} as const;
const STATE_TONE = {
  open: "warning",
  addressed: "info",
  resolved: "success",
  waived: "neutral",
} as const;

export function StatusBadge({ status }: { status: Review["status"] }) {
  return <Badge tone={STATUS_TONE[status]}>{STATUS_LABEL[status]}</Badge>;
}

function FindingList({
  findings,
  children,
}: {
  findings: Finding[];
  children?: (finding: Finding) => React.ReactNode;
}) {
  if (findings.length === 0) return <p>No findings.</p>;
  return (
    <ul className="cx-findings">
      {findings.map((finding) => (
        <li key={finding.public_id} className="cx-finding">
          <p className="cx-eyebrow">
            {finding.automated ? "Automated check" : "Organizer finding"} ·{" "}
            {finding.code}
          </p>
          <Badge tone={finding.severity === "blocking" ? "danger" : "neutral"}>
            {finding.severity}
          </Badge>{" "}
          <Badge tone={STATE_TONE[finding.state]}>{finding.state}</Badge>{" "}
          <p className="cx-finding__message">{finding.message}</p>
          {finding.participant_response && (
            <blockquote>
              <strong>Team response</strong>
              <p>{finding.participant_response}</p>
            </blockquote>
          )}
          {finding.resolution_note && (
            <p>
              <strong>Organizer decision:</strong> {finding.resolution_note}
            </p>
          )}
          {children?.(finding)}
        </li>
      ))}
    </ul>
  );
}

/** Participant: structured findings on their project, with remediation. */
export function ProjectEligibilityPanel({
  workspaceId,
  eventId,
  projectId,
}: {
  workspaceId: string;
  eventId: string;
  projectId: string;
}) {
  const base = `${eventBase(workspaceId, eventId)}projects/${projectId}/eligibility/`;
  const { data: review, error, loading, reload } = useLoad<Review>(base);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [problem, setProblem] = useState("");
  const [busy, setBusy] = useState("");

  async function respond(finding: Finding) {
    setProblem("");
    setBusy(finding.public_id);
    try {
      await api(`${base}findings/${finding.public_id}/respond/`, "POST", {
        response: drafts[finding.public_id] ?? "",
      });
      setDrafts((current) => ({ ...current, [finding.public_id]: "" }));
      reload();
    } catch (cause) {
      setProblem(messageOf(cause));
    } finally {
      setBusy("");
    }
  }

  return (
    <section aria-label="Eligibility review">
      <h3>Eligibility review</h3>
      <p>
        Review each finding, make the requested change, and describe your
        response. The organizers then decide whether to resolve or waive it.
      </p>
      {loading && <LoadingState label="Loading eligibility review…" />}
      {error && <ErrorState message={error.message} onRetry={reload} />}
      {problem && <p role="alert">{problem}</p>}
      {review && (
        <>
          <p>
            <StatusBadge status={review.status} /> · Review revision{" "}
            {review.revision}
            {review.decision_note && <> {review.decision_note}</>}
          </p>
          {review.status === "cleared" && (
            <p role="status">
              Your project is cleared. No further action is needed.
            </p>
          )}
          {review.status === "ineligible" && (
            <p role="status">
              This project was ruled ineligible. Contact the organizers if you
              believe this is a mistake.
            </p>
          )}
          {review.findings.length === 0 && review.status === "pending" ? (
            <p>No issues have been raised yet.</p>
          ) : (
            <FindingList findings={review.findings}>
              {(finding) =>
                finding.state === "open" &&
                review.status !== "ineligible" && (
                  <form
                    onSubmit={(event: FormEvent) => {
                      event.preventDefault();
                      void respond(finding);
                    }}
                  >
                    <label>
                      What did you change?{" "}
                      <textarea
                        required
                        value={drafts[finding.public_id] ?? ""}
                        onChange={(event) =>
                          setDrafts((current) => ({
                            ...current,
                            [finding.public_id]: event.target.value,
                          }))
                        }
                      />
                    </label>
                    <button disabled={busy === finding.public_id}>
                      Mark as fixed and resubmit for review
                    </button>
                  </form>
                )
              }
            </FindingList>
          )}
        </>
      )}
    </section>
  );
}

function ReviewDetail({
  base,
  projectId,
  onChanged,
}: {
  base: string;
  projectId: string;
  onChanged: () => void;
}) {
  const url = `${base}projects/${projectId}/eligibility/`;
  const { data: review, error, loading, reload } = useLoad<Review>(url);
  const [problem, setProblem] = useState("");
  const [note, setNote] = useState("");
  const [decision, setDecision] = useState("cleared");
  const [finding, setFinding] = useState("");
  const [severity, setSeverity] = useState("blocking");
  const [closeNotes, setCloseNotes] = useState<Record<string, string>>({});

  async function act(path: string, body?: object) {
    setProblem("");
    try {
      await api(url + path, "POST", body);
      reload();
      onChanged();
    } catch (cause) {
      setProblem(messageOf(cause));
    }
  }

  if (loading) return <LoadingState label="Loading review…" />;
  if (error) return <ErrorState message={error.message} onRetry={reload} />;
  if (!review) return null;
  return (
    <Card title="Review detail" as="h4">
      {problem && <p role="alert">{problem}</p>}
      <p>
        <StatusBadge status={review.status} /> revision {review.revision}
        {review.decision_note && <> · {review.decision_note}</>}
      </p>
      <Button variant="secondary" onClick={() => void act("checks/")}>
        Run automated checks
      </Button>
      <FindingList findings={review.findings}>
        {(item) =>
          (item.state === "open" || item.state === "addressed") && (
            <span>
              <label>
                Note{" "}
                <input
                  value={closeNotes[item.public_id] ?? ""}
                  onChange={(event) =>
                    setCloseNotes((current) => ({
                      ...current,
                      [item.public_id]: event.target.value,
                    }))
                  }
                />
              </label>{" "}
              {(["resolved", "waived"] as const).map((state) => (
                <Button
                  key={state}
                  variant="secondary"
                  onClick={() =>
                    void act(`findings/${item.public_id}/close/`, {
                      state,
                      note: closeNotes[item.public_id] ?? "",
                    })
                  }
                >
                  {state === "resolved" ? "Mark resolved" : "Waive"}
                </Button>
              ))}
            </span>
          )
        }
      </FindingList>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void act("findings/", { message: finding, severity }).then(() =>
            setFinding(""),
          );
        }}
      >
        <h5>Request changes</h5>
        <label>
          Finding{" "}
          <input
            required
            value={finding}
            onChange={(event) => setFinding(event.target.value)}
          />
        </label>{" "}
        <label>
          Severity{" "}
          <select
            value={severity}
            onChange={(event) => setSeverity(event.target.value)}
          >
            <option value="blocking">Blocking</option>
            <option value="advisory">Advisory</option>
          </select>
        </label>{" "}
        <button>Add finding</button>
      </form>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void act("decision/", { decision, note });
        }}
      >
        <h5>Decision</h5>
        <label>
          Outcome{" "}
          <select
            value={decision}
            onChange={(event) => setDecision(event.target.value)}
          >
            <option value="cleared">Approve (cleared)</option>
            <option value="needs_remediation">Request changes</option>
            <option value="ineligible">Reject (ineligible)</option>
            <option value="pending">Return to pending</option>
          </select>
        </label>{" "}
        <label>
          Note{" "}
          <input
            value={note}
            onChange={(event) => setNote(event.target.value)}
          />
        </label>{" "}
        <button>Record decision</button>
      </form>
    </Card>
  );
}

/** Organizer: review queue with approve / request changes / reject. */
export function EligibilityReviewPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = eventBase(workspaceId, eventId);
  const [filter, setFilter] = useState("");
  const reviews = useLoad<ReviewRow[]>(
    `${base}eligibility-reviews/${filter ? `?status=${filter}` : ""}`,
  );
  const projects = useLoad<Page<PortfolioProject>>(
    `/api/v1/workspaces/${workspaceId}/portfolio/projects/?event=${eventId}&limit=100`,
  );
  const [selected, setSelected] = useState("");

  return (
    <section aria-label="Eligibility review queue">
      <h3>Eligibility review</h3>
      <label>
        Show{" "}
        <select
          value={filter}
          onChange={(event) => setFilter(event.target.value)}
        >
          <option value="">All reviews</option>
          {Object.entries(STATUS_LABEL).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      {reviews.loading && <LoadingState label="Loading reviews…" />}
      {reviews.error && (
        <ErrorState message={reviews.error.message} onRetry={reviews.reload} />
      )}
      {reviews.data && reviews.data.length === 0 && (
        <EmptyState title="No eligibility reviews yet.">
          <p>Pick a project below to run its first check.</p>
        </EmptyState>
      )}
      {reviews.data && reviews.data.length > 0 && (
        <div
          className="cx-scroll-region"
          role="region"
          aria-label="Eligibility reviews table"
          tabIndex={0}
        >
          <table>
            <thead>
              <tr>
                <th scope="col">Project</th>
                <th scope="col">Status</th>
                <th scope="col">Open</th>
                <th scope="col">Addressed</th>
                <th scope="col">
                  <span className="cx-visually-hidden">Action</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {reviews.data.map((row) => (
                <tr key={row.project}>
                  <th scope="row">{row.project_name}</th>
                  <td>
                    <StatusBadge status={row.status} />
                  </td>
                  <td>{row.open_findings}</td>
                  <td>{row.addressed_findings}</td>
                  <td>
                    <Button
                      variant="secondary"
                      onClick={() => setSelected(row.project)}
                      aria-label={`Review ${row.project_name}`}
                    >
                      Review
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {projects.data && projects.data.results.length > 0 && (
        <label>
          Open a project{" "}
          <select
            value={selected}
            onChange={(event) => setSelected(event.target.value)}
          >
            <option value="">Choose a project</option>
            {projects.data.results.map((project) => (
              <option key={project.project} value={project.project}>
                {project.name}
              </option>
            ))}
          </select>
        </label>
      )}
      {selected && (
        <ReviewDetail
          key={selected}
          base={base}
          projectId={selected}
          onChanged={reviews.reload}
        />
      )}
    </section>
  );
}
