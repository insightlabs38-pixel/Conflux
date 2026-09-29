import { useEffect, useState, type FormEvent } from "react";
import { Button } from "../../components/Button";
import { Card } from "../../components/Card";

type AudienceKind = {
  key: string;
  label: string;
  param_names: string[];
  options: Record<string, { public_id: string; label: string }[]>;
};

type Message = {
  public_id: string;
  subject: string;
  body: string;
  audience_kind: string;
  recipient_count: number;
  email_failure_count: number;
  created_at: string;
};

type Reminder = {
  public_id: string;
  kind: string;
  due_at: string;
  subject: string;
  status: string;
  last_error: string;
};

async function readJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { credentials: "include", ...init });
  if (!response.ok)
    throw new Error(`Communications request failed (${response.status}).`);
  return response.json() as Promise<T>;
}

export function CommunicationsPanel({
  workspaceId,
  eventId,
}: {
  workspaceId: string;
  eventId: string;
}) {
  const base = `/api/v1/workspaces/${workspaceId}/events/${eventId}/communications/`;
  const [kinds, setKinds] = useState<AudienceKind[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [audienceKind, setAudienceKind] = useState("");
  const [param, setParam] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [preview, setPreview] = useState<{
    count: number;
    sample: { username: string }[];
  } | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [reminderKind, setReminderKind] = useState("deadline");
  const [reminderDue, setReminderDue] = useState("");
  const [reminderSubject, setReminderSubject] = useState("");
  const [reminderBody, setReminderBody] = useState("");

  useEffect(() => {
    let active = true;
    Promise.all([
      readJson<AudienceKind[]>(base + "audiences/"),
      readJson<Message[]>(base + "messages/"),
      readJson<Reminder[]>(base + "reminders/"),
    ])
      .then(([nextKinds, nextMessages, nextReminders]) => {
        if (active) {
          setKinds(nextKinds);
          setMessages(nextMessages);
          setReminders(nextReminders);
          if (nextKinds.length > 0) setAudienceKind(nextKinds[0].key);
        }
      })
      .catch((cause: unknown) => {
        if (active)
          setError(
            cause instanceof Error
              ? cause.message
              : "Communications could not load.",
          );
      });
    return () => {
      active = false;
    };
  }, [base]);

  const selectedKind = kinds.find((kind) => kind.key === audienceKind);
  const paramName = selectedKind?.param_names[0];
  const audienceParams = paramName && param ? { [paramName]: param } : {};

  async function previewAudience() {
    setError("");
    try {
      setPreview(
        await readJson(base + "audiences/preview/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            audience_kind: audienceKind,
            audience_params: audienceParams,
          }),
        }),
      );
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Preview failed.");
    }
  }

  async function send(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const sent = await readJson<Message>(base + "messages/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject,
          body,
          audience_kind: audienceKind,
          audience_params: audienceParams,
        }),
      });
      setMessages((current) => [sent, ...current]);
      setSubject("");
      setBody("");
      setPreview(null);
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Message could not be sent.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function scheduleReminder(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const reminder = await readJson<Reminder>(base + "reminders/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind: reminderKind,
          due_at: new Date(reminderDue).toISOString(),
          audience_kind: audienceKind,
          audience_params: audienceParams,
          subject: reminderSubject,
          body: reminderBody,
        }),
      });
      setReminders((current) =>
        [...current, reminder].sort((a, b) => a.due_at.localeCompare(b.due_at)),
      );
      setReminderDue("");
      setReminderSubject("");
      setReminderBody("");
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Reminder could not be scheduled.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function cancelReminder(id: string) {
    setError("");
    try {
      const updated = await readJson<Reminder>(
        base + `reminders/${id}/cancel/`,
        { method: "POST" },
      );
      setReminders((current) =>
        current.map((item) => (item.public_id === id ? updated : item)),
      );
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Reminder could not be cancelled.",
      );
    }
  }

  return (
    <Card title="Communications">
      {error && <p role="alert">{error}</p>}
      <form onSubmit={(event) => void send(event)}>
        <div className="cx-field-pair">
          <label htmlFor="comms-audience">Audience</label>
          <select
            id="comms-audience"
            value={audienceKind}
            onChange={(event) => {
              setAudienceKind(event.target.value);
              setParam("");
              setPreview(null);
            }}
          >
            {kinds.map((kind) => (
              <option key={kind.key} value={kind.key}>
                {kind.label}
              </option>
            ))}
          </select>
        </div>
        {paramName && selectedKind && (
          <>
            <div className="cx-field-pair">
              <label htmlFor="comms-param">{paramName}</label>
              <select
                id="comms-param"
                value={param}
                onChange={(event) => {
                  setParam(event.target.value);
                  setPreview(null);
                }}
                required
              >
                <option value="">Choose one</option>
                {(selectedKind.options[paramName] ?? []).map((option) => (
                  <option key={option.public_id} value={option.public_id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </>
        )}
        <Button
          type="button"
          variant="secondary"
          onClick={() => void previewAudience()}
        >
          Preview audience
        </Button>
        {preview && (
          <p>
            {preview.count} recipient(s)
            {preview.sample.length > 0 &&
              ` — e.g. ${preview.sample.map((s) => s.username).join(", ")}`}
          </p>
        )}
        <div className="cx-field-pair">
          <label htmlFor="comms-subject">Subject</label>
          <input
            id="comms-subject"
            value={subject}
            onChange={(event) => setSubject(event.target.value)}
            required
            maxLength={200}
          />
        </div>
        <div className="cx-field-pair">
          <label htmlFor="comms-body">Message</label>
          <textarea
            id="comms-body"
            value={body}
            onChange={(event) => setBody(event.target.value)}
            required
          />
        </div>
        <Button type="submit" disabled={busy}>
          Send message
        </Button>
      </form>
      <h4>Scheduled reminders</h4>
      <p>
        Uses the audience selected above. Recipients are checked when the
        reminder is sent to the in-app inbox.
      </p>
      <form onSubmit={(event) => void scheduleReminder(event)}>
        <div className="cx-field-pair">
          <label htmlFor="reminder-kind">Reminder type</label>
          <select
            id="reminder-kind"
            value={reminderKind}
            onChange={(event) => setReminderKind(event.target.value)}
          >
            <option value="deadline">Submission deadline</option>
            <option value="judging">Judging</option>
            <option value="voting">Voting</option>
          </select>
        </div>
        <div className="cx-field-pair">
          <label htmlFor="reminder-due">Send at</label>
          <input
            id="reminder-due"
            type="datetime-local"
            value={reminderDue}
            onChange={(event) => setReminderDue(event.target.value)}
            required
          />
        </div>
        <div className="cx-field-pair">
          <label htmlFor="reminder-subject">Subject</label>
          <input
            id="reminder-subject"
            value={reminderSubject}
            onChange={(event) => setReminderSubject(event.target.value)}
            required
            maxLength={200}
          />
        </div>
        <div className="cx-field-pair">
          <label htmlFor="reminder-body">Message</label>
          <textarea
            id="reminder-body"
            value={reminderBody}
            onChange={(event) => setReminderBody(event.target.value)}
            required
          />
        </div>
        <Button type="submit" disabled={busy}>
          Schedule reminder
        </Button>
      </form>
      {reminders.length === 0 ? (
        <p>No reminders scheduled.</p>
      ) : (
        <ul aria-label="Reminders">
          {reminders.map((reminder) => (
            <li key={reminder.public_id}>
              <strong>{reminder.subject}</strong> · {reminder.kind} ·{" "}
              {reminder.status} ·{" "}
              <time dateTime={reminder.due_at}>
                {new Date(reminder.due_at).toLocaleString()}
              </time>
              {reminder.last_error && ` · ${reminder.last_error}`}
              {reminder.status === "pending" && (
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => void cancelReminder(reminder.public_id)}
                >
                  Cancel
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
      <h4>Sent messages</h4>
      {messages.length === 0 ? (
        <p>No messages sent yet.</p>
      ) : (
        <ul>
          {messages.map((message) => (
            <li key={message.public_id}>
              <strong>{message.subject}</strong> · {message.recipient_count}{" "}
              recipient(s)
              {message.email_failure_count > 0 &&
                ` · ${message.email_failure_count} email failure(s)`}
              {" · "}
              <time dateTime={message.created_at}>
                {new Date(message.created_at).toLocaleString()}
              </time>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
