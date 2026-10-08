import { Fragment, useId, type ReactNode } from "react";
import {
  operatorLabel,
  type EntityField,
  type FilterNode,
  type FilterProblems,
  type Predicate,
} from "../lib/entityQuery";
import { Button } from "./Button";

type Mode = "and" | "or";
type Group = { mode: Mode; children: FilterNode[] };

/** How deep a group may sit (the root is level 1); the server allows 4, one is kept in reserve. */
export const MAX_GROUP_DEPTH = 3;
/** The server's limit on conditions in one filter (core.query.MAX_PREDICATES). */
export const MAX_CONDITIONS = 20;

const isAnd = (node: FilterNode): node is { and: FilterNode[] } =>
  "and" in node;
const isOr = (node: FilterNode): node is { or: FilterNode[] } => "or" in node;
const groupOf = (node: FilterNode): Group | null =>
  isAnd(node)
    ? { mode: "and", children: node.and }
    : isOr(node)
      ? { mode: "or", children: node.or }
      : null;
const make = (mode: Mode, children: FilterNode[]): FilterNode =>
  ({ [mode]: children }) as FilterNode;

/** The root as an editable group: nothing, one condition or a group all read as "match these". */
function rootGroup(filter: FilterNode | null): Group | null {
  if (filter === null) return { mode: "and", children: [] };
  return (
    groupOf(filter) ??
    ("not" in filter ? null : { mode: "and", children: [filter] })
  );
}

/** Empty groups go; a root with one child is that child, so the stored text stays canonical. */
function tidy(node: FilterNode | null, root = true): FilterNode | null {
  if (node === null) return null;
  const group = groupOf(node);
  if (!group) return node;
  const children = group.children
    .map((child) => tidy(child, false))
    .filter((child): child is FilterNode => child !== null);
  if (children.length === 0) return null;
  if (root && children.length === 1) return children[0];
  return make(group.mode, children);
}

export const countConditions = (node: FilterNode | null): number => {
  if (node === null) return 0;
  const group = groupOf(node);
  if (group)
    return group.children.reduce((n, child) => n + countConditions(child), 0);
  if ("not" in node) return countConditions(node.not);
  return 1;
};

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
 * Build a filter for an entity from its catalogue: match all or any of conditions and of nested
 * groups of them, each condition a field, an operator the field's type offers and a typed value.
 * The tree is the one the server reads; it validates every part and names a refused one by its
 * path, which is shown beside the condition or group it names. A `not` made elsewhere is kept as
 * it is and can be removed, not edited.
 */
