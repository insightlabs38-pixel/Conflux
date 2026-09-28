import { useState } from "react";
import { Badge } from "../../components/Badge";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";
import { EmptyState } from "../../components/EmptyState";
import { ErrorState } from "../../components/ErrorState";
import { LoadingState } from "../../components/LoadingState";
import { api, eventBase, formatWhen, messageOf, useLoad } from "./http";

type MentorRequest = {
  public_id: string;
  topic: string;
  urgency: "low" | "normal" | "urgent";
  status: "pending" | "claimed" | "resolved" | "cancelled";
  claimed_by: string | null;
  resolution_note: string;
  project?: string;
  project_name?: string;
};
type Slot = {
  public_id: string;
  mentor: string;
  starts_at: string;
  ends_at: string;
  location: string;
  capacity: number;
  signup_count: number;
  my_signup?: string | null;
  attendees?: { public_id: string; project: string }[];
};
type Mentor = {
  public_id: string;
  mentor: string;
  mentor_id: string;
  headline: string;
  is_available: boolean;
};

const STATUS_TONE = {
  pending: "info",
  claimed: "warning",
  resolved: "success",
  cancelled: "neutral",
} as const;

function useSlots(base: string) {
  return useLoad<Slot[]>(`${base}office-hours/`);
}

function SlotList({
  slots,
  children,
}: {
  slots: Slot[];
  children?: (slot: Slot) => React.ReactNode;
}) {
  if (slots.length === 0) return <p>No upcoming office hours.</p>;
  return (
    <ul>
      {slots.map((slot) => (
        <li key={slot.public_id}>
          {slot.mentor} · {formatWhen(slot.starts_at)} –{" "}
          {formatWhen(slot.ends_at)}
          {slot.location && ` · ${slot.location}`} · {slot.signup_count}/
          {slot.capacity} booked
          {slot.attendees && slot.attendees.length > 0 && (
            <> ({slot.attendees.map((item) => item.project).join(", ")})</>
          )}{" "}
          {children?.(slot)}
        </li>
      ))}
    </ul>
  );
}

