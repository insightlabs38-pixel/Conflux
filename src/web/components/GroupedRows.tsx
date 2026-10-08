import { useId, useState } from "react";
import {
  useEntityPage,
  type EntityBucket,
  type EntityGroup,
  type EntityRow,
  type FilterNode,
} from "../lib/entityQuery";
import { Icon } from "./Icon";
import { DataGrid, type GridColumn, type GridDensity } from "./DataGrid";

/**
 * Rows grouped by a field, and by a second inside it (spec 006, PD-F006-B02-T08). The server lists
 * the buckets with their counts for the current filter and search; a bucket is opened with the
 * ordinary query and the bucket's own value as one more condition, so there is one way to read rows
 * and the counts and the rows can never disagree about what a bucket holds. Empty values form a
 * last bucket, "(none)". Selection and bulk actions belong to the flat list: ungroup to use them.
 */
export function GroupedRows({
  base,
  entity,
  label,
  groupLabel,
  subgroupLabel,
  groupField,
  subgroupField,
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
  groupLabel: string;
  subgroupLabel?: string;
  groupField: string;
  subgroupField?: string;
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
  const [open, setOpen] = useState<Set<string>>(
    () => new Set(groups.length === 1 ? ["0"] : []),
  );
  const id = useId();
  const toggle = (path: string) =>
    setOpen((now) => {
      const next = new Set(now);
      if (next.has(path)) next.delete(path);
      else next.add(path);
      return next;
    });
  const is = (field: string, bucket: EntityBucket): FilterNode =>
    bucket.null
      ? { field, op: "is_null", value: true }
      : { field, op: "eq", value: bucket.key };
  const within = (...conditions: FilterNode[]): FilterNode | null => {
    const all = [...(filter ? [filter] : []), ...conditions];
    return all.length === 0 ? null : all.length === 1 ? all[0] : { and: all };
  };
  const body = (path: string, conditions: FilterNode[]) => (
    <BucketRows
      key={path}
      base={base}
      entity={entity}
      label={label}
      filter={within(...conditions)}
      search={search}
      sort={sort}
      columnKeys={columnKeys}
      columns={columns}
      density={density}
      rowLabel={rowLabel}
      actions={actions}
    />
  );
  if (groups.length === 0)
    return (
      <p className="cx-muted">
        Nothing to group: no {label.toLowerCase()} match.
      </p>
    );
  return (
    <div
      className="cx-groups"
      role="group"
      aria-label={`${label} grouped by ${groupLabel}${subgroupLabel ? `, then ${subgroupLabel}` : ""}`}
    >
      <ul>
        {groups.map((group, index) => {
          const path = String(index);
          const expanded = open.has(path);
          return (
            <li key={path}>
              <button
                type="button"
                className="cx-groups__head"
                aria-expanded={expanded}
                aria-controls={`${id}-${path}`}
                onClick={() => toggle(path)}
              >
                <Icon name={expanded ? "chevron-down" : "chevron-right"} />
                {groupLabel}: {group.label}{" "}
                <span className="cx-muted">
                  · {group.count.toLocaleString("en-US")}
                </span>
              </button>
              {expanded && (
                <div id={`${id}-${path}`} className="cx-groups__body">
                  {group.subgroups && subgroupField ? (
                    <ul>
                      {group.subgroups.map((sub, subIndex) => {
                        const subPath = `${path}.${subIndex}`;
                        const subOpen = open.has(subPath);
                        return (
                          <li key={subPath}>
                            <button
                              type="button"
                              className="cx-groups__head cx-groups__head--sub"
                              aria-expanded={subOpen}
                              aria-controls={`${id}-${subPath}`}
                              onClick={() => toggle(subPath)}
                            >
                              <Icon
                                name={
                                  subOpen ? "chevron-down" : "chevron-right"
                                }
                              />
                              {subgroupLabel}: {sub.label}{" "}
                              <span className="cx-muted">
                                · {sub.count.toLocaleString("en-US")}
                              </span>
                            </button>
                            {subOpen && (
                              <div
                                id={`${id}-${subPath}`}
                                className="cx-groups__body"
                              >
                                {body(subPath, [
                                  is(groupField, group),
                                  is(subgroupField, sub),
                                ])}
                              </div>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  ) : (
                    body(path, [is(groupField, group)])
                  )}
                </div>
              )}
            </li>
          );
        })}
      </ul>
      {truncated && (
        <p className="cx-muted">
          Showing the first {groups.length} groups. Narrow the list with a
          filter or a search to see the rest.
        </p>
      )}
    </div>
  );
}

/** The rows of one bucket: the ordinary query with the bucket as a condition, paged like the list. */
export function BucketRows({
  base,
  entity,
  label,
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
  filter: FilterNode | null;
  search: string;
  sort: string;
  columnKeys: string[];
  columns: GridColumn<EntityRow>[];
  density: GridDensity;
  rowLabel?: (row: EntityRow) => string;
  actions?: (row: EntityRow) => React.ReactNode;
}) {
  const [offset, setOffset] = useState(0);
  const limit = 25;
  const page = useEntityPage(base, entity, {
    filter,
    search,
    sort,
    columns: columnKeys,
    limit,
    offset,
  });
  const data = page.data;
  return (
    <DataGrid<EntityRow>
      label={label}
      columns={columns}
      rows={data?.rows ?? []}
      status={
        page.error
          ? {
              kind: "error",
              message: page.error.message,
              onRetry: () => void page.reload(),
            }
          : data === null
            ? { kind: "loading" }
            : { kind: "ready" }
      }
      total={data?.total}
      limit={limit}
      offset={offset}
      onPage={setOffset}
      density={density}
      rowLabel={rowLabel}
      actions={actions}
    />
  );
}
