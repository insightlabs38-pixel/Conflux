import { useRef, type KeyboardEvent, type ReactNode } from "react";
import { Button } from "./Button";
import { Icon } from "./Icon";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { DeniedState } from "./DeniedState";
import { LoadingState, SkeletonRows } from "./LoadingState";

/**
 * The dense data grid (PD-F002-B01-T03). A controlled, server-driven table: sort, paging, the
 * visible columns and the density are the caller's state; the grid renders only the rows it is
 * given, never sorts or filters a set in the browser, and selection is the ids the server returned.
 *
 * Semantics: a native table (caption, `aria-sort` on sortable headers, sticky header), row
 * selection through labelled checkboxes that Arrow keys move between, a stacked layout on narrow
 * screens (each cell carries its column label), and distinct loading, empty, filtered-empty, error
 * and denied states.
 */
export type GridColumn<Row> = {
  key: string;
  label: string;
  sortable?: boolean;
  align?: "start" | "end";
  render?: (row: Row) => ReactNode;
};
export type SortState = { key: string; descending: boolean } | null;
export type GridDensity = "compact" | "comfortable";
export type GridStatus =
  | { kind: "ready" }
  | { kind: "loading" }
  | { kind: "error"; message: string; onRetry?: () => void }
  | { kind: "denied"; message?: string };

