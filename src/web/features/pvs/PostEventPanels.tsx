import { useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { api, eventBase, formatWhen, messageOf, useLoad } from "./http";

type PortfolioProject = {
  project: string;
  name: string;
  event: { public_id: string; name: string; status: string };
  team: string | null;
  track: string | null;
  submissions: { stage: string; status: string; version: number | null }[];
  finalized: boolean;
  awards: { award: string; award_id: string }[];
};
type Portfolio = { events: number; projects: PortfolioProject[] };

/** Cross-event history of the signed-in person's projects, submissions and awards. */
export function PortfolioPanel({ workspaceId }: { workspaceId: string }) {
  const portfolio = useLoad<Portfolio>(
    `/api/v1/workspaces/${workspaceId}/portfolio/me/`,
  );
  return (
    <section aria-label="My portfolio">
      <h3>My portfolio</h3>
      {portfolio.loading && <LoadingState label="Loading your portfolio…" />}
      {portfolio.error && (
        <ErrorState
          message={portfolio.error.message}
          onRetry={portfolio.reload}
        />
      )}
      {portfolio.data && portfolio.data.projects.length === 0 && (
        <EmptyState title="You have no projects yet." />
      )}
      {portfolio.data && portfolio.data.projects.length > 0 && (
        <>
          <p>
            {portfolio.data.projects.length} project
            {portfolio.data.projects.length === 1 ? "" : "s"} across{" "}
            {portfolio.data.events} event
            {portfolio.data.events === 1 ? "" : "s"}
          </p>
          <div
            className="cx-scroll-region"
            role="region"
            aria-label="Portfolio table"
            tabIndex={0}
          >
            <table>
              <thead>
                <tr>
                  <th scope="col">Project</th>
                  <th scope="col">Event</th>
                  <th scope="col">Submission</th>
                  <th scope="col">Awards</th>
                </tr>
              </thead>
              <tbody>
                {portfolio.data.projects.map((item) => (
                  <tr key={item.project}>
                    <th scope="row">{item.name}</th>
                    <td>
                      {item.event.name} <Badge>{item.event.status}</Badge>
                    </td>
                    <td>
                      {item.submissions.length === 0
                        ? "Not started"
                        : item.submissions
                            .map(
                              (s) =>
                                `${s.stage}: ${s.status}${s.version ? ` v${s.version}` : ""}`,
                            )
                            .join("; ")}
                    </td>
                    <td>
                      {item.awards.length === 0
                        ? "–"
                        : item.awards.map((a) => a.award).join(", ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}

type Continuation = {
  project: string;
  name: string;
  summary: string;
  url: string;
  seeking: string[];
  is_public?: boolean;
  hidden?: boolean;
  hidden_reason?: string;
  updates: { body: string; posted_at: string }[];
};
const SEEKING = ["contributors", "mentors", "users", "feedback", "partners"];

/** Participant: publish and update what happens to the project after the event. */
export function ProjectContinuationPanel({
  workspaceId,
  eventId,
  projectId,
}: {
  workspaceId: string;
  eventId: string;
  projectId: string;
}) {
  const url = `${eventBase(workspaceId, eventId)}projects/${projectId}/continuation/`;
  // Continuation only exists once the event has closed; don't probe (and 404) before then.
  const portfolio = useLoad<Portfolio>(
    `/api/v1/workspaces/${workspaceId}/portfolio/me/`,
  );
  const eventState = portfolio.data?.projects.find(
    (entry) => entry.project === projectId,
  )?.event.status;
  const open = eventState === "closed" || eventState === "archived";
  const item = useLoad<Continuation>(open ? url : null);
  const [summary, setSummary] = useState<string | null>(null);
  const [link, setLink] = useState<string | null>(null);
  const [seeking, setSeeking] = useState<string[] | null>(null);
  const [isPublic, setIsPublic] = useState<boolean | null>(null);
  const [update, setUpdate] = useState("");
  const [problem, setProblem] = useState("");
  const [status, setStatus] = useState("");
  const missing = item.error?.status === 404;
  const current = item.data;
  const value = {
    summary: summary ?? current?.summary ?? "",
    url: link ?? current?.url ?? "",
    seeking: seeking ?? current?.seeking ?? [],
    is_public: isPublic ?? current?.is_public ?? false,
  };

  async function run(action: () => Promise<unknown>, message: string) {
    setProblem("");
    setStatus("");
    try {
      await action();
      setStatus(message);
      item.reload();
    } catch (cause) {
      setProblem(messageOf(cause));
    }
  }

  return (
    <section aria-label="After the event">
      <h3>After the event</h3>
      {portfolio.data && !open && (
        <p>
          Once the event has closed you can share where this project is headed
          and post updates here.
        </p>
      )}
      {item.loading && <LoadingState label="Loading…" />}
      {item.error && !missing && (
        <ErrorState message={item.error.message} onRetry={item.reload} />
      )}
      {problem && <p role="alert">{problem}</p>}
      {status && <p role="status">{status}</p>}
      {current?.hidden && (
        <p role="status">
          An organizer hid this listing
          {current.hidden_reason ? `: ${current.hidden_reason}` : "."}
        </p>
      )}
      {open && (current || missing) && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void run(() => api(url, "PUT", value), "Saved.");
          }}
        >
          <label>
            Where is the project headed?{" "}
            <textarea
              required
              value={value.summary}
              onChange={(event) => setSummary(event.target.value)}
            />
          </label>{" "}
          <label>
            Link{" "}
            <input
              type="url"
              value={value.url}
              onChange={(event) => setLink(event.target.value)}
            />
          </label>
          <fieldset>
            <legend>Looking for</legend>
            {SEEKING.map((kind) => (
              <label key={kind}>
                <input
                  type="checkbox"
                  checked={value.seeking.includes(kind)}
                  onChange={(event) =>
                    setSeeking(
                      event.target.checked
                        ? [...value.seeking, kind]
                        : value.seeking.filter((k) => k !== kind),
                    )
                  }
                />{" "}
                {kind}
              </label>
            ))}
          </fieldset>
          <label>
            <input
              type="checkbox"
              checked={value.is_public}
              onChange={(event) => setIsPublic(event.target.checked)}
            />{" "}
            Show on the public continuation list
          </label>{" "}
          <button>Save</button>
        </form>
      )}
      {current && (
        <>
          <h4>Updates</h4>
          {current.updates.length === 0 && <p>No updates posted yet.</p>}
          <ul>
            {current.updates.map((entry, index) => (
              <li key={index}>
                {formatWhen(entry.posted_at)}: {entry.body}
              </li>
            ))}
          </ul>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void run(async () => {
                await api(`${url}updates/`, "POST", { body: update });
                setUpdate("");
              }, "Update posted.");
            }}
          >
            <label>
              Post an update{" "}
              <input
                required
                value={update}
                onChange={(event) => setUpdate(event.target.value)}
              />
            </label>{" "}
            <button>Post</button>
          </form>
        </>
      )}
    </section>
  );
}

/** Organizer: every continuation listing with hide / restore moderation. */
export function ContinuationsAdminPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = eventBase(workspaceId, eventId);
  const items = useLoad<Continuation[]>(`${base}continuations/`);
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [problem, setProblem] = useState("");

  async function moderate(item: Continuation, action: "hide" | "restore") {
    setProblem("");
    try {
      await api(
        `${base}projects/${item.project}/continuation/${action}/`,
        "POST",
        {
          reason: reasons[item.project] ?? "",
        },
      );
      items.reload();
    } catch (cause) {
      setProblem(messageOf(cause));
    }
  }

  return (
    <section aria-label="Post-event continuation">
      <h3>Post-event continuation</h3>
      {items.loading && <LoadingState label="Loading continuation listings…" />}
      {items.error && (
        <ErrorState message={items.error.message} onRetry={items.reload} />
      )}
      {problem && <p role="alert">{problem}</p>}
      {items.data && items.data.length === 0 && (
        <EmptyState title="No project has posted a continuation yet.">
          <p>Continuation opens for teams once the event has closed.</p>
        </EmptyState>
      )}
      {items.data?.map((item) => (
        <Card key={item.project} title={item.name} as="h4">
          <p>
            {item.summary}{" "}
            {item.hidden ? (
              <Badge tone="warning">Hidden</Badge>
            ) : item.is_public ? (
              <Badge tone="success">Public</Badge>
            ) : (
              <Badge>Private</Badge>
            )}
          </p>
          {item.seeking.length > 0 && <p>Seeking: {item.seeking.join(", ")}</p>}
          <label>
            Reason{" "}
            <input
              value={reasons[item.project] ?? ""}
              onChange={(event) =>
                setReasons((current) => ({
                  ...current,
                  [item.project]: event.target.value,
                }))
              }
            />
          </label>{" "}
          {item.hidden ? (
            <Button
              variant="secondary"
              onClick={() => void moderate(item, "restore")}
            >
              Restore
            </Button>
          ) : (
            <Button
              variant="secondary"
              onClick={() => void moderate(item, "hide")}
            >
              Hide
            </Button>
          )}
        </Card>
      ))}
    </section>
  );
}

type Challenge = {
  public_id: string;
  name: string;
  description: string;
  components: {
    public_id: string;
    kind: string;
    name: string;
    quantity: number;
  }[];
  resources: {
    public_id: string;
    kind: string;
    title: string;
    url: string;
    body: string;
  }[];
};
const isWebUrl = (url: string) => /^https?:\/\//i.test(url);

/** Participant: sponsor challenges and the resources sponsors offer for them. */
export function ChallengesPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const challenges = useLoad<Challenge[]>(
    `${eventBase(workspaceId, eventId)}challenges/`,
  );
  if (challenges.loading) return <LoadingState label="Loading challenges…" />;
  if (challenges.error)
    return (
      <ErrorState
        message={challenges.error.message}
        onRetry={challenges.reload}
      />
    );
  return (
    <section aria-label="Sponsor challenges">
      <h3>Sponsor challenges and resources</h3>
      {challenges.data?.length === 0 && (
        <p>No sponsor challenges have been announced for this event.</p>
      )}
      {challenges.data?.map((challenge) => (
        <Card key={challenge.public_id} title={challenge.name} as="h4">
          {challenge.description && <p>{challenge.description}</p>}
          {challenge.components.length > 0 && (
            <p>
              Prizes:{" "}
              {challenge.components
                .map(
                  (c) => `${c.quantity > 1 ? `${c.quantity}× ` : ""}${c.name}`,
                )
                .join(", ")}
            </p>
          )}
          {challenge.resources.length === 0 ? (
            <p>The sponsor has not published resources yet.</p>
          ) : (
            <ul aria-label={`Resources for ${challenge.name}`}>
              {challenge.resources.map((resource) => (
                <li key={resource.public_id}>
                  <Badge>{resource.kind}</Badge>{" "}
                  {resource.url && isWebUrl(resource.url) ? (
                    <a
                      href={resource.url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {resource.title}
                    </a>
                  ) : (
                    resource.title
                  )}
                  {resource.body && <> — {resource.body}</>}
                </li>
              ))}
            </ul>
          )}
        </Card>
      ))}
    </section>
  );
}
