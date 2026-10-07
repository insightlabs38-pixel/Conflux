// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../lib/test-http";
import { withRouter } from "../lib/test-router";
import { EntityGrid } from "./EntityGrid";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

const field = (key: string, label: string, type: string, extra = {}) => ({
  key,
  label,
  type,
  operators: type === "enum" ? ["eq", "in"] : ["eq", "contains"],
  choices: [],
  sortable: true,
  filterable: true,
  default: true,
  ...extra,
});
const CATALOGUE = [
  {
    key: "applications",
    label: "Applications",
    default_sort: [],
    fields: [
      field("username", "Applicant", "text"),
      field("status", "Status", "enum", { choices: ["pending", "approved"] }),
      field("created_at", "Applied", "date", { operators: ["gt", "between"] }),
      field("note", "Note", "text", { default: false }),
    ],
  },
];
const ROWS = [
  {
    id: "1",
    username: "ada",
    status: "pending",
    created_at: "2027-03-01T12:00:00Z",
    note: "hi",
  },
  {
    id: "2",
    username: "ben",
    status: "approved",
    created_at: "2027-03-02T12:00:00Z",
    note: "",
  },
];

type Params = Record<string, string>;
async function mount(
  respond: (params: Params, path: string) => Response,
  props: Partial<React.ComponentProps<typeof EntityGrid>> = {},
) {
  const pages: Params[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown) => {
      const url = new URL(String(input), "http://x");
      if (url.pathname.endsWith("/entities/"))
        return jsonResponse(200, CATALOGUE);
      if (url.pathname.includes("/views/")) return jsonResponse(200, []);
      const params = Object.fromEntries(url.searchParams);
      pages.push(params);
      return respond(params, url.pathname);
    }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(
      withRouter(
        <EntityGrid
          workspaceId="w"
          eventId="e"
          entity="applications"
          label="Applications"
          {...props}
        />,
      ),
    ),
  );
  await act(async () => new Promise((resolve) => setTimeout(resolve, 0)));
  return { container, pages, root };
}
const page = (rows: unknown[], total = rows.length) => ({
  entity: "applications",
  total,
  limit: 25,
  offset: 0,
  filter: null,
  sort: [],
  columns: ["username", "status", "created_at"],
  rows,
});
const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));
async function until(check: () => boolean) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (check()) return;
    await act(async () => new Promise((resolve) => setTimeout(resolve, 5)));
  }
  throw new Error("Grid did not update");
}
const press = (c: HTMLElement, text: string) =>
  [...c.querySelectorAll("button")]
    .find((b) => b.textContent === text)!
    .click();
const choose = (el: HTMLSelectElement | HTMLInputElement, value: string) => {
  const proto =
    el instanceof HTMLSelectElement
      ? HTMLSelectElement.prototype
      : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(proto, "value")?.set?.call(el, value);
  el.dispatchEvent(
    new Event(el instanceof HTMLSelectElement ? "change" : "input", {
      bubbles: true,
    }),
  );
};

