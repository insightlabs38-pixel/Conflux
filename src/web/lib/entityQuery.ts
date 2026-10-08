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

export const OPERATOR_LABELS: Record<string, string> = {
  eq: "is",
  ne: "is not",
  in: "is one of",
  contains: "contains",
  startswith: "starts with",
  lt: "before or less than",
  lte: "at most",
  gt: "after or more than",
  gte: "at least",
  between: "between",
  is_null: "is empty",
};

const valueText = (value: unknown): string =>
  Array.isArray(value)
    ? value.join(", ")
    : value === undefined || value === null
      ? ""
      : String(value);

/**
 * A filter as a sentence, the same tree the server reads and nothing else: "Status is waitlisted
 * and Track is Open Data". Groups of the other kind are bracketed. Read-only; it is what the grid
 * shows as the active filter and what a person reads to a colleague.
 */
export function describeFilter(
  filter: FilterNode | null,
  fields: { key: string; label: string }[],
  inner = false,
): string {
  if (filter === null) return "";
  const label = (key: string) =>
    fields.find((f) => f.key === key)?.label ?? key;
  if ("and" in filter || "or" in filter) {
    const mode = "and" in filter ? "and" : "or";
    const children = (filter as Record<string, FilterNode[]>)[mode]
      .map((child) => describeFilter(child, fields, true))
      .filter(Boolean);
    const text = children.join(` ${mode} `);
    return inner && children.length > 1 ? `(${text})` : text;
  }
  if ("not" in filter)
    return `not (${describeFilter(filter.not, fields, true)})`;
  if (filter.op === "is_null")
    return `${label(filter.field)} is ${filter.value === false ? "not " : ""}empty`;
  const op = OPERATOR_LABELS[filter.op] ?? filter.op;
  if (filter.op === "between" && Array.isArray(filter.value))
    return `${label(filter.field)} ${op} ${filter.value.join(" and ")}`;
  return `${label(filter.field)} ${op} ${valueText(filter.value)}`.trim();
}

/** What the server said about a filter: a message per top-level condition, and any others. */
export type FilterProblems = {
  byCondition: Record<number, string>;
  general: string[];
};

/**
 * Read a 400 from the entity query. The server names the offending part by path
 * (`filter.and[1].op`); the builder shows each message beside the condition that holds that part
 * (a part inside a nested group is shown with its top-level condition).
 */
export function filterProblems(detail: unknown): FilterProblems | null {
  if (!detail || typeof detail !== "object") return null;
  const found: FilterProblems = { byCondition: {}, general: [] };
  let any = false;
  for (const [path, messages] of Object.entries(
    detail as Record<string, unknown>,
  )) {
    const match = /^filter(?:\.(?:and|or)\[(\d+)\])?/.exec(path);
    if (!match) continue;
    any = true;
    const text = Array.isArray(messages)
      ? messages.join(" ")
      : String(messages);
    if (match[1] !== undefined) {
      const index = Number(match[1]);
      found.byCondition[index] = found.byCondition[index]
        ? `${found.byCondition[index]} ${text}`
        : text;
    } else found.general.push(text);
  }
  return any ? found : null;
}
