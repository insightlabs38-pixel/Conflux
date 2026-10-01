import { useId, type ChangeEvent } from "react";
import {
  defaults,
  problemsByPath,
  type Problem,
  type Schema,
} from "../lib/schema";
import { utcToZonedInput, zonedToUtc } from "../lib/timeline";
import { Button } from "./Button";

type Value = Record<string, unknown>;

/**
 * The generic editor for a code-owned schema (`lib/schema.ts`, PD-F002-B02-T01): one control per
 * property chosen from its type, bounds and `x-widget`, arrays of objects as rows with a declared
 * cap, per-field problems linked with `aria-describedby`. It holds no value of its own and no rule:
 * it renders what the schema declares and hands every change to `onChange`, and the endpoint that
 * owns the value validates again.
 *
 * Controls: text (`input`, or `textarea` for `x-widget: textarea`), `select` for an enum, a
 * checkbox for a boolean, a number input with min and max, a date-time input for
 * `format: date-time` (shown on the `timeZone` clock, stored as a UTC instant), a checkbox group for
 * an array of enum values, and rows for an array of objects or scalars. A nullable field is empty
 * when its value is null.
 */
export function SchemaForm({
  schema,
  value,
  onChange,
  problems = [],
  disabled = false,
  timeZone = "UTC",
}: {
  schema: Schema;
  value: Value;
  onChange: (next: Value) => void;
  /** From `validate(schema, value)`; shown beside the field each belongs to. */
  problems?: Problem[];
  disabled?: boolean;
  timeZone?: string;
}) {
  return (
    <Fields
      schema={schema}
      value={value}
      path=""
      onChange={onChange}
      problems={problemsByPath(problems)}
      disabled={disabled}
      timeZone={timeZone}
    />
  );
}

type Shared = {
  problems: Record<string, string[]>;
  disabled: boolean;
  timeZone: string;
};

function Fields({
  schema,
  value,
  path,
  onChange,
  ...shared
}: Shared & {
  schema: Schema;
  value: Value;
  path: string;
  onChange: (next: Value) => void;
}) {
  return (
    <>
      {Object.entries(schema.properties ?? {}).map(([key, field]) => (
        <Field
          key={key}
          name={key}
          field={field}
          value={value[key] ?? field.default}
          path={path ? `${path}.${key}` : key}
          onChange={(next) => onChange({ ...value, [key]: next })}
          {...shared}
        />
      ))}
    </>
  );
}

const nullable = (field: Schema) =>
  Array.isArray(field.type) && field.type.includes("null");
const kind = (field: Schema) =>
  (Array.isArray(field.type) ? field.type : [field.type]).find(
    (k) => k !== "null",
  );
const labelOf = (field: Schema, name: string) =>
  field.title ?? name.replace(/_/g, " ");