/** Participant: ask a mentor for help and book office hours for a project. */
export function ProjectMentorshipPanel({
  workspaceId,
  eventId,
  projectId,
}: {
  workspaceId: string;
  eventId: string;
  projectId: string;
}) {
  const base = eventBase(workspaceId, eventId);
  const requests = useLoad<MentorRequest[]>(
    `${base}projects/${projectId}/mentor-requests/`,
  );
  const slots = useSlots(base);
  const mentors = useLoad<Mentor[]>(`${base}mentors/`);
  const [topic, setTopic] = useState("");
  const [urgency, setUrgency] = useState("normal");
  const [problem, setProblem] = useState("");

  async function act(action: () => Promise<unknown>) {
    setProblem("");
    try {
      await action();
      requests.reload();
      slots.reload();
    } catch (cause) {
      setProblem(messageOf(cause));
    }
  }

  return (
    <section aria-label="Mentorship">
      <h3>Mentorship</h3>
      {problem && <p role="alert">{problem}</p>}
      {mentors.data && (
        <p>
          {mentors.data.length === 0
            ? "No mentors are available right now."
            : `Available mentors: ${mentors.data
                .map((m) =>
                  m.headline ? `${m.mentor} (${m.headline})` : m.mentor,
                )
                .join(", ")}`}
        </p>
      )}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void act(async () => {
            await api(`${base}projects/${projectId}/mentor-requests/`, "POST", {
              topic,
              urgency,
            });
            setTopic("");
          });
        }}
      >
        <label>
          What do you need help with?{" "}
          <input
            required
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
          />
        </label>{" "}
        <label>
          Urgency{" "}
          <select
            value={urgency}
            onChange={(event) => setUrgency(event.target.value)}
          >
            <option value="low">Low</option>
            <option value="normal">Normal</option>
            <option value="urgent">Urgent</option>
          </select>
        </label>{" "}
        <button>Request a mentor</button>
      </form>
      {requests.loading && <LoadingState label="Loading your requests…" />}
      {requests.error && (
        <ErrorState
          message={requests.error.message}
          onRetry={requests.reload}
        />
      )}
      {requests.data && requests.data.length > 0 && (
        <ul aria-label="Your mentor requests">
          {requests.data.map((item) => (
            <li key={item.public_id}>
              {item.topic}{" "}
              <Badge tone={STATUS_TONE[item.status]}>{item.status}</Badge>
              {item.claimed_by && <> · {item.claimed_by}</>}
              {item.resolution_note && <> · {item.resolution_note}</>}
              {(item.status === "pending" || item.status === "claimed") && (
                <>
                  {" "}
                  <Button
                    variant="secondary"
                    onClick={() =>
                      void act(() =>
                        api(
                          `${base}mentor-requests/${item.public_id}/cancel/`,
                          "POST",
                        ),
                      )
                    }
                  >
                    Cancel
                  </Button>
                </>
              )}
            </li>
          ))}
        </ul>
      )}
      <h4>Office hours</h4>
      {slots.error && (
        <ErrorState message={slots.error.message} onRetry={slots.reload} />
      )}
      {slots.data && (
        <SlotList slots={slots.data}>
          {(slot) =>
            slot.my_signup ? (
              <Button
                variant="secondary"
                onClick={() =>
                  void act(() =>
                    api(
                      `${base}office-hours/signups/${slot.my_signup}/`,
                      "DELETE",
                    ),
                  )
                }
              >
                Cancel booking
              </Button>
            ) : (
              <Button
                variant="secondary"
                disabled={slot.signup_count >= slot.capacity}
                onClick={() =>
                  void act(() =>
                    api(
                      `${base}office-hours/${slot.public_id}/signups/`,
                      "POST",
                      { project: projectId },
                    ),
                  )
                }
              >
                {slot.signup_count >= slot.capacity ? "Full" : "Book"}
              </Button>
            )
          }
        </SlotList>
      )}
    </section>
  );
}

