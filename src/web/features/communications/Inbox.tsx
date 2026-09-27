import { useEffect, useState } from "react";
import { Badge } from "../../components/Badge";
import { Card } from "../../components/Card";

type InboxMessage = {
  public_id: string;
  subject: string;
  body: string;
  event_name: string;
  created_at: string;
  read_at: string | null;
};

async function readJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { credentials: "include", ...init });
  if (!response.ok) throw new Error(`Inbox request failed (${response.status}).`);
  return response.json() as Promise<T>;
}

export function Inbox({ workspaceId }: { workspaceId: string }) {
  const base = `/api/v1/workspaces/${workspaceId}/inbox/`;
  const [messages, setMessages] = useState<InboxMessage[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    readJson<InboxMessage[]>(base)
      .then((items) => {
        if (active) setMessages(items);
      })
      .catch((cause: unknown) => {
        if (active) setError(cause instanceof Error ? cause.message : "Inbox could not load.");
      });
    return () => {
      active = false;
    };
  }, [base]);

  async function markRead(id: string) {
    try {
      const updated = await readJson<InboxMessage>(`${base}${id}/read/`, { method: "POST" });
      setMessages((current) => current.map((item) => (item.public_id === id ? updated : item)));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not mark message as read.");
    }
  }

  if (messages.length === 0 && !error) return null;

  return (
    <Card title="Inbox">
      {error && <p role="alert">{error}</p>}
      <ul>
        {messages.map((message) => (
          <li key={message.public_id}>
            {!message.read_at && <Badge tone="info">new</Badge>}{" "}
            <strong>{message.subject}</strong> ({message.event_name}): {message.body}
            {!message.read_at && (
              <>
                {" "}
                <button type="button" onClick={() => void markRead(message.public_id)}>
                  Mark read
                </button>
              </>
            )}
          </li>
        ))}
      </ul>
    </Card>
  );
}
