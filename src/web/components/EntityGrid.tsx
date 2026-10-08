import {
  useCallback,
  useEffect,
  useId,
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
  describeSort,
  MAX_SORT_KEYS,
  type SortState,
} from "./DataGrid";
import { FilterBuilder } from "./FilterBuilder";
import { describeFilter, filterProblems } from "../lib/entityQuery";
import { ViewBar } from "./ViewBar";
import { Inspector } from "./Inspector";
import { useUrlParam } from "../lib/urlState";
import { useMe } from "../hooks/useMe";
import { announce } from "../lib/shellNotice";
import { useConnectionStatus, useRealtime } from "../hooks/useRealtime";
import { describeHealth } from "../lib/liveOps";
import { liveOpsTopic, LIVE_OPS_INTERVAL_MS } from "../lib/realtime";
import { LiveStatus } from "./LiveStatus";
import {
  countOf,
  publishSelection,
  type SelectionCommand,
} from "../lib/selection";
import {
  columnPreference,
  setColumnPreference,
  setLiveOperations,
  useLiveOperations,
} from "../lib/shellPreferences";

const PAGE_SIZE = 25;
/** The most rows one selection holds: a page is never larger, and the bulk planner takes no more per operation. */
const MAX_SELECTION = 100;

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
  return sort
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) =>
      part.startsWith("-")
        ? { key: part.slice(1), descending: true }
        : { key: part, descending: false },
    );
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
  selectionCommands,
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
  /**
   * Commands for the palette that apply to the selected rows (their ids), next to the ones every
   * list offers. They start the list's own workflow; they do not change anything by themselves.
   */
  selectionCommands?: (ids: string[]) => SelectionCommand[];
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
  // Search text is typed text, so it is transient (never in the URL or storage; spec 006 B01): a
  // saved view is how it is kept or shared. `searchText` is the box, `search` what is asked.
  const [searchText, setSearchText] = useState("");
  const [search, setSearch] = useState("");
  const typed = searchText.trim().replace(/\s+/g, " ");
  const tooShort =
    typed.length > 0 && typed.split(" ").some((w) => w.length < 2);
  useEffect(() => {
    if (tooShort) return;
    const timer = setTimeout(() => setSearch(typed), 300);
    return () => clearTimeout(timer);
  }, [typed, tooShort]);
  // The list's sort and page are panel state (lib/urlState.ts): fixed names, never typed text, so a
  // link reproduces the list exactly. Changing the sort goes back to the first page.
  const [sortParam, setSortParam] = useUrlParam(`sort_${entity}`, {
    clears: [`page_${entity}`],
  });
  const [pageParam, setPageParam] = useUrlParam(`page_${entity}`);
  // Columns: a saved view's own win while it is open, otherwise the person's remembered choice for
  // this list on this device (shellPreferences), otherwise the list's defaults. Only a choice made in
  // the picker is remembered; a view's columns never overwrite it.
  const user = useMe().data?.public_id ?? "";
  const [visible, setVisible] = useState<string[]>(() =>
    columnPreference(user, workspaceId, entity),
  );
  const remembered = useRef(user);
  useEffect(() => {
    // the person arrives after the first render: adopt their choice once, unless one was already made
    if (user && remembered.current !== user) {
      remembered.current = user;
      setVisible((now) =>
        now.length ? now : columnPreference(user, workspaceId, entity),
      );
    }
  }, [user, workspaceId, entity]);
  // Live operations mode (a device choice): the list asks the server again on every hint and shows
  // the connection's health and the data's age. Offline, actions that need fresh data wait.
  const live = useLiveOperations(user);
  const opsTopic = liveOpsTopic(workspaceId, eventId, entity);
  const health = describeHealth(
    useConnectionStatus(live ? opsTopic : null),
    LIVE_OPS_INTERVAL_MS / 1000,
  );
  const chooseColumns = (keys: string[]) => {
    setVisible(keys);
    setColumnPreference(user, workspaceId, entity, keys);
  };
  const [density, setDensity] = useState<GridDensity>("comfortable");
  const requestedPage = /^[0-9]{1,6}$/.test(pageParam) ? Number(pageParam) : 1;
  const [selected, setSelected] = useState<Set<string>>(new Set());
  // The record open in the inspector is panel state: a public id in the URL (`row_<entity>`), replaced
  // rather than pushed, so Back leaves the page instead of stepping through every record looked at.
  const [openId, setOpenId] = useUrlParam(`row_${entity}`);

  const fields = description?.fields ?? [];
  // the URL is a request: only a field this list can sort by is honoured, anything else is ignored
  const sortable = new Set(fields.filter((f) => f.sortable).map((f) => f.key));
  // In the address the keys are joined with ":" (a comma is not an id-like character, lib/urlState.ts);
  // the server takes the same keys as a comma list. Each key is checked on its own.
  const sort = sortParam
    .split(":")
    .filter((key) => sortable.has(key.replace(/^-/, "")))
    .slice(0, MAX_SORT_KEYS)
    .join(",");
  const setSort = (value: string) =>
    setSortParam(value.split(",").filter(Boolean).join(":"), { replace: true });
  const offset = requestedPage > 1 ? (requestedPage - 1) * PAGE_SIZE : 0;
  const setOffset = (next: number) =>
    setPageParam(next > 0 ? String(Math.floor(next / PAGE_SIZE) + 1) : "", {
      replace: true,
    });
  // a remembered key the list no longer has is dropped; if none remain the defaults show
  const known = useMemo(
    () => visible.filter((k) => fields.some((f) => f.key === k)),
    [fields, visible],
  );
  const shown = useMemo(
    () =>
      known.length > 0
        ? fields.filter((f) => known.includes(f.key))
        : fields.filter((f) => f.default),
    [fields, known],
  );
  // The filter is applied a moment after the last change, so a half-typed date or number is not
  // asked of the server on every keystroke (the box shows what is typed at once).
  const [queryFilter, setQueryFilter] = useState<FilterNode | null>(filter);
  useEffect(() => {
    const timer = setTimeout(() => setQueryFilter(filter), 400);
    return () => clearTimeout(timer);
  }, [filter]);
  const page = useEntityPage(description ? base : null, entity, {
    filter: queryFilter,
    search,
    sort,
    columns: known,
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
  // the age of what is on screen: a failed refresh keeps the last good time instead of going blank
  const lastUpdated = useRef<number | null>(null);
  if (page.data && page.updatedAt) lastUpdated.current = page.updatedAt;

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
  // A view opened by a link that also names a sort keeps that sort over the view's own default;
  // choosing a view by hand applies the view's sort as before.
  const sortRef = useRef(sortParam);
  sortRef.current = sortParam;
  const userRef = useRef(user);
  userRef.current = user;
  const apply = useCallback(
    (view: SavedView | null, fromLink = false) => {
      const query = view?.query;
      setFilter(query?.filter ?? null);
      setQueryFilter(query?.filter ?? null);
      setSearchText(query?.search ?? "");
      setSearch(query?.search ?? "");
      if (!(fromLink && sortRef.current)) setSort(query?.sort ?? "");
      setVisible(
        query?.columns ??
          columnPreference(userRef.current, workspaceId, entity),
      );
      setDensity(query?.density ?? "comfortable");
      setOffset(0);
      setSelected(new Set());
    },
    // the setters only call the URL setters, which are stable
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [workspaceId, entity],
  );
  const current: ViewDefinition = {
    filter,
    sort,
    columns: known,
    density,
    ...(search ? { search } : {}),
  };

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
  useRealtime(opsTopic, () => void page.reload(), live && description !== null);
  // The selection is offered to the command palette as commands about those rows (lib/selection.ts).
  const slot = useId();
  const rowsOnPage = page.data?.rows ?? lastPage.current?.rows ?? [];
  const nameOf = (row: EntityRow) =>
    rowLabel ? rowLabel(row) : String(row[shown[0]?.key ?? ""] ?? row.id);
  // rows that left the list (a refresh, another person's change) leave the selection with them,
  // so a bulk action never acts on a row that is no longer shown
  useEffect(() => {
    if (selected.size === 0) return;
    const present = new Set(rowsOnPage.map((row) => row.id));
    const kept = [...selected].filter((id) => present.has(id));
    if (kept.length === selected.size) return;
    const next = new Set(kept);
    setSelected(next);
    onSelect?.(next);
    // `selected` and `onSelect` change with the selection itself
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rowsOnPage]);
  const clearSelection = () => {
    setSelected(new Set());
    onSelect?.(new Set());
  };
  useEffect(() => {
    if (!selectable || selected.size === 0) return publishSelection(slot, null);
    const chosen = rowsOnPage.filter((row) => selected.has(row.id));
    const noun = label.toLowerCase();
    const count = chosen.length;
    const commands: SelectionCommand[] = [];
    if (count === 1 && inspect)
      commands.push({
        id: "open",
        label: `Open details for ${nameOf(chosen[0])}`,
        run: () => setOpenId(chosen[0].id, { replace: true }),
      });
    commands.push(
      ...(selectionCommands?.(chosen.map((row) => row.id)) ?? []),
      {
        id: "copy-names",
        label: `Copy the names of ${countOf(count, label)}`,
        run: () => {
          const text = chosen.map(nameOf).join("\n");
          if (!navigator.clipboard)
            return announce("Could not copy. Select the names in the list.");
          navigator.clipboard
            .writeText(text)
            .then(() => announce(`Copied ${countOf(count, label)}.`))
            .catch(() =>
              announce("Could not copy. Select the names in the list."),
            );
        },
      },
      {
        id: "clear",
        label: `Clear the selection of ${countOf(count, label)}`,
        run: clearSelection,
      },
    );
    publishSelection(slot, { entity, noun, count, commands });
    // the closures read the latest state through the setters; the snapshot depends on what is chosen
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected, rowsOnPage, selectable, selectionCommands, label, inspect]);
  useEffect(() => () => publishSelection(slot, null), [slot]);
  const searchable = (description?.search_fields?.length ?? 0) > 0;
  const searchHint = useId();
  const searchLabels = (description?.search_fields ?? [])
    .map((key) => fields.find((f) => f.key === key)?.label ?? key)
    .join(", ")
    .toLowerCase();
  // asking something else starts again at the first page with nothing selected
  const askedBefore = useRef(search);
  useEffect(() => {
    if (askedBefore.current === search) return;
    askedBefore.current = search;
    restart();
    // restart only calls setters
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);
  // A 400 that names the filter is shown beside the condition it names, and the list keeps the last
  // results it had; any other failure replaces the list as before.
  const problems =
    page.error instanceof ApiError && page.error.status === 400
      ? filterProblems(page.error.detail)
      : null;
  const failure = catalogue.error ?? (problems ? null : page.error);
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
          {live && health.blocksActions ? (
            <fieldset
              disabled
              className="cx-entity-grid__held"
              title={health.detail}
            >
              {actions?.(row)}
            </fieldset>
          ) : (
            actions?.(row)
          )}
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
        {searchable && (
          <div role="search" className="cx-entity-grid__search">
            <label>
              Search {label.toLowerCase()}
              <input
                type="search"
                value={searchText}
                maxLength={200}
                autoComplete="off"
                aria-describedby={searchHint}
                onChange={(e) => setSearchText(e.target.value)}
              />
            </label>
            <p id={searchHint} className="cx-muted" role="status">
              {tooShort
                ? "Each word needs at least 2 characters."
                : search && shownPage
                  ? `${shownPage.total.toLocaleString("en-US")} ${shownPage.total === 1 ? "result" : "results"} for “${search}”.`
                  : `Looks in ${searchLabels}.`}
            </p>
          </div>
        )}
        {filter && (
          <div
            role="group"
            aria-label="Active filter"
            className="cx-entity-grid__chips"
          >
            <span>Filter: {describeFilter(filter, fields)}</span>{" "}
            <button
              type="button"
              onClick={() => {
                setFilter(null);
                setQueryFilter(null);
                restart();
              }}
            >
              Clear filter
            </button>
            {problems && (
              <p role="status" className="cx-filter-problem">
                This filter could not be applied, so the list shows the last
                results. Open Filter, views and columns to fix it.
              </p>
            )}
          </div>
        )}
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
            problems={problems}
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
                    chooseColumns(
                      fields.filter((f) => keys.has(f.key)).map((f) => f.key),
                    );
                  }}
                />{" "}
                {field.label}
              </label>
            ))}
            <button type="button" onClick={() => chooseColumns([])}>
              Reset columns
            </button>
            {user && <small>Your choice is remembered on this device.</small>}
          </fieldset>
          {user && (
            <button
              type="button"
              aria-pressed={live}
              onClick={() => setLiveOperations(user, !live)}
            >
              Live operations
            </button>
          )}
          <label>
            Sort by{" "}
            <select
              value={sortState(sort).length > 1 ? "__several" : sort}
              onChange={(e) => {
                setSort(e.target.value);
                restart();
              }}
            >
              <option value="">Default order</option>
              {sortState(sort).length > 1 && (
                <option value="__several" disabled>
                  Several columns (set in the headers)
                </option>
              )}
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
        {live && (
          <LiveStatus topic={opsTopic} updatedAt={lastUpdated.current} />
        )}
        <DataGrid<EntityRow>
          label={label}
          columns={columns}
          rows={shownPage?.rows ?? []}
          status={status}
          sort={sortState(sort)}
          onSort={(next, additive) => {
            const before = sortState(sort);
            if (
              additive &&
              before.length >= MAX_SORT_KEYS &&
              next.length === before.length &&
              next.every(
                (n, i) =>
                  n.key === before[i].key &&
                  n.descending === before[i].descending,
              )
            )
              return announce(
                `Sort by at most ${MAX_SORT_KEYS} columns. Clear one first.`,
              );
            setSort(
              next.map((n) => `${n.descending ? "-" : ""}${n.key}`).join(","),
            );
            announce(
              describeSort(
                next,
                (key) => fields.find((f) => f.key === key)?.label ?? key,
              ),
            );
            restart();
          }}
          total={shownPage?.total}
          limit={PAGE_SIZE}
          offset={offset}
          onPage={(next) => {
            // a selection is of the rows in front of the person: another page starts with none
            setOffset(next);
            clearSelection();
          }}
          density={density}
          selected={selectable ? selected : undefined}
          onSelect={
            selectable
              ? (ids) => {
                  const bounded = new Set([...ids].slice(0, MAX_SELECTION));
                  if (bounded.size < ids.size)
                    announce(`Select at most ${MAX_SELECTION} rows at a time.`);
                  setSelected(bounded);
                  onSelect?.(bounded);
                }
              : undefined
          }
          rowLabel={rowLabel}
          actions={inspectAction}
          highlightedId={inspect ? openId : undefined}
          empty={empty}
          filtered={filter !== null || search !== ""}
          onClearFilter={() => {
            setFilter(null);
            setSearchText("");
            setSearch("");
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
