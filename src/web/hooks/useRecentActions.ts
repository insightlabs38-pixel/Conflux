import { useQuery } from "@tanstack/react-query";
import { apiRequest } from "../lib/api";

export type RecentAction = {
  public_id: string;
  action: string;
  target_type: string;
  created_at: string;
};

/** "event.status_changed" read as words: "Event status changed". */
export function actionWords(action: string): string {
  const text = action.replace(/[._]+/g, " ").trim();
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : "Action";
}

/** "5 min ago", "3 h ago", "2 d ago", else the date. */
export function ago(iso: string, now = Date.now()): string {
  const seconds = Math.max(
    0,
    Math.round((now - new Date(iso).getTime()) / 1000),
  );
  if (Number.isNaN(seconds)) return "";
  if (seconds < 90) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 90) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 36) return `${hours} h ago`;
  const days = Math.round(hours / 24);
  if (days < 14) return `${days} d ago`;
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

/**
 * The caller's own latest actions in the workspace, from the existing audit log (`mine` and `limit`
 * bound it on the server). Organizers and admins only (the endpoint's own rule); anyone else asks
 * nothing. Read-only: the shell shows the log, it never writes it.
 */
export function useRecentActions(
  workspaceId: string,
  enabled: boolean,
  limit = 8,
) {
  const query = useQuery({
    queryKey: ["recent-actions", workspaceId, limit],
    queryFn: ({ signal }) =>
      apiRequest<RecentAction[]>(
        `/api/v1/audit/${workspaceId}/?mine=1&limit=${limit}`,
        { signal },
      ),
    enabled: enabled && workspaceId !== "",
    staleTime: 15_000,
    retry: false,
  });
  return {
    actions: Array.isArray(query.data) ? query.data : [],
    failed: query.isError,
    reload: () => query.refetch(),
    updatedAt: query.dataUpdatedAt || null,
  };
}