/** Mentor / organizer: help-request queue, availability and office hours. */
export function MentorDeskPanel({
  workspaceId,
  eventId,
  isOrganizer,
}: {
  workspaceId: string;
  eventId: string;
  isOrganizer: boolean;
}) {
  const base = eventBase(workspaceId, eventId);
  const queue = useLoad<MentorRequest[]>(`${base}mentor-requests/queue/`);
  const slots = useSlots(base);
  const mentors = useLoad<Mentor[]>(`${base}mentors/`);
  const [problem, setProblem] = useState("");
  const [status, setStatus] = useState("");
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [reassignTo, setReassignTo] = useState<Record<string, string>>({});
  const [headline, setHeadline] = useState("");
  const [available, setAvailable] = useState(true);
  const [starts, setStarts] = useState("");
  const [ends, setEnds] = useState("");
  const [where, setWhere] = useState("");
  const [capacity, setCapacity] = useState("1");

  async function act(action: () => Promise<unknown>, message = "") {
    setProblem("");
    setStatus("");
    try {
      await action();
      if (message) setStatus(message);
      queue.reload();
      slots.reload();
      mentors.reload();
    } catch (cause) {
      setProblem(messageOf(cause));
    }
  }

  const DONE: Record<string, string> = {
    claim: "Request claimed.",
    resolve: "Request resolved.",
    reassign: "Request reassigned.",
  };
  const post = (item: MentorRequest, action: string, body?: object) =>
    act(
      () =>
        api(
          `${base}mentor-requests/${item.public_id}/${action}/`,
          "POST",
          body,
        ),
      DONE[action],
    );

  return (
    <section aria-label="Mentor desk">
      <h3>Mentor desk</h3>
      {problem && <p role="alert">{problem}</p>}
      {status && <p role="status">{status}</p>}
      {!isOrganizer && (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void act(
              () =>
                api(`${base}mentors/me/`, "PUT", {
                  headline,
                  is_available: available,
                }),
              "Availability saved.",
            );
          }}
        >
          <h4>Your availability</h4>
          <label>
            Headline{" "}
            <input
              value={headline}
              maxLength={200}
              onChange={(event) => setHeadline(event.target.value)}
            />
          </label>{" "}
          <label>
            <input
              type="checkbox"
              checked={available}
              onChange={(event) => setAvailable(event.target.checked)}
            />{" "}
            Available to help
          </label>{" "}
          <button>Save</button>
        </form>
      )}
      <h4>Help requests</h4>
      {queue.loading && <LoadingState label="Loading the queue…" />}
      {queue.error && (
        <ErrorState message={queue.error.message} onRetry={queue.reload} />
      )}
      {queue.data && queue.data.length === 0 && (
        <EmptyState title="The queue is empty." />
      )}
      {queue.data?.map((item) => (
        <Card
          key={item.public_id}
          title={item.project_name ?? "Project"}
          as="h5"
        >
          <p>
            {item.topic}{" "}
            <Badge tone={item.urgency === "urgent" ? "danger" : "neutral"}>
              {item.urgency}
            </Badge>{" "}
            <Badge tone={STATUS_TONE[item.status]}>{item.status}</Badge>
            {item.claimed_by && <> · claimed by {item.claimed_by}</>}
          </p>
          {item.status === "pending" && (
            <Button onClick={() => void post(item, "claim")}>Claim</Button>
          )}
          {item.status === "claimed" && (
            <>
              <label>
                Resolution note{" "}
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
              <Button
                onClick={() =>
                  void post(item, "resolve", {
                    note: notes[item.public_id] ?? "",
                  })
                }
              >
                Resolve
              </Button>
            </>
          )}
          {isOrganizer &&
            (item.status === "pending" || item.status === "claimed") && (
              <>
                {" "}
                <label>
                  Reassign to{" "}
                  <select
                    value={reassignTo[item.public_id] ?? ""}
                    onChange={(event) =>
                      setReassignTo((current) => ({
                        ...current,
                        [item.public_id]: event.target.value,
                      }))
                    }
                  >
                    <option value="">Choose a mentor</option>
                    {mentors.data?.map((mentor) => (
                      <option key={mentor.mentor_id} value={mentor.mentor_id}>
                        {mentor.mentor}
                      </option>
                    ))}
                  </select>
                </label>{" "}
                <Button
                  variant="secondary"
                  disabled={!reassignTo[item.public_id]}
                  onClick={() =>
                    void post(item, "reassign", {
                      to_mentor: reassignTo[item.public_id],
                    })
                  }
                >
                  Reassign
                </Button>
              </>
            )}
        </Card>
      ))}
      <h4>Office hours</h4>
      {slots.data && <SlotList slots={slots.data} />}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void act(async () => {
            await api(`${base}office-hours/`, "POST", {
              starts_at: new Date(starts).toISOString(),
              ends_at: new Date(ends).toISOString(),
              location: where,
              capacity: Number(capacity),
            });
            setStarts("");
            setEnds("");
            setWhere("");
          }, "Office hours scheduled.");
        }}
      >
        <label>
          Starts{" "}
          <input
            type="datetime-local"
            required
            value={starts}
            onChange={(event) => setStarts(event.target.value)}
          />
        </label>{" "}
        <label>
          Ends{" "}
          <input
            type="datetime-local"
            required
            value={ends}
            onChange={(event) => setEnds(event.target.value)}
          />
        </label>{" "}
        <label>
          Location{" "}
          <input
            value={where}
            onChange={(event) => setWhere(event.target.value)}
          />
        </label>{" "}
        <label>
          Capacity{" "}
          <input
            type="number"
            min={1}
            value={capacity}
            onChange={(event) => setCapacity(event.target.value)}
          />
        </label>{" "}
        <button>Schedule office hours</button>
      </form>
    </section>
  );
}
