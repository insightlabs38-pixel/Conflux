// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../lib/test-http";
import { createTestQueryClient, withRouter } from "../lib/test-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, useLocation } from "react-router";
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
      if (url.pathname.includes("/accounts/me/"))
        // the view bar knows whose pins to read
        return jsonResponse(200, { public_id: "u1", memberships: [] });
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
      [...container.querySelectorAll("thead th")]
        .filter((h) => h.textContent?.trim() !== "Actions") // the Details column has no visible heading
        .map((h) => h.textContent?.replace(/,.*$/, "").trim()),
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

function Where() {
  const location = useLocation();
  return <p data-testid="where">{location.search}</p>;
}
const search = () =>
  document.querySelector('[data-testid="where"]')!.textContent;

/** The grid inside a router whose location is readable, starting at `url`. */
async function mountAt(
  url: string,
  props: Partial<React.ComponentProps<typeof EntityGrid>> = {},
) {
  const pages: Params[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown) => {
      const u = new URL(String(input), "http://x");
      if (u.pathname.endsWith("/entities/"))
        return jsonResponse(200, CATALOGUE);
      if (u.pathname.includes("/views/")) return jsonResponse(200, []);
      if (u.pathname.includes("/accounts/me/"))
        return jsonResponse(200, { public_id: "u1", memberships: [] });
      pages.push(Object.fromEntries(u.searchParams));
      return jsonResponse(200, page(ROWS));
    }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(
      <QueryClientProvider client={createTestQueryClient()}>
        <MemoryRouter initialEntries={[url]}>
          <Where />
          <EntityGrid
            workspaceId="w"
            eventId="e"
            entity="applications"
            label="Applications"
            {...props}
          />
        </MemoryRouter>
      </QueryClientProvider>,
    ),
  );
  await act(async () => new Promise((resolve) => setTimeout(resolve, 0)));
  return { container, pages, root };
}

describe("EntityGrid inspector", () => {
  afterEach(() => {
    document.body.innerHTML = ""; // each test reads the document, so none may leave its grid in it
  });
  const details = (c: HTMLElement, id: string) =>
    c.querySelector<HTMLButtonElement>(`[data-inspect="${id}"]`)!;
  const inspector = () => document.querySelector(".cx-inspector");
  const fieldsShown = () =>
    [...document.querySelectorAll(".cx-inspector__fields > div")].map((row) => [
      row.querySelector("dt")?.textContent,
      row.querySelector("dd")?.textContent,
    ]);

  it("opens a record beside the list with every field, marks it in the list and keeps the list as it was", async () => {
    const { container, pages, root } = await mountAt("/w/w/participants");
    await until(() => container.querySelector("tbody tr") !== null);
    expect(inspector()).toBeNull();
    await act(async () => details(container, "2").click());
    await until(() => inspector() !== null);
    expect(inspector()!.getAttribute("aria-labelledby")).toBeTruthy();
    expect(inspector()!.querySelector("h3")!.textContent).toBe("ben");
    expect(fieldsShown().map(([label]) => label)).toEqual([
      "Applicant",
      "Status",
      "Applied",
      "Note", // a field the list does not show
    ]);
    expect(fieldsShown()[1]).toEqual(["Status", "approved"]);
    expect(fieldsShown()[3]).toEqual(["Note", "—"]);
    // the row is marked and is the same element as before (the list was not remounted)
    expect(
      container
        .querySelector('tr[data-row-id="2"]')!
        .getAttribute("aria-current"),
    ).toBe("true");
    expect(search()).toBe("?row_applications=2"); // panel state in the URL
    // the detail read asked for every field, the list's own for its columns
    expect(
      pages.some((p) => (p.columns ?? "").split(",").includes("note")),
    ).toBe(true);
    await act(async () => root.unmount());
  });

  it("steps to the neighbouring record, says where it is, and closes with Escape giving focus back", async () => {
    const { container, root } = await mountAt("/w/w/participants");
    await until(() => container.querySelector("tbody tr") !== null);
    await act(async () => details(container, "1").click());
    await until(() => inspector() !== null);
    const [previous, next] = [
      ...inspector()!.querySelectorAll<HTMLButtonElement>(
        ".cx-inspector__step button",
      ),
    ];
    expect(previous.disabled).toBe(true); // first record
    expect(
      inspector()!.querySelector(".cx-inspector__step span")!.textContent,
    ).toBe("1 of 2");
    await act(async () => next.click());
    expect(inspector()!.querySelector("h3")!.textContent).toBe("ben");
    expect(search()).toBe("?row_applications=2");
    expect(
      inspector()!.querySelectorAll<HTMLButtonElement>(
        ".cx-inspector__step button",
      )[1].disabled,
    ).toBe(true);
    await act(async () => {
      inspector()!
        .querySelector("h3")!
        .dispatchEvent(
          new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
        );
    });
    expect(inspector()).toBeNull();
    expect(search()).toBe("");
    await act(async () => new Promise((resolve) => setTimeout(resolve, 20)));
    expect(document.activeElement).toBe(details(container, "2"));
    await act(async () => root.unmount());
  });

  it("opens from a link, and says so when the record is not on this page", async () => {
    const { container, root } = await mountAt(
      "/w/w/participants?row_applications=99",
    );
    await until(() => inspector() !== null);
    expect(inspector()!.textContent).toContain("not on the current page");
    expect(container.querySelector("tr[aria-current]")).toBeNull();
    await act(async () => root.unmount());
  });

  it("offers no Details button when a list opts out", async () => {
    window.history.replaceState({}, "", "/");
    const { container, root } = await mount(
      () => jsonResponse(200, page(ROWS)),
      { inspect: false },
    );
    await until(() => container.querySelector("tbody tr") !== null);
    expect(container.querySelector("[data-inspect]")).toBeNull();
    await act(async () => root.unmount());
  });
});

