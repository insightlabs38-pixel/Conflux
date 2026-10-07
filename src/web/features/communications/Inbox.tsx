import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Status } from "../../components/Status";
import { Card } from "../../components/Card";
import { apiRequest } from "../../lib/api";
import { queryKeys } from "../../lib/query";
import { useRealtimeInvalidate } from "../../hooks/useRealtime";

type InboxMessage = {
  public_id: string;
  subject: string;
  body: string;
  event_name: string;
  created_at: string;
  read_at: string | null;
};

type Init = { method?: "POST" | "PUT" | "PATCH" | "DELETE"; body?: object };

function readJson<T>(url: string, init: Init = {}): Promise<T> {
  return apiRequest<T>(url, {
    ...init,
    describe: (status) => `Inbox request failed (${status}).`,
  });
}

export function Inbox({ workspaceId }: { workspaceId: string }) {
  const base = `/api/v1/workspaces/${workspaceId}/inbox/`;
  const client = useQueryClient();
  const key = queryKeys.inbox(workspaceId);
  const inbox = useQuery({
    queryKey: key,
    queryFn: ({ signal }) =>
      apiRequest<InboxMessage[]>(base, {
        signal,
        describe: (status) => `Inbox request failed (${status}).`,
      }),
    staleTime: 0,
  });
  // New messages arrive as a hint to refetch (lib/realtime.ts): what is shown is what the server
  // just returned for this account.
  useRealtimeInvalidate(`workspace:${workspaceId}:inbox`, key);
  const [actionError, setActionError] = useState("");
  const messages = inbox.data ?? [];
  const error =
    actionError ||
    (inbox.isError && !inbox.isFetching
      ? inbox.error instanceof Error && inbox.error.message
        ? inbox.error.message
        : "Inbox could not load."
      : "");

  async function markRead(id: string) {
    setActionError("");
    try {
      const updated = await readJson<InboxMessage>(`${base}${id}/read/`, {
        method: "POST",
      });
      client.setQueryData<InboxMessage[]>(key, (current) =>
        (current ?? []).map((item) => (item.public_id === id ? updated : item)),
      );
    } catch (cause) {
      setActionError(
        cause instanceof Error
          ? cause.message
          : "Could not mark message as read.",
      );
    }
  }

  if (messages.length === 0 && !error) return null;

  return (
    <Card title="Inbox">
      {error && <p role="alert">{error}</p>}
      <ul>
        {messages.map((message) => (
          <li key={message.public_id}>
            {!message.read_at && <Status tone="info">new</Status>}{" "}
            <strong>{message.subject}</strong> ({message.event_name}):{" "}
            {message.body}
            {!message.read_at && (
              <>
                {" "}
                <button
                  type="button"
                  onClick={() => void markRead(message.public_id)}
                >
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