export function DataGrid<Row extends { id: string }>({
  label,
  columns,
  rows,
  status = { kind: "ready" },
  sort,
  onSort,
  total,
  limit,
  offset,
  onPage,
  density = "comfortable",
  selected,
  onSelect,
  rowLabel,
  actions,
  empty,
  filtered = false,
  onClearFilter,
}: {
  label: string;
  columns: GridColumn<Row>[];
  rows: Row[];
  status?: GridStatus;
  sort?: SortState;
  onSort?: (next: SortState) => void;
  total?: number;
  limit?: number;
  offset?: number;
  onPage?: (offset: number) => void;
  density?: GridDensity;
  selected?: ReadonlySet<string>;
  onSelect?: (ids: Set<string>) => void;
  /** Accessible name of a row's checkbox, for example the applicant's name. */
  rowLabel?: (row: Row) => string;
  /** A column of per-row actions, rendered last. */
  actions?: (row: Row) => ReactNode;
  empty?: ReactNode;
  /** A filter is applied: "no rows" then means "no rows match". */
  filtered?: boolean;
  onClearFilter?: () => void;
}) {
  const body = useRef<HTMLTableSectionElement>(null);

  // The columns are known, so the grid keeps its header and shows the shape of the rows to come.
  if (status.kind === "loading")
    return (
      <div className={`cx-grid-wrap cx-grid-wrap--${density}`} aria-busy="true">
        <LoadingState label={`Loading ${label}…`} />
        <div className="cx-table-region cx-datagrid" aria-hidden="true">
          <table className="cx-table cx-datagrid__table">
            <thead>
              <tr>
                {onSelect && <th scope="col" className="cx-datagrid__select" />}
                {columns.map((column) => (
                  <th key={column.key} scope="col">
                    {column.label}
                  </th>
                ))}
              </tr>
            </thead>
          </table>
          <SkeletonRows columns={columns.length + (onSelect ? 1 : 0)} />
        </div>
      </div>
    );
  if (status.kind === "denied") return <DeniedState message={status.message} />;
  if (status.kind === "error")
    return (
      <ErrorState
        kind="read"
        message={status.message}
        onRetry={status.onRetry}
      />
    );

  if (rows.length === 0)
    return filtered ? (
      <EmptyState
        title="No rows match this filter"
        why="Nothing in this list meets the conditions that are set."
        next={
          onClearFilter && (
            <Button variant="secondary" onClick={onClearFilter}>
              Clear filter
            </Button>
          )
        }
      />
    ) : (
      <EmptyState
        title={`No ${label.toLowerCase()} yet`}
        why="Nothing has been added to this list yet."
      >
        {empty}
      </EmptyState>
    );

  const selectable = Boolean(onSelect);
  const chosen = selected ?? new Set<string>();
  const allOnPage = rows.every((row) => chosen.has(row.id));
  const someOnPage = rows.some((row) => chosen.has(row.id));

  function toggle(id: string, on: boolean) {
    const next = new Set(chosen);
    if (on) next.add(id);
    else next.delete(id);
    onSelect?.(next);
  }
  function togglePage(on: boolean) {
    const next = new Set(chosen);
    for (const row of rows) {
      if (on) next.add(row.id);
      else next.delete(row.id);
    }
    onSelect?.(next);
  }
  function move(event: KeyboardEvent<HTMLInputElement>, index: number) {
    const boxes = [
      ...(body.current?.querySelectorAll<HTMLInputElement>(
        "input[data-row-select]",
      ) ?? []),
    ];
    const target =
      event.key === "ArrowDown"
        ? index + 1
        : event.key === "ArrowUp"
          ? index - 1
          : event.key === "Home"
            ? 0
            : event.key === "End"
              ? boxes.length - 1
              : event.key === "PageDown"
                ? index + 10
                : event.key === "PageUp"
                  ? index - 10
                  : null;
    if (target === null) return;
    event.preventDefault();
    boxes[Math.max(0, Math.min(boxes.length - 1, target))]?.focus();
  }

  const first = offset !== undefined ? offset + 1 : 1;
  const last = offset !== undefined ? offset + rows.length : rows.length;
  const paged = total !== undefined && limit !== undefined && onPage;

  return (
    <div className={`cx-grid-wrap cx-grid-wrap--${density}`}>
      <div
        className="cx-table-region cx-datagrid"
        role="region"
        aria-label={label}
        tabIndex={0}
      >
        <table className="cx-table cx-datagrid__table">
          <caption className="cx-visually-hidden">
            {label}
            {total !== undefined ? `, ${total} in all` : ""}
          </caption>
          <thead>
            <tr>
              {selectable && (
                <th scope="col" className="cx-datagrid__select">
                  <input
                    type="checkbox"
                    aria-label={`Select all ${label.toLowerCase()} on this page`}
                    checked={allOnPage}
                    ref={(el) => {
                      if (el) el.indeterminate = someOnPage && !allOnPage;
                    }}
                    onChange={(e) => togglePage(e.target.checked)}
                  />
                </th>
              )}
              {columns.map((column) => {
                const active = sort?.key === column.key;
                return (
                  <th
                    key={column.key}
                    scope="col"
                    aria-sort={
                      column.sortable
                        ? active
                          ? sort!.descending
                            ? "descending"
                            : "ascending"
                          : "none"
                        : undefined
                    }
                    className={
                      column.align === "end" ? "cx-datagrid__end" : undefined
                    }
                  >
                    {column.sortable && onSort ? (
                      <button
                        type="button"
                        className="cx-datagrid__sort"
                        onClick={() =>
                          onSort(
                            !active
                              ? { key: column.key, descending: false }
                              : !sort!.descending
                                ? { key: column.key, descending: true }
                                : null,
                          )
                        }
                      >
                        {column.label}
                        {active && (
                          <Icon
                            name={
                              sort!.descending ? "chevron-down" : "chevron-up"
                            }
                          />
                        )}
                        <span className="cx-visually-hidden">
                          {active
                            ? sort!.descending
                              ? ", sorted descending; activate to clear"
                              : ", sorted ascending; activate to sort descending"
                            : ", activate to sort ascending"}
                        </span>
                      </button>
                    ) : (
                      column.label
                    )}
                  </th>
                );
              })}
              {actions && (
                <th scope="col">
                  <span className="cx-visually-hidden">Actions</span>
                </th>
              )}
            </tr>
          </thead>
          <tbody ref={body}>
            {rows.map((row, index) => (
              <tr
                key={row.id}
                aria-selected={selectable ? chosen.has(row.id) : undefined}
              >
                {selectable && (
                  <td className="cx-datagrid__select" data-label="Select">
                    <input
                      type="checkbox"
                      data-row-select=""
                      aria-label={`Select ${rowLabel ? rowLabel(row) : `row ${first + index}`}`}
                      checked={chosen.has(row.id)}
                      onChange={(e) => toggle(row.id, e.target.checked)}
                      onKeyDown={(e) => move(e, index)}
                    />
                  </td>
                )}
                {columns.map((column) => (
                  <td
                    key={column.key}
                    data-label={column.label}
                    className={
                      column.align === "end" ? "cx-datagrid__end" : undefined
                    }
                  >
                    {column.render
                      ? column.render(row)
                      : String(
                          (row as Record<string, unknown>)[column.key] ?? "—",
                        )}
                  </td>
                ))}
                {actions && (
                  <td data-label="Actions" className="cx-datagrid__actions">
                    {actions(row)}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="cx-datagrid__footer">
        <span role="status">
          {total !== undefined
            ? `Showing ${first}–${last} of ${total}`
            : `${rows.length} rows`}
          {selectable && chosen.size > 0 ? ` · ${chosen.size} selected` : ""}
        </span>
        {paged && (
          <nav aria-label={`${label} pages`} className="cx-datagrid__pages">
            <Button
              variant="secondary"
              disabled={(offset ?? 0) <= 0}
              onClick={() => onPage(Math.max(0, (offset ?? 0) - limit))}
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              disabled={(offset ?? 0) + limit >= total}
              onClick={() => onPage((offset ?? 0) + limit)}
            >
              Next
            </Button>
          </nav>
        )}
      </div>
    </div>
  );
}
