/**
 * The platform's schema subset in the browser (PD-F002-B02-T01). It is the same validator as
 * `core/schema_subset.py`: `tests/fixtures/schema_cases.json` is run by both, so a form never says
 * "fine" to something the server refuses, or the reverse. The server still validates again in the
 * endpoint that owns the value; this only saves a round trip and points at the field.
 *
 * Keywords: `type` (object, string, integer, number, boolean, array; a list adds "null"), `enum`,
 * `default`, `title`, `description`, string `minLength`/`maxLength`/`format: "date-time"`, number
 * `minimum`/`maximum`, array `items`/`minItems`/`maxItems`/`uniqueItems`, object `properties`/
 * `required`/`additionalProperties`; UI hints `x-widget`, `x-help`, `x-create-default` and the
 * rule `x-nonblank`. Schemas are code-owned: they come from the server's catalogue, never from user
 * input.
 */
export type Widget = "input" | "textarea" | "select" | "switch" | "datetime";

export type Schema = {
  type: string | string[];
  title?: string;
  description?: string;
  default?: unknown;
  enum?: unknown[];
  minLength?: number;
  maxLength?: number;
  format?: "date-time";
  minimum?: number;
  maximum?: number;
  items?: Schema;
  minItems?: number;
  maxItems?: number;
  uniqueItems?: boolean;
  properties?: Record<string, Schema>;
  required?: string[];
  additionalProperties?: boolean;
  "x-widget"?: Widget;
  "x-help"?: string;
  "x-create-default"?: string | null;
  "x-nonblank"?: boolean;
};

export type Problem = {
  /** `rows[2].name`; "" for the value itself. */
  path: string;
  code: string;
  /** The same sentence the server gives. */
  message: string;
  /** The title of the part the problem is about. */
  label: string;
};

export const MAX_STRING = 100_000;
export const MAX_ARRAY = 1_000;
export const MAX_DEPTH = 8;

const INSTANT = /^\d{4}-\d\d-\d\dT\d\d:\d\d(:\d\d(\.\d+)?)?(Z|[+-]\d\d:\d\d)$/;
const isRecord = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);
const chars = (text: string) => Array.from(text).length;

function kindOf(schema: Schema): { kind: string; nullable: boolean } {
  const kinds = Array.isArray(schema.type) ? schema.type : [schema.type];
  return {
    kind: kinds.find((k) => k !== "null") ?? "",
    nullable: kinds.includes("null"),
  };
}

/** The starting value of an object schema (`x-create-default` first when creating). */
export function defaults(
  schema: Schema,
  creating = false,
): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [name, field] of Object.entries(schema.properties ?? {})) {
    const chosen =
      (creating ? field["x-create-default"] : undefined) ?? field.default;
    if (chosen !== undefined) out[name] = structuredClone(chosen);
  }
  return out;
}

