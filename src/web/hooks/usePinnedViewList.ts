import { useQueries } from "@tanstack/react-query";
import { apiRequest } from "../lib/api";
import { usePinnedViews } from "../lib/shellPreferences";
import { viewsBase, type SavedView } from "../lib/savedViews";

export type PinnedViewItem = { id: string; entity: string; name: string };

/**
 * The person's pinned views of the selected event that still exist and are still visible to them,
 * with their current names. A pin is only three ids; the server lists the views (per entity, under
 * the viewer's own rights), so a deleted or hidden view is not offered.
 */
export function usePinnedViewList(
  workspaceId: string,
  eventId: string,
  user: string,
): PinnedViewItem[] {
  const pins = usePinnedViews(user, workspaceId).filter(
    (pin) => pin.event === eventId,
  );
  const entities = [...new Set(pins.map((pin) => pin.entity))];
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
  for (const pin of pins) {
    const list = lists[entities.indexOf(pin.entity)]?.data;
    const view = Array.isArray(list)
      ? list.find((candidate) => candidate.public_id === pin.view)
      : undefined;
    if (view)
      items.push({ id: view.public_id, entity: pin.entity, name: view.name });
  }
  return items;
}
