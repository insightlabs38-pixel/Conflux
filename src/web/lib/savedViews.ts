import { useLoad, type Loaded } from "../hooks/useLoad";
import { apiJson, describeProblem } from "./api";
import {
  canonicalFilter,
  type EntityQuery,
  type FilterNode,
} from "./entityQuery";

/**
 * Saved views (PD-F002-B01-T02): named definitions of how to look at one entity in one event. A
 * view is a query definition, never rows; running it goes through the entity query under the
 * viewer's own rights. The only thing a shareable URL carries is the view's public id (`view_<entity>`),
 * because filters can hold free text and personal data (URL-state rules, lib/urlState.ts).
 */
export type ViewDefinition = {
  filter: FilterNode | null;
  sort: string;
  columns: string[];
  density: "compact" | "comfortable";
  /** Free text search; stored only when used, so views saved before it existed are unchanged. */
  search?: string;
};
export type SavedView = {
  public_id: string;
  entity: string;
  name: string;
  query: ViewDefinition;
  visibility: "private" | "organizers";
  version: number;
  owner: string;
  mine: boolean;
  updated_at: string;
};

export const EMPTY_DEFINITION: ViewDefinition = {
  filter: null,
  sort: "",
  columns: [],
  density: "comfortable",
};

export function viewsBase(workspaceId: string, eventId: string): string {
  return `/api/v1/workspaces/${workspaceId}/events/${eventId}/views/`;
}

export function useSavedViews(
  base: string | null,
  entity: string,
): Loaded<SavedView[]> {
  return useLoad<SavedView[]>(
    base === null ? null : `${base}?entity=${encodeURIComponent(entity)}`,
    { describe: describeProblem },
  );
}

/** The grid/list query a definition stands for (paging is the caller's). */
export function definitionQuery(definition: ViewDefinition): EntityQuery {
  return {
    filter: definition.filter,
    sort: definition.sort,
    columns: definition.columns,
    search: definition.search,
  };
}

/** Whether two definitions mean the same thing (filter compared by its canonical text). */
export function sameDefinition(a: ViewDefinition, b: ViewDefinition): boolean {
  const text = (d: ViewDefinition) =>
    JSON.stringify([
      d.filter ? canonicalFilter(d.filter) : null,
      d.sort,
      d.columns,
      d.density,
      d.search ?? "",
    ]);
  return text(a) === text(b);
}

export function createView(
  base: string,
  input: {
    entity: string;
    name: string;
    query: ViewDefinition;
    visibility?: SavedView["visibility"];
  },
): Promise<SavedView> {
  return apiJson<SavedView>(base, "POST", input);
}

export function updateView(
  base: string,
  view: SavedView,
  change: Partial<Pick<SavedView, "name" | "visibility" | "query">>,
): Promise<SavedView> {
  return apiJson<SavedView>(`${base}${view.public_id}/`, "PATCH", {
    ...change,
    version: view.version,
  });
}

export function deleteView(base: string, view: SavedView): Promise<void> {
  return apiJson<void>(`${base}${view.public_id}/`, "DELETE");
}
