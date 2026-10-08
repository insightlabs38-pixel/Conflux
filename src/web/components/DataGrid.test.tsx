// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot } from "react-dom/client";
import { describe, expect, it, vi } from "vitest";
import {
  DataGrid,
  type GridColumn,
  type GridStatus,
  type SortState,
} from "./DataGrid";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

type Row = { id: string; name: string; score: number };
const ROWS: Row[] = [
  { id: "a", name: "Ada", score: 3 },
  { id: "b", name: "Ben", score: 5 },
  { id: "c", name: "Cyd", score: 4 },
];
const COLUMNS: GridColumn<Row>[] = [
  { key: "name", label: "Name", sortable: true },
  { key: "score", label: "Score", sortable: true, align: "end" },
  { key: "note", label: "Note" },
];

function mount(ui: React.ReactElement) {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  act(() => root.render(ui));
  return { container, root };
}
const key = (el: Element, name: string) =>
  act(async () => {
    el.dispatchEvent(
      new KeyboardEvent("keydown", {
        key: name,
        bubbles: true,
        cancelable: true,
      }),
    );
  });

describe("DataGrid", () => {
  it("is a real table: caption, column headers, row cells labelled for the stacked layout", () => {
    const { container, root } = mount(
      <DataGrid label="Applications" columns={COLUMNS} rows={ROWS} total={3} />,
    );
    expect(container.querySelector("caption")?.textContent).toContain(
      "Applications, 3 in all",
    );
    expect(
      [...container.querySelectorAll("th")].map((h) => h.getAttribute("scope")),
    ).toEqual(["col", "col", "col"]);
    const cells = container.querySelectorAll("tbody tr:first-child td");
    expect([...cells].map((c) => c.getAttribute("data-label"))).toEqual([
      "Name",
      "Score",
      "Note",
    ]);
    expect(cells[2].textContent).toBe("—"); // a missing value is a dash, not "undefined"
    expect(container.textContent).toContain("Showing 1–3 of 3");
    act(() => root.unmount());
  });

  it("sorts through the server: header state, cycle asc, desc, none, and never reorders rows itself", async () => {
    const seen: SortState[] = [];
    function Host() {
      const [sort, setSort] = useState<SortState>([]);
      return (
        <DataGrid
          label="People"
          columns={COLUMNS}
          rows={ROWS}
          sort={sort}
          onSort={(next) => {
            seen.push(next);
            setSort(next);
          }}
        />
      );
    }
    const { container, root } = mount(<Host />);
    const heads = () =>
      [...container.querySelectorAll("th")].map((h) =>
        h.getAttribute("aria-sort"),
      );
    expect(heads()).toEqual(["none", "none", null]); // the unsortable column has no aria-sort
    const sortButton = () =>
      container.querySelector<HTMLButtonElement>("th button")!;
    await act(async () => sortButton().click());
    expect(seen.at(-1)).toEqual([{ key: "name", descending: false }]);
    expect(heads()[0]).toBe("ascending");
    await act(async () => sortButton().click());
    expect(seen.at(-1)).toEqual([{ key: "name", descending: true }]);
    expect(heads()[0]).toBe("descending");
    await act(async () => sortButton().click());
    expect(seen.at(-1)).toEqual([]);
    expect(heads()[0]).toBe("none");
    // The rows stay exactly as given whatever the sort state.
    expect(
      [...container.querySelectorAll("tbody tr td:first-child")].map(
        (c) => c.textContent,
      ),
    ).toEqual(["Ada", "Ben", "Cyd"]);
    act(() => root.unmount());
  });

  it("adds a second and third sort key with Shift, shows their order and refuses a fourth", async () => {
    const COLS = [
      ...COLUMNS,
      { key: "a", label: "A", sortable: true },
      { key: "b", label: "B", sortable: true },
    ];
    function Host() {
      const [sort, setSort] = useState<SortState>([]);
      return (
        <DataGrid
          label="People"
          columns={COLS}
          rows={ROWS}
          sort={sort}
          onSort={(next) => setSort(next)}
        />
      );
    }
    const { container, root } = mount(<Host />);
    const button = (label: string) =>
      [...container.querySelectorAll<HTMLButtonElement>("th button")].find(
        (b) => b.textContent?.startsWith(label),
      )!;
    const click = (label: string, shiftKey = false) =>
      act(async () => {
        button(label).dispatchEvent(
          new MouseEvent("click", { bubbles: true, shiftKey }),
        );
      });
    const state = () =>
      Object.fromEntries(
        [...container.querySelectorAll("th")]
          .filter((h) => h.getAttribute("aria-sort"))
          .map((h) => [
            h.textContent?.split(",")[0].replace(/\d$/, ""),
            h.getAttribute("aria-sort"),
          ]),
      );
    await click("Name");
    await click("Score", true);
    await click("A", true);
    expect(state()).toMatchObject({
      Name: "ascending",
      Score: "ascending",
      A: "ascending",
      B: "none",
    });
    expect(container.querySelectorAll(".cx-datagrid__rank").length).toBe(3);
    expect(button("A").textContent).toContain("sort key 3 of 3");
    await click("B", true); // a fourth key is refused: nothing changes
    expect(state().B).toBe("none");
    await click("Score", true); // cycles within the keys: descending
    expect(state().Score).toBe("descending");
    await click("Score", true); // and leaves
    expect(state()).toMatchObject({
      Name: "ascending",
      Score: "none",
      A: "ascending",
    });
    await click("A"); // a plain click on another column starts again there
    expect(state()).toMatchObject({
      Name: "none",
      Score: "none",
      A: "ascending",
    });
    act(() => root.unmount());
  });

  it("selects rows and pages, and moves between row checkboxes with the arrow keys", async () => {
    const chosen: string[][] = [];
    function Host() {
      const [selected, setSelected] = useState<Set<string>>(new Set());
      return (
        <DataGrid
          label="People"
          columns={COLUMNS}
          rows={ROWS}
          selected={selected}
          onSelect={(ids) => {
            chosen.push([...ids].sort());
            setSelected(ids);
          }}
          rowLabel={(row) => row.name}
        />
      );
    }
    const { container, root } = mount(<Host />);
    const box = (name: string) =>
      container.querySelector<HTMLInputElement>(
        `[aria-label="Select ${name}"]`,
      )!;
    await act(async () => box("Ben").click());
    expect(chosen.at(-1)).toEqual(["b"]);
    expect(
      container.querySelector("tr[aria-selected=true]")?.textContent,
    ).toContain("Ben");
    expect(container.textContent).toContain("1 selected");
    const all = container.querySelector<HTMLInputElement>(
      '[aria-label="Select all people on this page"]',
    )!;
    expect(all.indeterminate).toBe(true);
    await act(async () => all.click());
    expect(chosen.at(-1)).toEqual(["a", "b", "c"]);
    await act(async () => all.click());
    expect(chosen.at(-1)).toEqual([]);

    box("Ada").focus();
    await key(box("Ada"), "ArrowDown");
    expect(document.activeElement).toBe(box("Ben"));
    await key(box("Ben"), "End");
    expect(document.activeElement).toBe(box("Cyd"));
    await key(box("Cyd"), "ArrowDown"); // stays on the last row
    expect(document.activeElement).toBe(box("Cyd"));
    await key(box("Cyd"), "Home");
    expect(document.activeElement).toBe(box("Ada"));
    act(() => root.unmount());
  });

  it("pages with previous and next and says where you are", async () => {
    const onPage = vi.fn();
    const { container, root } = mount(
      <DataGrid
        label="People"
        columns={COLUMNS}
        rows={ROWS}
        total={7}
        limit={3}
        offset={3}
        onPage={onPage}
      />,
    );
    expect(container.textContent).toContain("Showing 4–6 of 7");
    const button = (text: string) =>
      [...container.querySelectorAll("button")].find(
        (b) => b.textContent === text,
      )!;
    await act(async () => button("Next").click());
    expect(onPage).toHaveBeenLastCalledWith(6);
    await act(async () => button("Previous").click());
    expect(onPage).toHaveBeenLastCalledWith(0);
    act(() => root.unmount());
    const last = mount(
      <DataGrid
        label="People"
        columns={COLUMNS}
        rows={ROWS}
        total={6}
        limit={3}
        offset={3}
        onPage={onPage}
      />,
    );
    expect(
      [...last.container.querySelectorAll("button")].find(
        (b) => b.textContent === "Next",
      )!.disabled,
    ).toBe(true);
    act(() => last.root.unmount());
  });

  it("has a distinct state for loading, empty, filtered-empty, error and denied", async () => {
    const states: [GridStatus, string][] = [
      [{ kind: "loading" }, "Loading People…"],
      [{ kind: "denied", message: "No access." }, "Access denied"],
      [{ kind: "error", message: "Boom", onRetry: () => {} }, "Try again"],
    ];
    for (const [status, text] of states) {
      const { container, root } = mount(
        <DataGrid label="People" columns={COLUMNS} rows={[]} status={status} />,
      );
      expect(container.textContent).toContain(text);
      // only loading keeps a table: the known columns with placeholder rows, hidden from assistive tech
      expect(container.querySelector("table") !== null).toBe(
        status.kind === "loading",
      );
      act(() => root.unmount());
    }
    const loading = mount(
      <DataGrid
        label="People"
        columns={COLUMNS}
        rows={[]}
        status={{ kind: "loading" }}
      />,
    );
    expect(
      loading.container.querySelector("[aria-busy='true']"),
    ).not.toBeNull();
    expect(loading.container.querySelectorAll("th")).toHaveLength(
      COLUMNS.length,
    );
    expect(loading.container.querySelectorAll("tbody tr")).toHaveLength(0);
    expect(
      loading.container.querySelectorAll(
        ".cx-skeleton-rows[aria-hidden='true'] .cx-skeleton",
      ),
    ).toHaveLength(5 * COLUMNS.length);
    act(() => loading.root.unmount());
    const empty = mount(
      <DataGrid
        label="People"
        columns={COLUMNS}
        rows={[]}
        empty={<p>Nobody has joined.</p>}
      />,
    );
    expect(empty.container.textContent).toContain("No people yet");
    expect(empty.container.textContent).toContain("Nobody has joined.");
    act(() => empty.root.unmount());

    const cleared = vi.fn();
    const filtered = mount(
      <DataGrid
        label="People"
        columns={COLUMNS}
        rows={[]}
        filtered
        onClearFilter={cleared}
      />,
    );
    expect(filtered.container.textContent).toContain(
      "No rows match this filter",
    );
    await act(async () => filtered.container.querySelector("button")!.click());
    expect(cleared).toHaveBeenCalled();
    act(() => filtered.root.unmount());
  });

  it("renders custom cells and per-row actions, and a compact density class", () => {
    const { container, root } = mount(
      <DataGrid
        label="People"
        columns={[
          {
            key: "name",
            label: "Name",
            render: (row: Row) => <strong>{row.name}!</strong>,
          },
        ]}
        rows={ROWS}
        density="compact"
        actions={(row: Row) => <button type="button">Open {row.name}</button>}
      />,
    );
    expect(container.querySelector("tbody td strong")?.textContent).toBe(
      "Ada!",
    );
    expect(container.querySelector(".cx-grid-wrap--compact")).not.toBeNull();
    expect(container.textContent).toContain("Open Cyd");
    act(() => root.unmount());
  });
});