describe("EntityGrid", () => {
  it("shows the catalogue's default columns, formats values by type and asks for one page", async () => {
    const { container, pages, root } = await mount(() =>
      jsonResponse(200, page(ROWS)),
    );
    await until(
      () => container.querySelector("tbody tr:not([aria-hidden])") !== null,
    );
    expect(
      [...container.querySelectorAll("thead th")].map((h) =>
        h.textContent?.replace(/,.*$/, "").trim(),
      ),
    ).toEqual(["Applicant", "Status", "Applied"]);
    expect(container.textContent).toContain("Mar 1, 2027");
    expect(container.textContent).toContain("UTC");
    expect(pages[0]).toEqual({ limit: "25" });
    expect(container.textContent).toContain("Showing 1–2 of 2");
    await act(async () => root.unmount());
  });

  it("asks the server for sort, filter and a column choice rather than doing them itself", async () => {
    const { container, pages, root } = await mount(() =>
      jsonResponse(200, page(ROWS)),
    );
    await until(() => container.querySelector("th button") !== null);
    await act(async () =>
      container.querySelector<HTMLButtonElement>("th button")!.click(),
    );
    await settle();
    expect(pages.at(-1)).toMatchObject({ sort: "username", limit: "25" });
    await act(async () =>
      container.querySelector<HTMLButtonElement>("th button")!.click(),
    );
    await settle();
    expect(pages.at(-1)).toMatchObject({ sort: "-username" });

    // A column the catalogue does not show by default can be added.
    const note = [
      ...container.querySelectorAll<HTMLInputElement>("fieldset input"),
    ].find((i) => i.parentElement?.textContent?.includes("Note"))!;
    await act(async () => note.click());
    await until(
      () => pages.at(-1)?.columns === "username,status,created_at,note",
    );

    await act(async () => press(container, "Add condition"));
    await act(async () =>
      choose(
        container.querySelector<HTMLSelectElement>(
          '[aria-label="Field of condition 1"]',
        )!,
        "status",
      ),
    );
    await act(async () =>
      choose(
        container.querySelector<HTMLSelectElement>(
          '[aria-label="Value of condition 1"]',
        )!,
        "pending",
      ),
    );
    await settle();
    expect(JSON.parse(pages.at(-1)!.filter)).toEqual({
      field: "status",
      op: "eq",
      value: "pending",
    });
    expect(container.textContent).toContain("(filtered)");
    await act(async () => root.unmount());
  });

  it("pages through the server and says when a filter matches nothing", async () => {
    const { container, pages, root } = await mount((params) =>
      params.filter
        ? jsonResponse(200, { ...page([]), total: 0 })
        : jsonResponse(200, { ...page(ROWS), total: 60 }),
    );
    await until(
      () => container.textContent?.includes("Showing 1–2 of 60") ?? false,
    );
    await act(async () => press(container, "Next"));
    await until(() => pages.at(-1)?.offset === "25");
    await act(async () => press(container, "Add condition"));
    await act(async () =>
      choose(
        container.querySelector<HTMLInputElement>(
          '[aria-label="Value of condition 1"]',
        )!,
        "zzz",
      ),
    );
    await until(
      () =>
        container.textContent?.includes("No rows match this filter") ?? false,
    );
    expect(pages.at(-1)).not.toHaveProperty("offset"); // a new filter starts on the first page
    await act(async () => press(container, "Clear filter"));
    await until(
      () => container.textContent?.includes("Showing 1–2 of 60") ?? false,
    );
    await act(async () => root.unmount());
  });

  it("renders row actions and custom cells and reloads when the token changes", async () => {
    let served = 0;
    const respond = () => {
      served += 1;
      return jsonResponse(200, page(ROWS));
    };
    const { container, root } = await mount(respond, {
      actions: (row) => (
        <button type="button">Approve {String(row.username)}</button>
      ),
      renderers: { status: (row) => <em>{String(row.status)}!</em> },
      rowLabel: (row) => String(row.username),
      selectable: true,
    });
    await until(() => container.textContent?.includes("Approve ada") ?? false);
    expect(container.querySelector("td em")?.textContent).toBe("pending!");
    expect(container.querySelector('[aria-label="Select ada"]')).not.toBeNull();
    const before = served;
    await act(async () =>
      root.render(
        withRouter(
          <EntityGrid
            workspaceId="w"
            eventId="e"
            entity="applications"
            label="Applications"
            refreshToken={1}
          />,
        ),
      ),
    );
    await until(() => served > before);
    await act(async () => root.unmount());
  });

  it("shows a denied list when the caller may not query the entity, and a failed load with a retry", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse(200, [])),
    );
    const denied = document.createElement("div");
    document.body.appendChild(denied);
    const deniedRoot = createRoot(denied);
    await act(async () =>
      deniedRoot.render(
        withRouter(
          <EntityGrid
            workspaceId="w"
            eventId="e"
            entity="applications"
            label="Applications"
          />,
        ),
      ),
    );
    await until(() => denied.textContent?.includes("Access denied") ?? false);
    await act(async () => deniedRoot.unmount());

    const { container, root } = await mount(() =>
      jsonResponse(500, { detail: "Boom" }),
    );
    await until(() => container.textContent?.includes("Try again") ?? false);
    expect(container.querySelector("table")).toBeNull();
    await act(async () => root.unmount());
  });
});
