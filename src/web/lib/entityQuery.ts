import { useLoad, type Loaded } from "../hooks/useLoad";
import { describeProblem } from "./api";

/**
 * The client half of the universal entity query contract (`core.query`, PD-F002-B01-T01): typed
 * filter trees, the same canonical text the server stores, and the URL for an entity's page. The
 * server decides what may be queried and validates every part; nothing here filters or sorts rows.
 */

export type FieldType = "text" | "number" | "date" | "bool" | "enum" | "uuid";
export type EntityField = {
  key: string;
  label: string;
  type: FieldType;
  operators: string[];
  choices: string[];
  sortable: boolean;
  filterable: boolean;
  default: boolean;
};
export type EntityDescription = {
  key: string;
  label: string;
  default_sort: string[];
  /** Keys of the fields a free-text search looks in; none means the list has no search. */
  search_fields?: string[];
  fields: EntityField[];
};

export type Predicate = { field: string; op: string; value?: unknown };
export type FilterNode =
  | Predicate
  | { and: FilterNode[] }
  | { or: FilterNode[] }
  | { not: FilterNode };

export type EntityQuery = {
  filter?: FilterNode | null;
  /** `name,-created_at`: a field per key, `-` for descending. */
  sort?: string;
  columns?: string[];
  /** Free text: every word must appear in one of the list's search fields (server side). */
  search?: string;
  limit?: number;
  offset?: number;
};
export type EntityRow = { id: string } & Record<string, unknown>;
export type EntityPage<Row = EntityRow> = {
  entity: string;
  total: number;
  limit: number;
  offset: number;
  filter: FilterNode | null;
  sort: string[];
  search?: string;
  columns: string[];
  rows: Row[];
};

function sorted(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sorted);
  if (value && typeof value === "object")
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
        .map(([key, inner]) => [key, sorted(inner)]),
    );
  return value;
}

/** The one text form of a filter (sorted keys, no spaces): identical to `core.query.canonical`. */
export function canonicalFilter(filter: FilterNode): string {
  return JSON.stringify(sorted(filter));
}

export function isGroup(
  node: FilterNode,
): node is { and: FilterNode[] } | { or: FilterNode[] } | { not: FilterNode } {
  return "and" in node || "or" in node || "not" in node;
}

export function entityBase(workspaceId: string, eventId: string): string {
  return `/api/v1/workspaces/${workspaceId}/events/${eventId}/entities/`;
}

export function entityUrl(
  base: string,
  entity: string,
  query: EntityQuery = {},
): string {
  const params = new URLSearchParams();
  if (query.filter) params.set("filter", canonicalFilter(query.filter));
  if (query.sort) params.set("sort", query.sort);
  if (query.search) params.set("search", query.search);
  if (query.columns?.length) params.set("columns", query.columns.join(","));
  if (query.limit !== undefined) params.set("limit", String(query.limit));
  if (query.offset) params.set("offset", String(query.offset));
  const text = params.toString();
  return `${base}${entity}/${text ? `?${text}` : ""}`;
}

/** What the caller may query in this event, with each field's type and operators. */
export function useEntityCatalogue(
  base: string | null,
): Loaded<EntityDescription[]> {
  return useLoad<EntityDescription[]>(base, { describe: describeProblem });
}

/** One page of an entity. A null `base` waits (for example until the event is known). */
export function useEntityPage<Row = EntityRow>(
  base: string | null,
  entity: string,
  query: EntityQuery = {},
): Loaded<EntityPage<Row>> {
  return useLoad<EntityPage<Row>>(
    base === null ? null : entityUrl(base, entity, query),
    { describe: describeProblem },
  );
}
