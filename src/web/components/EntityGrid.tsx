import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  entityBase,
  useEntityCatalogue,
  useEntityPage,
  type EntityField,
  type EntityRow,
  type FilterNode,
} from "../lib/entityQuery";
import { ApiError } from "../lib/api";
import type { SavedView, ViewDefinition } from "../lib/savedViews";
import {
  DataGrid,
  type GridColumn,
  type GridDensity,
  type SortState,
} from "./DataGrid";
import { FilterBuilder } from "./FilterBuilder";
import { ViewBar } from "./ViewBar";
import { Inspector } from "./Inspector";
import { useUrlParam } from "../lib/urlState";

const PAGE_SIZE = 25;

function show(field: EntityField, value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (field.type === "bool") return value ? "Yes" : "No";
  if (field.type === "date" && typeof value === "string")
    return (
      new Date(value).toLocaleString("en-US", {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "UTC",
      }) + " UTC"
    );
  return String(value).replace(/_/g, " ");
}

function sortState(sort: string): SortState {
  const first = sort.split(",")[0]?.trim();
  if (!first) return null;
  return first.startsWith("-")
    ? { key: first.slice(1), descending: true }
    : { key: first, descending: false };
}

/**
 * The standard list of an entity: the data grid over the universal entity query, with a filter
 * builder, saved views, a column picker and density. Everything the server decides (what rows this
 * person may see, what can be filtered or sorted) comes from the catalogue and the page; this only
 * arranges it. A feature adds per-row actions and cell renderers, not its own list plumbing.
 */