function walk(
  schema: Schema,
  value: unknown,
  path: string,
  depth: number,
  problems: Problem[],
): unknown {
  const label = schema.title ?? "Configuration";
  const fail = (code: string, message: string) =>
    problems.push({ path, code, message, label });
  if (depth > MAX_DEPTH)
    return (fail("depth", "Nested too deeply."), undefined);
  const { kind, nullable } = kindOf(schema);
  if (value === null && nullable) return null;
  if (schema.enum && !schema.enum.some((option) => option === value)) {
    fail("enum", `Must be one of: ${schema.enum.join(", ")}.`);
    return undefined;
  }
  switch (kind) {
    case "object": {
      if (!isRecord(value))
        return (fail("type", "Must be an object."), undefined);
      const properties = schema.properties ?? {};
      if (
        schema.additionalProperties === false &&
        Object.keys(value).some((key) => !(key in properties))
      )
        fail("unknown_fields", "Unknown fields.");
      const required = new Set(schema.required ?? []);
      const result: Record<string, unknown> = {};
      for (const [name, field] of Object.entries(properties)) {
        const child = path ? `${path}.${name}` : name;
        if (Object.prototype.hasOwnProperty.call(value, name))
          result[name] = walk(field, value[name], child, depth + 1, problems);
        else if (field.default !== undefined)
          result[name] = walk(
            field,
            structuredClone(field.default),
            child,
            depth + 1,
            problems,
          );
        else if (required.has(name))
          problems.push({
            path: child,
            code: "required",
            message: "This field is required.",
            label: field.title ?? name,
          });
      }
      return result;
    }
    case "string": {
      if (typeof value !== "string")
        return (fail("type", "Must be text."), undefined);
      if (schema["x-nonblank"] && value.trim() === "")
        return (fail("required", "This field is required."), undefined);
      const longest = schema.maxLength ?? MAX_STRING;
      if (chars(value) > longest)
        return (
          fail("max_length", `Must be at most ${longest} characters.`),
          undefined
        );
      const shortest = schema.minLength ?? 0;
      if (chars(value) < shortest)
        return (
          fail("min_length", `Must be at least ${shortest} characters.`),
          undefined
        );
      if (
        schema.format === "date-time" &&
        !(INSTANT.test(value) && !Number.isNaN(Date.parse(value)))
      )
        return (
          fail("format", "Must be a date and time with a UTC offset."),
          undefined
        );
      return value;
    }
    case "integer":
    case "number": {
      const noun = kind === "integer" ? "an integer" : "a number";
      const { minimum: low, maximum: high } = schema;
      const wording =
        low !== undefined && high !== undefined
          ? `Must be ${noun} from ${low} to ${high}.`
          : low !== undefined
            ? `Must be ${noun} of at least ${low}.`
            : high !== undefined
              ? `Must be ${noun} of at most ${high}.`
              : `Must be ${noun}.`;
      const ok =
        typeof value === "number" &&
        Number.isFinite(value) &&
        (kind === "number" || Number.isInteger(value));
      if (!ok) return (fail("type", wording), undefined);
      if (
        (low !== undefined && value < low) ||
        (high !== undefined && value > high)
      )
        return (fail("range", wording), undefined);
      return value;
    }
    case "boolean":
      if (typeof value !== "boolean")
        return (fail("type", "Must be true or false."), undefined);
      return value;
    case "array": {
      const most = schema.maxItems ?? MAX_ARRAY;
      if (!Array.isArray(value) || value.length > most)
        return (
          fail("max_items", `Must be a list of at most ${most} items.`),
          undefined
        );
      const fewest = schema.minItems ?? 0;
      if (value.length < fewest)
        return (
          fail("min_items", `Must be a list of at least ${fewest} items.`),
          undefined
        );
      const items = value.map((item, index) =>
        walk(
          schema.items as Schema,
          item,
          `${path}[${index}]`,
          depth + 1,
          problems,
        ),
      );
      if (
        schema.uniqueItems &&
        new Set(items.map((i) => JSON.stringify(i))).size !== items.length
      )
        return (fail("unique", "Must not repeat an item."), undefined);
      return items;
    }
    default:
      return (
        fail("unsupported", "Unsupported configuration type."),
        undefined
      );
  }
}

/** Every problem with `value`, in the same order the server reports them. */
export function validate(schema: Schema, value: unknown): Problem[] {
  const problems: Problem[] = [];
  walk(schema, value, "", 0, problems);
  return problems;
}

/** The normalised value (declared keys only, defaults filled) and the problems found. */
export function normalize(
  schema: Schema,
  value: unknown,
): { value: unknown; problems: Problem[] } {
  const problems: Problem[] = [];
  const result = walk(schema, value, "", 0, problems);
  return { value: result, problems };
}

/** A problem as a sentence about its field ("Title is required."). */
export function sentence(problem: Problem): string {
  if (problem.code === "unsupported") return problem.message;
  if (problem.code === "required") return `${problem.label} is required.`;
  if (problem.code === "unknown_fields")
    return `${problem.label} has unknown fields.`;
  return `${problem.label} ${problem.message.charAt(0).toLowerCase()}${problem.message.slice(1)}`;
}

/** The first problem as a sentence, or "" when the value is valid. */
export function firstError(schema: Schema, value: unknown): string {
  const [first] = validate(schema, value);
  return first ? sentence(first) : "";
}

/** Problems keyed by path, for showing each next to its field. */
export function problemsByPath(problems: Problem[]): Record<string, string[]> {
  const out: Record<string, string[]> = {};
  for (const problem of problems)
    (out[problem.path] ??= []).push(problem.message);
  return out;
}