export function FilterBuilder({
  fields,
  value,
  onChange,
  problems,
}: {
  fields: EntityField[];
  value: FilterNode | null;
  onChange: (filter: FilterNode | null) => void;
  /** What the server said about this filter, shown beside the condition or group each names. */
  problems?: FilterProblems | null;
}) {
  const id = useId();
  const filterable = fields.filter((field) => field.filterable);
  const root = rootGroup(value);
  const total = countConditions(value);
  const full = total >= MAX_CONDITIONS;
  const sequence = { n: 0, groups: 0 };
  const fieldOf = (key: string) => filterable.find((f) => f.key === key);
  const fresh = (): Predicate => {
    const first = filterable[0];
    return {
      field: first.key,
      op: first.operators[0],
      value: first.type === "bool" ? true : "",
    };
  };
  const emit = (node: FilterNode | null) => onChange(tidy(node));

  if (root === null)
    return (
      <div role="group" aria-label="Filter">
        <p>
          This filter uses a negation, which is kept as it is and applied. It
          cannot be edited here.
        </p>
        <Button variant="secondary" onClick={() => onChange(null)}>
          Clear filter
        </Button>
      </div>
    );

  /** The problem the server named for the node at `path`; a root condition is the root's. */
  const problemAt = (path: string, implicit = false) =>
    problems?.byPath[path] ??
    (implicit && problems?.general.length
      ? problems.general.join(" ")
      : undefined);

  function renderCondition({
    condition,
    path,
    implicit,
    onChange: change,
    onRemove,
  }: {
    condition: Predicate;
    path: string;
    implicit: boolean;
    onChange: (next: Predicate) => void;
    onRemove: () => void;
  }) {
    const number = ++sequence.n;
    const field = fieldOf(condition.field) ?? filterable[0];
    const operators = field?.operators ?? [];
    const op = operators.includes(condition.op)
      ? condition.op
      : (operators[0] ?? "eq");
    const problem = problemAt(path, implicit);
    const problemId = `${id}-problem-${number}`;
    const invalid = {
      "aria-invalid": problem ? true : undefined,
      "aria-describedby": problem ? problemId : undefined,
    } as const;
    const label = `condition ${number}`;
    const set = (next: unknown) =>
      change({ field: field.key, op, value: next });
    const list = (v: unknown): string[] =>
      Array.isArray(v)
        ? v.map(String)
        : v === "" || v === undefined || v === null
          ? []
          : [String(v)];
    const scalarType =
      field?.type === "number"
        ? "number"
        : field?.type === "date"
          ? "date"
          : "text";
    const parse = (text: string): unknown =>
      field?.type === "number" ? (text === "" ? "" : Number(text)) : text;
    let control: ReactNode;
    if (op === "is_null") {
      control = (
        <select
          aria-label={`Value of ${label}`}
          {...invalid}
          value={String(condition.value !== false)}
          onChange={(e) => set(e.target.value === "true")}
        >
          <option value="true">yes</option>
          <option value="false">no</option>
        </select>
      );
    } else if (field?.type === "bool") {
      control = (
        <select
          aria-label={`Value of ${label}`}
          {...invalid}
          value={String(condition.value === true)}
          onChange={(e) => set(e.target.value === "true")}
        >
          <option value="true">yes</option>
          <option value="false">no</option>
        </select>
      );
    } else if (field?.type === "enum" && op === "in") {
      const chosen = new Set(list(condition.value));
      control = (
        <fieldset aria-label={`Values of ${label}`} {...invalid}>
          {field.choices.map((choice) => (
            <label key={choice}>
              <input
                type="checkbox"
                checked={chosen.has(choice)}
                onChange={(e) => {
                  const next = new Set(chosen);
                  if (e.target.checked) next.add(choice);
                  else next.delete(choice);
                  set(field.choices.filter((c) => next.has(c)));
                }}
              />{" "}
              {choice}
            </label>
          ))}
        </fieldset>
      );
    } else if (field?.type === "enum") {
      control = (
        <select
          aria-label={`Value of ${label}`}
          {...invalid}
          value={show(condition.value)}
          onChange={(e) => set(e.target.value)}
        >
          <option value="" />
          {field.choices.map((choice) => (
            <option key={choice} value={choice}>
              {choice}
            </option>
          ))}
        </select>
      );
    } else if (op === "between") {
      const [from = "", to = ""] = list(condition.value);
      const pair = (start: string, end: string) =>
        set(
          [start, end].map((v) =>
            scalarType === "number" && v !== "" ? Number(v) : v,
          ),
        );
      control = (
        <>
          <input
            aria-label={`Start of ${label}`}
            {...invalid}
            type={scalarType}
            value={from}
            onChange={(e) => pair(e.target.value, to)}
          />{" "}
          and{" "}
          <input
            aria-label={`End of ${label}`}
            {...invalid}
            type={scalarType}
            value={to}
            onChange={(e) => pair(from, e.target.value)}
          />
        </>
      );
    } else if (op === "in") {
      control = (
        <input
          aria-label={`Value of ${label}`}
          {...invalid}
          type="text"
          placeholder="comma separated"
          value={show(condition.value)}
          onChange={(e) => set(typed(field, op, e.target.value))}
        />
      );
    } else {
      control = (
        <input
          aria-label={`Value of ${label}`}
          {...invalid}
          type={scalarType}
          value={show(condition.value)}
          onChange={(e) => set(parse(e.target.value))}
        />
      );
    }
    return (
      <li>
        <select
          aria-label={`Field of ${label}`}
          value={field?.key}
          onChange={(e) => {
            const next = fieldOf(e.target.value)!;
            change({
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
          aria-label={`Operator of ${label}`}
          value={op}
          onChange={(e) => {
            const next = e.target.value;
            // the value keeps what it can: a pair or a list gives its first item to a single
            // value, a single value starts a pair or a list
            const current = condition.value;
            const keep =
              next === "is_null"
                ? true
                : next === "between"
                  ? list(current).slice(0, 2)
                  : next === "in"
                    ? list(current)
                    : Array.isArray(current)
                      ? (current[0] ?? "")
                      : current;
            change({ field: field.key, op: next, value: keep });
          }}
        >
          {operators.map((o) => (
            <option key={o} value={o}>
              {operatorLabel(field.type, o)}
            </option>
          ))}
        </select>
        {control}{" "}
        <Button
          variant="secondary"
          aria-label={`Remove condition ${number}`}
          onClick={onRemove}
        >
          Remove
        </Button>
        {problem && (
          <p id={problemId} role="alert" className="cx-filter-problem">
            Condition {number}: {problem}
          </p>
        )}
      </li>
    );
  }

  function renderGroup({
    group,
    path,
    depth,
    onGroup,
    onRemove,
  }: {
    group: Group;
    path: string;
    depth: number;
    onGroup: (next: Group) => void;
    onRemove?: () => void;
  }) {
    const number = onRemove ? ++sequence.groups : 0;
    const at = (index: number) =>
      `${path ? path + "." : ""}${group.mode}[${index}]`;
    const setChild = (index: number, node: FilterNode | null) =>
      onGroup({
        ...group,
        children: group.children.flatMap((child, i) =>
          i === index ? (node === null ? [] : [node]) : [child],
        ),
      });
    const groupProblem = onRemove ? problems?.byPath[path] : undefined;
    const body = (
      <>
        {group.children.length > 1 && (
          <label>
            Match{" "}
            <select
              aria-label={onRemove ? `Match of group ${number}` : undefined}
              value={group.mode}
              onChange={(e) =>
                onGroup({ ...group, mode: e.target.value as Mode })
              }
            >
              <option value="and">all conditions</option>
              <option value="or">any condition</option>
            </select>
          </label>
        )}
        {groupProblem && (
          <p role="alert" className="cx-filter-problem">
            Group {number}: {groupProblem}
          </p>
        )}
        <ul>
          {group.children.map((child, index) => {
            const inner = groupOf(child);
            if (inner)
              return (
                <li key={index}>
                  {renderGroup({
                    group: inner,
                    path: at(index),
                    depth: depth + 1,
                    onGroup: (next) =>
                      setChild(index, make(next.mode, next.children)),
                    onRemove: () => setChild(index, null),
                  })}
                </li>
              );
            if ("not" in child)
              return (
                <li key={index}>
                  <span>not ({describeNot(child)})</span>{" "}
                  <Button
                    variant="secondary"
                    onClick={() => setChild(index, null)}
                  >
                    Remove
                  </Button>
                </li>
              );
            return (
              <Fragment key={index}>
                {renderCondition({
                  condition: child as Predicate,
                  path: at(index),
                  implicit:
                    !onRemove &&
                    group.children.length === 1 &&
                    value !== null &&
                    groupOf(value) === null,
                  onChange: (next) => setChild(index, next),
                  onRemove: () => setChild(index, null),
                })}
              </Fragment>
            );
          })}
        </ul>
        <Button
          variant="secondary"
          disabled={filterable.length === 0 || full}
          onClick={() =>
            onGroup({ ...group, children: [...group.children, fresh()] })
          }
        >
          {onRemove ? `Add condition to group ${number}` : "Add condition"}
        </Button>
        {depth < MAX_GROUP_DEPTH && (
          <Button
            variant="secondary"
            disabled={filterable.length === 0 || full}
            onClick={() =>
              onGroup({
                ...group,
                children: [
                  ...group.children,
                  make(group.mode === "and" ? "or" : "and", [fresh()]),
                ],
              })
            }
          >
            {onRemove ? `Add group inside group ${number}` : "Add group"}
          </Button>
        )}
        {onRemove && (
          <Button variant="secondary" onClick={onRemove}>
            Remove group {number}
          </Button>
        )}
      </>
    );
    return onRemove ? (
      <fieldset className="cx-filter-group">
        <legend>
          Group {number} (match {group.mode === "and" ? "all" : "any"} of these)
        </legend>
        {body}
      </fieldset>
    ) : (
      <div role="group" aria-label="Filter">
        {body}
      </div>
    );
  }

  const top = renderGroup({
    group: root,
    path: "",
    depth: 1,
    onGroup: (next) => emit(make(next.mode, next.children)),
  });
  return (
    <>
      {top}
      {full && (
        <p className="cx-muted">
          A filter holds at most {MAX_CONDITIONS} conditions.
        </p>
      )}
      {total > 0 && (
        <Button variant="secondary" onClick={() => onChange(null)}>
          Clear filter
        </Button>
      )}
    </>
  );
}

function describeNot(node: FilterNode): string {
  return "not" in node ? JSON.stringify(node.not) : "";
}