export function EntityGrid({
  workspaceId,
  eventId,
  entity,
  label,
  rowLabel,
  actions,
  renderers = {},
  selectable = false,
  onSelect,
  refreshToken = 0,
  empty,
  inspect = true,
}: {
  workspaceId: string;
  eventId: string;
  entity: string;
  /** Plural noun for the list, for example "Applications". */
  label: string;
  rowLabel?: (row: EntityRow) => string;
  actions?: (row: EntityRow) => ReactNode;
  renderers?: Record<string, (row: EntityRow) => ReactNode>;
  selectable?: boolean;
  onSelect?: (ids: Set<string>) => void;
  /** Change it to reload the page (after a row action). */
  refreshToken?: number;
  empty?: ReactNode;
  /** Offer a Details button per row that opens the record beside the list (on by default). */
  inspect?: boolean;
}) {
  const base = entityBase(workspaceId, eventId);
  const catalogue = useEntityCatalogue(base);
  const description = catalogue.data?.find((e) => e.key === entity) ?? null;

  const [filter, setFilter] = useState<FilterNode | null>(null);
  const [sort, setSort] = useState("");
  const [visible, setVisible] = useState<string[]>([]);
  const [density, setDensity] = useState<GridDensity>("comfortable");
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  // The record open in the inspector is panel state: a public id in the URL (`row_<entity>`), replaced
  // rather than pushed, so Back leaves the page instead of stepping through every record looked at.
  const [openId, setOpenId] = useUrlParam(`row_${entity}`);

  const fields = description?.fields ?? [];
  const shown = useMemo(
    () =>
      visible.length > 0
        ? fields.filter((f) => visible.includes(f.key))
        : fields.filter((f) => f.default),
    [fields, visible],
  );
  const page = useEntityPage(description ? base : null, entity, {
    filter,
    sort,
    columns: visible,
    limit: PAGE_SIZE,
    offset,
  });

  // The inspector shows every field, not only the columns the list chose: the same page again with
  // all of them (the server still decides what this person may see). Read only while one is open.
  const detail = useEntityPage(
    description && inspect && openId ? base : null,
    entity,
    {
      filter,
      sort,
      columns: fields.map((f) => f.key),
      limit: PAGE_SIZE,
      offset,
    },
  );

  // While the next page loads, keep showing the last one (marked busy) instead of blanking the list.
  const lastPage = useRef(page.data);
  if (page.data) lastPage.current = page.data;
  const shownPage = page.data ?? lastPage.current;

  const first = useRef(true);
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    setSelected(new Set()); // rows may be gone or changed: an earlier selection is stale
    void page.reload();
    // Only a change of the token reloads; `page` identity changes on every render.
  }, [refreshToken]);

  const restart = () => {
    setOffset(0);
    setSelected(new Set());
    onSelect?.(new Set());
  };
  const apply = useCallback((view: SavedView | null) => {
    const query = view?.query;
    setFilter(query?.filter ?? null);
    setSort(query?.sort ?? "");
    setVisible(query?.columns ?? []);
    setDensity(query?.density ?? "comfortable");
    setOffset(0);
    setSelected(new Set());
  }, []);
  const current: ViewDefinition = { filter, sort, columns: visible, density };

  const columns: GridColumn<EntityRow>[] = shown.map((field) => ({
    key: field.key,
    label: field.label,
    sortable: field.sortable,
    render: renderers[field.key] ?? ((row) => show(field, row[field.key])),
  }));

  const denied =
    catalogue.data !== null && description === null
      ? "You do not have access to this list."
      : null;
  const failure = catalogue.error ?? page.error;
  const status = denied
    ? ({ kind: "denied", message: denied } as const)
    : failure
      ? ({
          kind: "error",
          message:
            failure instanceof ApiError
              ? failure.message
              : "Could not load the list.",
          onRetry: () => {
            void catalogue.reload();
            void page.reload();
          },
        } as const)
      : shownPage === null || description === null
        ? ({ kind: "loading" } as const)
        : ({ kind: "ready" } as const);

  const active = filter ? 1 : 0;
  const rows = shownPage?.rows ?? [];
  const at = openId ? rows.findIndex((row) => row.id === openId) : -1;
  const opened = at >= 0 ? rows[at] : null;
  const closeInspector = () => {
    const id = openId;
    setOpenId("", { replace: true });
    // the control that opened it gets focus back
    requestAnimationFrame(() =>
      document
        .querySelector<HTMLElement>(
          `[data-entity="${entity}"] [data-inspect="${id}"]`,
        )
        ?.focus(),
    );
  };
  const inspectAction = inspect
    ? (row: EntityRow) => (
        <>
          {actions?.(row)}
          <button
            type="button"
            className="cx-inspect"
            data-inspect={row.id}
            aria-expanded={row.id === openId}
            aria-label={`Details for ${rowLabel ? rowLabel(row) : (row[shown[0]?.key] ?? "row")}`}
            onClick={() => setOpenId(row.id, { replace: true })}
          >
            Details
          </button>
        </>
      )
    : actions;
  const full = opened
    ? (detail.data?.rows.find((r) => r.id === openId) ?? opened)
    : null;
  return (
    <div
      className={`cx-entity-grid${openId && inspect ? " cx-entity-grid--inspecting" : ""}`}
      data-entity={entity}
      aria-busy={page.data === null && shownPage !== null}
    >
      <div className="cx-entity-grid__main">
        <details className="cx-entity-grid__tools">
          <summary>
            Filter, views and columns
            {active ? " (filtered)" : ""}
          </summary>
          <ViewBar
            workspaceId={workspaceId}
            eventId={eventId}
            entity={entity}
            current={current}
            onApply={apply}
          />
          <FilterBuilder
            fields={fields}
            value={filter}
            onChange={(next) => {
              setFilter(next);
              restart();
            }}
          />
          <fieldset>
            <legend>Columns</legend>
            {fields.map((field) => (
              <label key={field.key}>
                <input
                  type="checkbox"
                  checked={shown.some((f) => f.key === field.key)}
                  disabled={shown.length === 1 && shown[0].key === field.key}
                  onChange={(e) => {
                    const keys = new Set(shown.map((f) => f.key));
                    if (e.target.checked) keys.add(field.key);
                    else keys.delete(field.key);
                    setVisible(
                      fields.filter((f) => keys.has(f.key)).map((f) => f.key),
                    );
                  }}
                />{" "}
                {field.label}
              </label>
            ))}
            <button type="button" onClick={() => setVisible([])}>
              Reset columns
            </button>
          </fieldset>
          <label>
            Sort by{" "}
            <select
              value={sort}
              onChange={(e) => {
                setSort(e.target.value);
                restart();
              }}
            >
              <option value="">Default order</option>
              {fields
                .filter((f) => f.sortable)
                .flatMap((f) => [
                  <option key={f.key} value={f.key}>
                    {f.label}, ascending
                  </option>,
                  <option key={`-${f.key}`} value={`-${f.key}`}>
                    {f.label}, descending
                  </option>,
                ])}
            </select>
          </label>
          <div role="group" aria-label="Density">
            {(["comfortable", "compact"] as const).map((value) => (
              <button
                key={value}
                type="button"
                aria-pressed={density === value}
                onClick={() => setDensity(value)}
              >
                {value === "compact" ? "Compact" : "Comfortable"}
              </button>
            ))}
          </div>
        </details>
        <DataGrid<EntityRow>
          label={label}
          columns={columns}
          rows={shownPage?.rows ?? []}
          status={status}
          sort={sortState(sort)}
          onSort={(next) => {
            setSort(next ? `${next.descending ? "-" : ""}${next.key}` : "");
            restart();
          }}
          total={shownPage?.total}
          limit={PAGE_SIZE}
          offset={offset}
          onPage={setOffset}
          density={density}
          selected={selectable ? selected : undefined}
          onSelect={
            selectable
              ? (ids) => {
                  setSelected(ids);
                  onSelect?.(ids);
                }
              : undefined
          }
          rowLabel={rowLabel}
          actions={inspectAction}
          highlightedId={inspect ? openId : undefined}
          empty={empty}
          filtered={filter !== null}
          onClearFilter={() => {
            setFilter(null);
            restart();
          }}
        />
      </div>
      {inspect && openId && shownPage !== null && (
        <Inspector
          title={String(
            full?.[shown[0]?.key ?? ""] ??
              (opened ? "Record" : "Record not on this page"),
          )}
          position={
            opened
              ? `${(offset ?? 0) + at + 1} of ${shownPage.total}`
              : undefined
          }
          onClose={closeInspector}
          onPrevious={
            at > 0
              ? () => setOpenId(rows[at - 1].id, { replace: true })
              : undefined
          }
          onNext={
            at >= 0 && at < rows.length - 1
              ? () => setOpenId(rows[at + 1].id, { replace: true })
              : undefined
          }
        >
          {!opened ? (
            <p role="status">
              This record is not on the current page of the list.{" "}
              <button type="button" onClick={closeInspector}>
                Close
              </button>
            </p>
          ) : (
            <>
              {detail.error && (
                <p role="alert">
                  Some fields could not be loaded.{" "}
                  <button type="button" onClick={() => void detail.reload()}>
                    Try again
                  </button>
                </p>
              )}
              <dl className="cx-inspector__fields">
                {fields.map((field) => (
                  <div key={field.key}>
                    <dt>{field.label}</dt>
                    <dd>{show(field, (full ?? opened)[field.key])}</dd>
                  </div>
                ))}
              </dl>
            </>
          )}
        </Inspector>
      )}
    </div>
  );
}
