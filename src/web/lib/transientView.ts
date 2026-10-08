import type { EntityField, FilterNode, Predicate } from "./entityQuery";

/**
 * A transient view in the address (PD-F006-B02-T07): the filter a person is looking at, put in a
 * link so a colleague opens the same list without anyone saving anything. The URL rule (lib/urlState.ts)
 * is that a link holds what you are looking at, never what you typed, so only a filter whose every
 * value is *structured* is encoded: a choice from the field's own list, a yes or no, a number, a
 * calendar date or time, or an emptiness check. A filter with free text or an id (a name, a team) is
 * not put in a link; the person is told, and saving it as a view is how it is shared.
 *
 * The encoding is the canonical filter text in URL-safe base64, decoded and checked again against the
 * catalogue when a link is opened; the server validates it once more. A link that does not decode
 * or does not fit is refused as a whole, never partly applied.
 */
export const MAX_ENCODED = 1500;
const MAX_DEPTH = 4;
const MAX_CONDITIONS = 20;

const DATE =
  /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2})?)?$/;

function safeValue(field: EntityField, value: unknown): boolean {
  switch (field.type) {
    case "enum":
      return typeof value === "string" && field.choices.includes(value);
    case "bool":
      return typeof value === "boolean";
    case "number":
      return typeof value === "number" && Number.isFinite(value);
    case "date":
      return typeof value === "string" && DATE.test(value);
    default:
      return false; // text and ids are typed or personal: never in a link
  }
}

function safePredicate(node: Predicate, fields: EntityField[]): boolean {
  const field = fields.find((f) => f.key === node.field && f.filterable);
  if (!field || !field.operators.includes(node.op)) return false;
  if (node.op === "is_null") return typeof node.value === "boolean";
  const values = Array.isArray(node.value) ? node.value : [node.value];
  if (values.length === 0 || values.length > 50) return false;
  if (Array.isArray(node.value) && node.op !== "in" && node.op !== "between")
    return false;
  return values.every((v) => safeValue(field, v));
}

function safeNode(
  node: unknown,
  fields: EntityField[],
  depth: number,
  budget: { n: number },
): node is FilterNode {
  if (
    !node ||
    typeof node !== "object" ||
    Array.isArray(node) ||
    depth > MAX_DEPTH
  )
    return false;
  const record = node as Record<string, unknown>;
  const keys = Object.keys(record);
  const group = keys.find((k) => k === "and" || k === "or");
  if (group) {
    const children = record[group];
    return (
      keys.length === 1 &&
      Array.isArray(children) &&
      children.length > 0 &&
      children.every((child) => safeNode(child, fields, depth + 1, budget))
    );
  }
  if (keys.length === 1 && keys[0] === "not")
    return safeNode(record.not, fields, depth + 1, budget);
  budget.n += 1;
  if (budget.n > MAX_CONDITIONS) return false;
  return (
    keys.every((k) => k === "field" || k === "op" || k === "value") &&
    typeof record.field === "string" &&
    typeof record.op === "string" &&
    safePredicate(record as unknown as Predicate, fields)
  );
}

/** Whether every value of this filter may go in a link. */
export const isShareable = (
  filter: FilterNode | null,
  fields: EntityField[],
): boolean => filter !== null && safeNode(filter, fields, 1, { n: 0 });

const toBase64Url = (text: string) => {
  const bytes = new TextEncoder().encode(text);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary)
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replace(/=+$/, "");
};
const fromBase64Url = (text: string) => {
  const binary = atob(text.replaceAll("-", "+").replaceAll("_", "/"));
  return new TextDecoder().decode(
    Uint8Array.from(binary, (c) => c.charCodeAt(0)),
  );
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

export type Encoded =
  | { kind: "ok"; text: string }
  | { kind: "empty" }
  | { kind: "text" } // holds free text or an id: not for a link
  | { kind: "long" }; // too long for a link

export function encodeFilter(
  filter: FilterNode | null,
  fields: EntityField[],
): Encoded {
  if (filter === null) return { kind: "empty" };
  if (!isShareable(filter, fields)) return { kind: "text" };
  const text = toBase64Url(JSON.stringify(sorted(filter)));
  return text.length > MAX_ENCODED ? { kind: "long" } : { kind: "ok", text };
}

/** The filter a link names, or null when it does not decode, does not fit the catalogue or holds anything unsafe. */
export function decodeFilter(
  text: string,
  fields: EntityField[],
): FilterNode | null {
  if (!/^[A-Za-z0-9_-]{1,1500}$/.test(text)) return null;
  try {
    const parsed: unknown = JSON.parse(fromBase64Url(text));
    return safeNode(parsed, fields, 1, { n: 0 })
      ? (parsed as FilterNode)
      : null;
  } catch {
    return null;
  }
}