describe("DataGrid paging footer", () => {
  function Host({
    offset = 50,
    limit = 25,
    total = 5012,
    onPage = () => {},
    onPageSize,
  }: {
    offset?: number;
    limit?: number;
    total?: number;
    onPage?: (n: number) => void;
    onPageSize?: (n: number) => void;
  }) {
    return (
      <DataGrid
        label="People"
        columns={COLUMNS}
        rows={ROWS}
        total={total}
        limit={limit}
        offset={offset}
        onPage={onPage}
        pageSizes={[25, 50, 100]}
        onPageSize={onPageSize}
      />
    );
  }
  it("says where the page is in thousands, jumps to the first and last pages and changes the page size", async () => {
    const jumps: number[] = [];
    const sizes: number[] = [];
    const { container, root } = mount(
      <Host onPage={(n) => jumps.push(n)} onPageSize={(n) => sizes.push(n)} />,
    );
    const text = () =>
      container.querySelector(".cx-datagrid__footer")!.textContent!;
    expect(text()).toContain("Showing 51–53 of 5,012");
    expect(text()).toContain("Page 3 of 201");
    const press = (name: string) =>
      [...container.querySelectorAll("button")].find(
        (b) => b.textContent === name,
      )!;
    await act(async () => press("Last").click());
    await act(async () => press("First").click());
    await act(async () => press("Next").click());
    expect(jumps).toEqual([5000, 0, 75]);
    const select = container.querySelector<HTMLSelectElement>(
      ".cx-datagrid__size select",
    )!;
    expect([...select.options].map((o) => o.value)).toEqual([
      "25",
      "50",
      "100",
    ]);
    await act(async () => {
      Object.getOwnPropertyDescriptor(
        HTMLSelectElement.prototype,
        "value",
      )!.set!.call(select, "100");
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    expect(sizes).toEqual([100]);
    act(() => root.unmount());
  });

  it("shows no first, last or page choice for a single page and handles an empty result", async () => {
    const { container, root } = mount(<Host offset={0} total={3} />);
    const names = [
      ...container.querySelectorAll(".cx-datagrid__pages button"),
    ].map((b) => b.textContent);
    expect(names).toEqual(["Previous", "Next"]);
    expect(container.textContent).toContain("Page 1 of 1");
    act(() => root.unmount());
  });
});