function Field({
  name,
  field,
  value,
  path,
  onChange,
  problems,
  disabled,
  timeZone,
}: Shared & {
  name: string;
  field: Schema;
  value: unknown;
  path: string;
  onChange: (next: unknown) => void;
}) {
  const id = useId();
  const type = kind(field);
  const label = labelOf(field, name);
  const hint = field["x-help"] ?? field.description;
  const messages = problems[path] ?? [];
  const described = [
    hint ? `${id}-hint` : "",
    messages.length ? `${id}-error` : "",
  ]
    .filter(Boolean)
    .join(" ");
  const aria = {
    "aria-describedby": described || undefined,
    "aria-invalid": messages.length ? true : undefined,
    disabled,
  };
  const notes = (
    <>
      {hint && (
        <small id={`${id}-hint`} className="cx-muted">
          {hint}
        </small>
      )}
      {messages.length > 0 && (
        <small id={`${id}-error`} role="alert">
          {messages.join(" ")}
        </small>
      )}
    </>
  );

  if (type === "object")
    return (
      <fieldset>
        <legend>{label}</legend>
        <Fields
          schema={field}
          value={(value as Value) ?? {}}
          path={path}
          onChange={onChange}
          problems={problems}
          disabled={disabled}
          timeZone={timeZone}
        />
        {notes}
      </fieldset>
    );

  if (type === "array") {
    const rows = (value as unknown[]) ?? [];
    const itemKind = field.items ? kind(field.items) : undefined;
    if (itemKind === "string" && field.items?.enum) {
      const options = field.items.enum as string[];
      return (
        <fieldset {...{ disabled }}>
          <legend>{label}</legend>
          {options.map((option) => (
            <label key={option}>
              <input
                type="checkbox"
                checked={rows.includes(option)}
                onChange={(e) =>
                  onChange(
                    e.target.checked
                      ? options.filter((o) => rows.includes(o) || o === option)
                      : rows.filter((r) => r !== option),
                  )
                }
              />{" "}
              {option.replace(/_/g, " ")}{" "}
            </label>
          ))}
          {notes}
        </fieldset>
      );
    }
    const itemSchema = field.items as Schema;
    return (
      <div className="cx-config-list">
        {rows.map((row, index) => (
          <div key={index} className="cx-config-item">
            <p className="cx-config-item__title">Item {index + 1}</p>
            {itemKind === "object" ? (
              <Fields
                schema={itemSchema}
                value={(row as Value) ?? {}}
                path={`${path}[${index}]`}
                onChange={(next) =>
                  onChange(rows.map((r, i) => (i === index ? next : r)))
                }
                problems={problems}
                disabled={disabled}
                timeZone={timeZone}
              />
            ) : (
              <Field
                name={label}
                field={{ ...itemSchema, title: label }}
                value={row}
                path={`${path}[${index}]`}
                onChange={(next) =>
                  onChange(rows.map((r, i) => (i === index ? next : r)))
                }
                problems={problems}
                disabled={disabled}
                timeZone={timeZone}
              />
            )}
            <Button
              variant="secondary"
              disabled={disabled}
              onClick={() => onChange(rows.filter((_, i) => i !== index))}
            >
              Remove
            </Button>
          </div>
        ))}
        <Button
          variant="secondary"
          disabled={disabled || rows.length >= (field.maxItems ?? Infinity)}
          onClick={() =>
            onChange([
              ...rows,
              itemKind === "object"
                ? defaults(itemSchema)
                : (itemSchema.default ?? ""),
            ])
          }
        >
          Add item
        </Button>
        {notes}
      </div>
    );
  }

  if (type === "boolean")
    return (
      <label>
        <input
          type="checkbox"
          checked={value === true}
          onChange={(e) => onChange(e.target.checked)}
          {...aria}
        />{" "}
        {label}
        {notes}
      </label>
    );

  if (type === "integer" || type === "number")
    return (
      <label>
        {label}{" "}
        <input
          type="number"
          step={type === "integer" ? 1 : "any"}
          min={field.minimum}
          max={field.maximum}
          value={value === null || value === undefined ? "" : Number(value)}
          onChange={(e) =>
            onChange(
              e.target.value === ""
                ? nullable(field)
                  ? null
                  : ""
                : Number(e.target.value),
            )
          }
          {...aria}
        />
        {notes}
      </label>
    );

  if (type === "string") {
    if (field.enum)
      return (
        <label>
          {label}{" "}
          <select
            value={String(value ?? "")}
            onChange={(e) => onChange(e.target.value)}
            {...aria}
          >
            {(field.enum as string[]).map((option) => (
              <option key={option} value={option}>
                {option.replace(/_/g, " ")}
              </option>
            ))}
          </select>
          {notes}
        </label>
      );
    if (field.format === "date-time" || field["x-widget"] === "datetime")
      return (
        <label>
          {label}{" "}
          <input
            type="datetime-local"
            value={
              typeof value === "string" && value
                ? utcToZonedInput(value, timeZone)
                : ""
            }
            onChange={(e) =>
              onChange(
                e.target.value === ""
                  ? nullable(field)
                    ? null
                    : ""
                  : zonedToUtc(e.target.value, timeZone),
              )
            }
            {...aria}
          />{" "}
          <span className="cx-muted">({timeZone})</span>
          {notes}
        </label>
      );
    const props = {
      value: String(value ?? ""),
      maxLength: field.maxLength,
      required: field["x-nonblank"],
      onChange: (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
        onChange(e.target.value),
      ...aria,
    };
    return (
      <label>
        {label}{" "}
        {field["x-widget"] === "textarea" ? (
          <textarea {...props} />
        ) : (
          <input {...props} />
        )}
        {notes}
      </label>
    );
  }
  return <p role="alert">Unsupported configuration type.</p>;
}
