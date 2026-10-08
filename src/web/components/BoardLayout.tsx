import { useState } from "react";
import {
  useEntityPage,
  type EntityField,
  type EntityGroup,
  type EntityRow,
  type FilterNode,
} from "../lib/entityQuery";
import { showValue } from "../lib/entityFormat";
import { Button } from "./Button";

const STEP = 10;
const MOST = 100;

/**
 * The rows of a list as columns, one per value of a field (spec 006, PD-F006-B03-T01). The server
 * lists the buckets with their counts for the current filter and search; each column is the
 * ordinary query with the bucket's value as one more condition, so a column's count and its rows
 * cannot disagree. An enum field shows every value it can take, an empty column included, because
 * "nobody is rejected" is information; any other field shows the values that exist. Selection and
 * bulk actions stay in the list.
 */
export function BoardLayout({
  base,
  entity,
  label,
  field,
  groups,
  filter,
  search,
  sort,
  columnKeys,
  fields,
  rowLabel,
  onOpen,
  openId,
}: {
  base: string;
  entity: string;
  label: string;
  field: EntityField;
  groups: EntityGroup[];
  filter: FilterNode | null;
  search: string;
  sort: string;
  columnKeys: string[];
  fields: EntityField[];
  rowLabel?: (row: EntityRow) => string;
  onOpen?: (id: string) => void;
  openId?: string;
}) {
  const known = new Map(groups.map((g) => [String(g.key), g]));
  const columns: EntityGroup[] =
    field.type === "enum"
      ? [
          ...field.choices.map(
            (choice) =>
              known.get(choice) ?? {
                key: choice,
                label: choice,
                null: false,
                count: 0,
              },
          ),
          ...groups.filter((g) => g.null),
        ]
      : groups;
  if (columns.length === 0)
    return (
      <p className="cx-muted">
        Nothing to show: no {label.toLowerCase()} match.
      </p>
    );
  return (
    <div
      className="cx-board"
      role="group"
      aria-label={`${label} as a board by ${field.label}`}
    >
      {columns.map((column) => (
        <BoardColumn
          key={`${column.null ? "null" : String(column.key)}`}
          {...{ base, entity, label, field, column, filter, search, sort }}
          columnKeys={columnKeys}
          fields={fields}
          rowLabel={rowLabel}
          onOpen={onOpen}
          openId={openId}
        />
      ))}
    </div>
  );
}

function BoardColumn({
  base,
  entity,
  label,
  field,
  column,
  filter,
  search,
  sort,
  columnKeys,
  fields,
  rowLabel,
  onOpen,
  openId,
}: {
  base: string;
  entity: string;
  label: string;
  field: EntityField;
  column: EntityGroup;
  filter: FilterNode | null;
  search: string;
  sort: string;
  columnKeys: string[];
  fields: EntityField[];
  rowLabel?: (row: EntityRow) => string;
  onOpen?: (id: string) => void;
  openId?: string;
}) {
  const [limit, setLimit] = useState(STEP);
  const condition: FilterNode = column.null
    ? { field: field.key, op: "is_null", value: true }
    : { field: field.key, op: "eq", value: column.key };
  const page = useEntityPage(column.count > 0 ? base : null, entity, {
    filter: filter ? { and: [filter, condition] } : condition,
    search,
    sort,
    columns: columnKeys,
    limit,
  });
  const rows = page.data?.rows ?? [];
  // the first column shown is the name; the next two give a card its context
  const shown = columnKeys.length
    ? columnKeys
        .map((key) => fields.find((f) => f.key === key))
        .filter((f): f is EntityField => !!f)
    : fields.filter((f) => f.default);
  const context = shown.filter((f) => f.key !== field.key).slice(1, 3);
  const name = (row: EntityRow) =>
    rowLabel
      ? rowLabel(row)
      : showValue(
          shown.find((f) => f.key !== field.key) ?? shown[0],
          row[(shown.find((f) => f.key !== field.key) ?? shown[0]).key],
        );
  return (
    <section className="cx-board__column" aria-labelledby={undefined}>
      <h3 className="cx-board__head">
        {column.null ? "(none)" : column.label.replace(/_/g, " ")}{" "}
        <span className="cx-muted">
          · {column.count.toLocaleString("en-US")}
        </span>
      </h3>
      {column.count === 0 ? (
        <p className="cx-muted">None.</p>
      ) : page.error ? (
        <p role="alert">
          Could not load this column.{" "}
          <button type="button" onClick={() => void page.reload()}>
            Try again
          </button>
        </p>
      ) : page.data === null && rows.length === 0 ? (
        <p aria-busy="true" className="cx-muted">
          Loading…
        </p>
      ) : (
        <ul className="cx-board__list" aria-busy={page.data === null}>
          {rows.map((row) => (
            <li
              key={row.id}
              className="cx-board__item"
              aria-current={row.id === openId ? "true" : undefined}
            >
              {onOpen ? (
                <button
                  type="button"
                  className="cx-board__open"
                  onClick={() => onOpen(row.id)}
                >
                  {name(row)}
                </button>
              ) : (
                <span className="cx-board__open">{name(row)}</span>
              )}
              {context.map((f) => (
                <span key={f.key} className="cx-muted cx-board__fact">
                  {f.label}: {showValue(f, row[f.key])}
                </span>
              ))}
            </li>
          ))}
        </ul>
      )}
      {column.count > rows.length && rows.length > 0 && (
        <p className="cx-board__more">
          {limit < MOST ? (
            <Button
              size="sm"
              onClick={() => setLimit((now) => Math.min(MOST, now + STEP))}
            >
              Show more ({rows.length} of {column.count.toLocaleString("en-US")}
              )
            </Button>
          ) : (
            <span className="cx-muted">
              Showing the first {MOST}. Narrow the list with a filter or a
              search to see the rest.
            </span>
          )}
        </p>
      )}
    </section>
  );
}
