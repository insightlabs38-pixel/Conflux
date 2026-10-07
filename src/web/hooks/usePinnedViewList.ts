import { useQueries } from "@tanstack/react-query";
import { apiRequest } from "../lib/api";
import {
  usePinnedViews,
  useRecentViews,
  type PinnedView,
} from "../lib/shellPreferences";
import { viewsBase, type SavedView } from "../lib/savedViews";

export type PinnedViewItem = { id: string; entity: string; name: string };

/**
 * A list of view references (pins, recents) of the selected event resolved against what the server
 * lists now: each is three ids, the views are listed per entity under the viewer's own rights, so a
 * deleted or hidden view is not offered and a renamed one shows its new name.
 */
function useResolvedViews(
  workspaceId: string,
  eventId: string,
  user: string,
  refs: PinnedView[],
): PinnedViewItem[] {
  const own = refs.filter((ref) => ref.event === eventId);
  const entities = [...new Set(own.map((ref) => ref.entity))];
  const lists = useQueries({
    queries: entities.map((entity) => {
      const url = `${viewsBase(workspaceId, eventId)}?entity=${encodeURIComponent(entity)}`;
      return {
        queryKey: ["load", url, ""],
        queryFn: ({ signal }: { signal: AbortSignal }) =>
          apiRequest<SavedView[]>(url, { signal }),
        enabled: workspaceId !== "" && eventId !== "" && user !== "",
        staleTime: 30_000,
        retry: false,
      };
    }),
  });
  const items: PinnedViewItem[] = [];
  for (const ref of own) {
    const list = lists[entities.indexOf(ref.entity)]?.data;
    const view = Array.isArray(list)
      ? list.find((candidate) => candidate.public_id === ref.view)
      : undefined;
    if (view)
      items.push({ id: view.public_id, entity: ref.entity, name: view.name });
  }
  return items;
}

/** The person's pinned views of the selected event that still exist. */
export const usePinnedViewList = (
  workspaceId: string,
  eventId: string,
  user: string,
) =>
  useResolvedViews(
    workspaceId,
    eventId,
    user,
    usePinnedViews(user, workspaceId),
  );

/** The views the person opened lately in the selected event that still exist, newest first. */
export const useRecentViewList = (
  workspaceId: string,
  eventId: string,
  user: string,
) =>
  useResolvedViews(
    workspaceId,
    eventId,
    user,
    useRecentViews(user, workspaceId),
  );
