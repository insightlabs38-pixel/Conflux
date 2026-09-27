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

  useEffect(() => {
    let active = true;
    Promise.all([
      readJson<AudienceKind[]>(base + "audiences/"),
      readJson<Message[]>(base + "messages/"),
    ])
      .then(([nextKinds, nextMessages]) => {
        if (active) {
          setKinds(nextKinds);
          setMessages(nextMessages);
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

  return (
    <Card title="Communications">
      {error && <p role="alert">{error}</p>}
      <form onSubmit={(event) => void send(event)}>
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
        {paramName && selectedKind && (
          <>
            <label htmlFor="comms-param">{paramName}</label>
            <select
              id="comms-param"
              value={param}
              onChange={(event) => setParam(event.target.value)}
              required
            >
              <option value="">Choose one</option>
              {(selectedKind.options[paramName] ?? []).map((option) => (
                <option key={option.public_id} value={option.public_id}>
                  {option.label}
                </option>
              ))}
            </select>
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
        <label htmlFor="comms-subject">Subject</label>
        <input
          id="comms-subject"
          value={subject}
          onChange={(event) => setSubject(event.target.value)}
          required
          maxLength={200}
        />
        <label htmlFor="comms-body">Message</label>
        <textarea
          id="comms-body"
          value={body}
          onChange={(event) => setBody(event.target.value)}
          required
        />
        <Button type="submit" disabled={busy}>
          Send message
        </Button>
      </form>
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
