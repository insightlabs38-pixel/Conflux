import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "../lib/api";
import { queryKeys } from "../lib/query";
import { useRealtimeInvalidate } from "./useRealtime";

export type InboxMessage = {
  public_id: string;
  subject: string;
  body: string;
  event_name: string;
  created_at: string;
  read_at: string | null;
};

/** The server returns the newest hundred; the unread figure is of those. */
export const INBOX_PAGE = 100;

/**
 * One person's inbox in one workspace: the list, the unread count, and marking one message read.
 * The header's notification center and the Messages destination both use this, so there is one
 * query, one cache entry and one mark-read path. New mail arrives as a realtime hint to refetch
 * (lib/realtime.ts): what is shown is what the server just returned for this account.
 */
export function useInbox(workspaceId: string, { live = true } = {}) {
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
    enabled: workspaceId !== "",
  });
  // One subscriber per workspace is enough: every instance shares this query, and two handlers on
  // the same topic would each invalidate it, doubling the reads on every hint. The header's
  // notification center is always mounted and keeps the cache fresh, so the Messages card passes
  // `live: false`.
  useRealtimeInvalidate(live ? `workspace:${workspaceId}:inbox` : null, key);
  const [actionError, setActionError] = useState("");
  const messages = Array.isArray(inbox.data) ? inbox.data : [];
  const loadError =
    inbox.isError && !inbox.isFetching
      ? inbox.error instanceof Error && inbox.error.message
        ? inbox.error.message
        : "Inbox could not load."
      : "";

  async function markRead(id: string) {
    setActionError("");
    try {
      const updated = await apiRequest<InboxMessage>(`${base}${id}/read/`, {
        method: "POST",
        describe: (status) => `Inbox request failed (${status}).`,
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

  return {
    messages,
    unread: messages.filter((message) => !message.read_at).length,
    loading: inbox.isPending && inbox.isFetching,
    /** A failure to read the list (what is already shown is kept). */
    loadError,
    /** A failure to mark one message read. */
    actionError,
    error: actionError || loadError,
    markRead,
    reload: () => inbox.refetch(),
  };
}
