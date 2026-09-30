import { useId } from "react";
import {
  isGroup,
  type EntityField,
  type FilterNode,
  type Predicate,
} from "../lib/entityQuery";
import { Button } from "./Button";

type Mode = "and" | "or";

const OPERATOR_LABELS: Record<string, string> = {
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

/** The conditions of a flat filter, or null when the filter is nested and cannot be edited here. */
function flat(
  filter: FilterNode | null,
): { mode: Mode; conditions: Predicate[] } | null {
  if (filter === null) return { mode: "and", conditions: [] };
  if (!isGroup(filter)) return { mode: "and", conditions: [filter] };
  for (const mode of ["and", "or"] as const) {
    if (mode in filter) {
      const children = (filter as Record<Mode, FilterNode[]>)[mode];
      if (children.every((child) => !isGroup(child)))
        return { mode, conditions: children as Predicate[] };
    }
  }
  return null;
}

function assemble(mode: Mode, conditions: Predicate[]): FilterNode | null {
  if (conditions.length === 0) return null;
  if (conditions.length === 1) return conditions[0];
  return { [mode]: conditions } as FilterNode;
}

function typed(field: EntityField, op: string, raw: string): unknown {
  if (op === "is_null") return raw !== "false";
  const one = (text: string): unknown =>
    field.type === "number"
      ? text === ""
        ? ""
        : Number(text)
      : field.type === "bool"
        ? text === "true"
        : text;
  if (op === "in" || op === "between")
    return raw
      .split(",")
      .map((part) => one(part.trim()))
      .filter((part) => part !== "");
  return one(raw);
}

function show(value: unknown): string {
  if (Array.isArray(value)) return value.join(", ");
  return value === undefined || value === null ? "" : String(value);
}

/**
 * Build a filter for an entity from its catalogue: match all or any of a list of conditions, each
 * a field, an operator the field's type offers, and a typed value. The server validates every
 * part; a nested filter made elsewhere (a saved view, a link) is shown and kept, not flattened.
 */
export function FilterBuilder({
  fields,
  value,
  onChange,
}: {
  fields: EntityField[];
  value: FilterNode | null;
  onChange: (filter: FilterNode | null) => void;
}) {
  const id = useId();
  const filterable = fields.filter((field) => field.filterable);
  const shape = flat(value);

  if (shape === null)
    return (
      <div role="group" aria-label="Filter">
        <p>
          This filter combines groups, so it cannot be edited here. It is still
          applied.
        </p>
        <Button variant="secondary" onClick={() => onChange(null)}>
          Clear filter
        </Button>
      </div>
    );

  const { mode, conditions } = shape;
  const update = (index: number, next: Predicate) =>
    onChange(
      assemble(
        mode,
        conditions.map((c, i) => (i === index ? next : c)),
      ),
    );
  const fieldOf = (key: string) => filterable.find((f) => f.key === key);

  return (
    <div role="group" aria-label="Filter">
      {conditions.length > 1 && (
        <label>
          Match{" "}
          <select
            value={mode}
            onChange={(e) =>
              onChange(assemble(e.target.value as Mode, conditions))
            }
          >
            <option value="and">all conditions</option>
            <option value="or">any condition</option>
          </select>
        </label>
      )}
      <ul>
        {conditions.map((condition, index) => {
          const field = fieldOf(condition.field) ?? filterable[0];
          const operators = field?.operators ?? [];
          const op = operators.includes(condition.op)
            ? condition.op
            : (operators[0] ?? "eq");
          return (
            <li key={`${id}-${index}`}>
              <select
                aria-label={`Field of condition ${index + 1}`}
                value={field?.key}
                onChange={(e) => {
                  const next = fieldOf(e.target.value)!;
                  update(index, {
                    field: next.key,
                    op: next.operators[0],
                    value: next.type === "bool" ? true : "",
                  });
                }}
              >
                {filterable.map((f) => (
                  <option key={f.key} value={f.key}>
                    {f.label}
                  </option>
                ))}
              </select>
              <select
                aria-label={`Operator of condition ${index + 1}`}
                value={op}
                onChange={(e) =>
                  update(index, {
                    field: field.key,
                    op: e.target.value,
                    value:
                      e.target.value === "is_null" ? true : condition.value,
                  })
                }
              >
                {operators.map((o) => (
                  <option key={o} value={o}>
                    {OPERATOR_LABELS[o] ?? o}
                  </option>
                ))}
              </select>
              {op === "is_null" ? (
                <select
                  aria-label={`Value of condition ${index + 1}`}
                  value={String(condition.value !== false)}
                  onChange={(e) =>
                    update(index, {
                      field: field.key,
                      op,
                      value: e.target.value === "true",
                    })
                  }
                >
                  <option value="true">yes</option>
                  <option value="false">no</option>
                </select>
              ) : field?.type === "enum" && op === "eq" ? (
                <select
                  aria-label={`Value of condition ${index + 1}`}
                  value={show(condition.value)}
                  onChange={(e) =>
                    update(index, {
                      field: field.key,
                      op,
                      value: e.target.value,
                    })
                  }
                >
                  <option value="" />
                  {field.choices.map((choice) => (
                    <option key={choice} value={choice}>
                      {choice}
                    </option>
                  ))}
                </select>
              ) : field?.type === "bool" ? (
                <select
                  aria-label={`Value of condition ${index + 1}`}
                  value={String(condition.value === true)}
                  onChange={(e) =>
                    update(index, {
                      field: field.key,
                      op,
                      value: e.target.value === "true",
                    })
                  }
                >
                  <option value="true">yes</option>
                  <option value="false">no</option>
                </select>
              ) : (
                <input
                  aria-label={`Value of condition ${index + 1}`}
                  type={
                    field?.type === "number" && op !== "in" && op !== "between"
                      ? "number"
                      : "text"
                  }
                  placeholder={
                    op === "in" || op === "between"
                      ? "comma separated"
                      : field?.type === "date"
                        ? "2027-03-05 or 2027-03-05T09:00:00Z"
                        : ""
                  }
                  value={show(condition.value)}
                  onChange={(e) =>
                    update(index, {
                      field: field.key,
                      op,
                      value: typed(field, op, e.target.value),
                    })
                  }
                />
              )}
              <Button
                variant="secondary"
                aria-label={`Remove condition ${index + 1}`}
                onClick={() =>
                  onChange(
                    assemble(
                      mode,
                      conditions.filter((_, i) => i !== index),
                    ),
                  )
                }
              >
                Remove
              </Button>
            </li>
          );
        })}
      </ul>
      <Button
        variant="secondary"
        disabled={filterable.length === 0}
        onClick={() => {
          const first = filterable[0];
          onChange(
            assemble(mode, [
              ...conditions,
              {
                field: first.key,
                op: first.operators[0],
                value: first.type === "bool" ? true : "",
              },
            ]),
          );
        }}
      >
        Add condition
      </Button>
      {conditions.length > 0 && (
        <Button variant="secondary" onClick={() => onChange(null)}>
          Clear filter
        </Button>
      )}
    </div>
  );
}
