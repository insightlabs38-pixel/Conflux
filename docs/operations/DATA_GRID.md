# Data grid (lists over the entity query)

The standard list of an organizer surface: `EntityGrid` (filter builder, saved views, columns, density, paging) over `DataGrid` (a controlled, server-driven table), fed by the [entity query](../api/ENTITY_QUERY.md). A feature adds per-row actions and cell renderers; it does not write its own list plumbing.

## What organizers get

- **Applications** (Participants > Registration) and **Projects** (Participants > Projects) are grids. Columns, sort, filter and paging are asked of the server; nothing is sorted or filtered in the browser.
- Under **Filter, views and columns** (collapsed by default): saved views ([guide](../api/SAVED_VIEWS.md)), a filter built from conditions (all or any), the column picker, **Sort by** and density (comfortable or compact).
- Sorting is also available from the column headers on wide screens (`aria-sort`, activate to cycle ascending, descending, none); the narrow layout stacks each row as a card, so sorting there is through **Sort by**.
- Row checkboxes (when a feature enables selection) move with the arrow keys, Home, End and Page Up or Down; a header checkbox selects the page.
- Distinct states: loading, empty (with a feature-supplied hint), "No rows match this filter" (with a clear button), error with retry, and denied when the caller may not query the entity.

## For developers

- `DataGrid<Row>` (`components/DataGrid.tsx`): `columns`, `rows`, `status`, `sort`/`onSort`, `total`/`limit`/`offset`/`onPage`, `density`, `selected`/`onSelect`/`rowLabel`, `actions`, `empty`, `filtered`/`onClearFilter`. A native table (caption, `scope`, `aria-sort`, sticky header, horizontal scroll region); it never reorders or filters the rows it is given.
- `EntityGrid` (`components/EntityGrid.tsx`): `workspaceId`, `eventId`, `entity`, `label`, `rowLabel`, `actions`, `renderers` (per column key), `selectable`/`onSelect`, `refreshToken` (change it to reload after a row action), `empty`. Which fields exist, their types and which are default columns come from the entity registration.
- While the next page loads, the last page stays visible and the grid is marked busy.
- To list a new entity: register it (`core.entities.register` in your app's `entities.py`), then render `<EntityGrid entity="…" />`. The hand-written tables keep working and adopt it when next touched.

## Not here

Saved column widths and order, inline editing, virtual scrolling (server paging bounds the rows), and multi-column header sort (the query supports three sort keys; the grid exposes one through the headers and **Sort by**).
