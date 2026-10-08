import { useState } from "react";
import {
  type EntityBucket,
  type EntityGroup,
  type EntityRow,
  type FilterNode,
} from "../lib/entityQuery";
import { BucketRows } from "./GroupedRows";
import type { GridColumn, GridDensity } from "./DataGrid";

const condition = (field: string, bucket: EntityBucket): FilterNode =>
  bucket.null
    ? { field, op: "is_null", value: true }
    : { field, op: "eq", value: bucket.key };

/**
 * Counts at the crossing of two fields (spec 006, PD-F006-B03-T01): rows are the first field's
 * values, columns the second's, each cell the number of rows with both, from the same filtered
 * query as the list. It is a real table (row and column headers, totals), so it is its own text
 * alternative; a cell with rows opens them beneath through the ordinary query with the two values
 * as conditions. Empty values are the last row and column, "(none)".
 */
export function MatrixLayout({
  base,
  entity,
  label,
  rowLabelText,
  columnLabelText,
  rowField,
  columnField,
  groups,
  truncated,
  filter,
  search,
  sort,
  columnKeys,
  columns,
  density,
  rowLabel,
  actions,
}: {
  base: string;
  entity: string;
  label: string;
  rowLabelText: string;
  columnLabelText: string;
  rowField: string;
  columnField: string;
  groups: EntityGroup[];
  truncated: boolean;
  filter: FilterNode | null;
  search: string;
  sort: string;
  columnKeys: string[];
  columns: GridColumn<EntityRow>[];
  density: GridDensity;
  rowLabel?: (row: EntityRow) => string;
  actions?: (row: EntityRow) => React.ReactNode;
}) {
  const [open, setOpen] = useState<{ row: number; col: number } | null>(null);
  if (groups.length === 0)
    return (
      <p className="cx-muted">
        Nothing to show: no {label.toLowerCase()} match.
      </p>
    );
  // the columns are every second-field value that occurs, in the order the server gave them
  const across: EntityBucket[] = [];
  for (const group of groups)
    for (const sub of group.subgroups ?? [])
      if (!across.some((c) => c.null === sub.null && c.key === sub.key))
        across.push(sub);
  across.sort((a, b) => Number(a.null) - Number(b.null));
  const cell = (group: EntityGroup, column: EntityBucket) =>
    group.subgroups?.find((s) => s.null === column.null && s.key === column.key)
      ?.count ?? 0;
  const columnTotal = (column: EntityBucket) =>
    groups.reduce((sum, group) => sum + cell(group, column), 0);
  const grand = groups.reduce((sum, group) => sum + group.count, 0);
  const picked =
    open && groups[open.row] && across[open.col]
      ? { group: groups[open.row], column: across[open.col] }
      : null;
  return (
    <div className="cx-matrix">
      <div
        className="cx-scroll-region"
        tabIndex={0}
        role="region"
        aria-label={`${label} by ${rowLabelText} and ${columnLabelText}`}
      >
        <table className="cx-matrix__table">
          <caption>
            {label}: {rowLabelText} by {columnLabelText}. Each number is a count
            of rows with both.
          </caption>
          <thead>
            <tr>
              <th scope="col">{rowLabelText}</th>
              {across.map((column, i) => (
                <th scope="col" key={i} className="cx-matrix__num">
                  {column.label}
                </th>
              ))}
              <th scope="col" className="cx-matrix__num">
                Total
              </th>
            </tr>
          </thead>
          <tbody>
            {groups.map((group, r) => (
              <tr key={r}>
                <th scope="row">{group.label}</th>
                {across.map((column, c) => {
                  const count = cell(group, column);
                  const isOpen = open?.row === r && open?.col === c;
                  return (
                    <td key={c} className="cx-matrix__num">
                      {count === 0 ? (
                        <span className="cx-muted">0</span>
                      ) : (
                        <button
                          type="button"
                          className="cx-matrix__cell"
                          aria-expanded={isOpen}
                          aria-label={`${group.label}, ${column.label}: ${count.toLocaleString("en-US")}. ${isOpen ? "Hide" : "Show"} these rows`}
                          onClick={() =>
                            setOpen(isOpen ? null : { row: r, col: c })
                          }
                        >
                          {count.toLocaleString("en-US")}
                        </button>
                      )}
                    </td>
                  );
                })}
                <td className="cx-matrix__num">
                  <strong>{group.count.toLocaleString("en-US")}</strong>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <th scope="row">Total</th>
              {across.map((column, c) => (
                <td key={c} className="cx-matrix__num">
                  <strong>{columnTotal(column).toLocaleString("en-US")}</strong>
                </td>
              ))}
              <td className="cx-matrix__num">
                <strong>{grand.toLocaleString("en-US")}</strong>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
      {truncated && (
        <p className="cx-muted">
          Showing the first {groups.length} {rowLabelText.toLowerCase()} values.
          Narrow the list with a filter or a search to see the rest.
        </p>
      )}
      {picked && (
        <section
          aria-label={`${picked.group.label}, ${picked.column.label}`}
          className="cx-matrix__rows"
        >
          <h3 className="cx-matrix__title">
            {rowLabelText}: {picked.group.label} · {columnLabelText}:{" "}
            {picked.column.label}
          </h3>
          <BucketRows
            key={`${open?.row}.${open?.col}`}
            base={base}
            entity={entity}
            label={label}
            filter={{
              and: [
                ...(filter ? [filter] : []),
                condition(rowField, picked.group),
                condition(columnField, picked.column),
              ],
            }}
            search={search}
            sort={sort}
            columnKeys={columnKeys}
            columns={columns}
            density={density}
            rowLabel={rowLabel}
            actions={actions}
          />
        </section>
      )}
    </div>
  );
}