describe("EntityGrid sort and page in the URL", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });
  const lastQuery = (pages: Record<string, string>[]) => pages.at(-1)!;

  it("reads the sort and page a link names, asks the server for them, and ignores what it cannot honour", async () => {
    const { pages, root } = await mountAt(
      "/w/w/participants?sort_applications=-username&page_applications=3",
    );
    await until(() => pages.length > 0);
    expect(lastQuery(pages)).toMatchObject({
      sort: "-username",
      offset: "50",
      limit: "25",
    });
    await act(async () => root.unmount());
    document.body.innerHTML = "";
    const bad = await mountAt(
      "/w/w/participants?sort_applications=password&page_applications=abc",
    );
    await until(() => bad.pages.length > 0);
    expect(lastQuery(bad.pages).sort).toBeUndefined(); // not a sortable field: ignored
    expect(lastQuery(bad.pages).offset).toBeUndefined(); // not a page number: the first page
    await act(async () => bad.root.unmount());
  });

  it("writes a chosen sort to the URL (replacing, back to the first page) so a link reproduces the list", async () => {
    const { container, root } = await mountAt(
      "/w/w/participants?page_applications=2",
    );
    await until(() => container.querySelector("th button") !== null);
    await act(async () =>
      container.querySelector<HTMLButtonElement>("th button")!.click(),
    );
    expect(search()).toBe("?sort_applications=username"); // the page param was cleared with the sort
    await act(async () => root.unmount());
  });
});

describe("remembered columns", () => {
  const headers = (c: HTMLElement) =>
    [...c.querySelectorAll("th")].map((th) => th.textContent?.trim());

  it("remembers the picker's choice per person and list, offers a reset, and ignores keys the list no longer has", async () => {
    window.localStorage.clear();
    const first = await mount(() => jsonResponse(200, page(ROWS)));
    await until(() => first.container.querySelector("tbody tr") !== null);
    await until(
      () => first.container.textContent?.includes("remembered") ?? false,
    );
    const note = [...first.container.querySelectorAll("label")]
      .find((l) => l.textContent?.includes("Note"))!
      .querySelector("input") as HTMLInputElement;
    await act(async () => note.click());
    expect(
      JSON.parse(
        window.localStorage.getItem("conflux:v1:u1:w:columns:applications")!,
      ),
    ).toEqual(["username", "status", "created_at", "note"]);
    await act(async () => first.root.unmount());

    // a new visit, same person: the choice is back without touching the picker
    const again = await mount(() => jsonResponse(200, page(ROWS)));
    await until(() => headers(again.container).includes("Note"));

    // reset forgets it
    await act(async () => press(again.container, "Reset columns"));
    expect(
      window.localStorage.getItem("conflux:v1:u1:w:columns:applications"),
    ).toBeNull();
    await until(() => !headers(again.container).includes("Note"));
    await act(async () => again.root.unmount());

    // a stored key that no longer exists never leaves the list without columns
    window.localStorage.setItem(
      "conflux:v1:u1:w:columns:applications",
      JSON.stringify(["gone"]),
    );
    const stale = await mount(() => jsonResponse(200, page(ROWS)));
    await until(() =>
      headers(stale.container).some((h) => h?.startsWith("Applicant")),
    );
    await act(async () => stale.root.unmount());
    window.localStorage.clear();
  });
});
