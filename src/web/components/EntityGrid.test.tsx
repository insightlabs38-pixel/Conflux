// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../lib/test-http";
import { createTestQueryClient, withRouter } from "../lib/test-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, useLocation } from "react-router";
import { EntityGrid } from "./EntityGrid";
import { currentSelection } from "../lib/selection";
import { RealtimeProvider } from "../hooks/useRealtime";
import { manualTransport, RealtimeHub } from "../lib/realtime";
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
    search_fields: ["username", "note"],
    fields: [
      field("username", "Applicant", "text"),
      field("status", "Status", "enum", {
        choices: ["pending", "approved"],
        groupable: true,
      }),
      field("created_at", "Applied", "date", { operators: ["gt", "between"] }),
      field("note", "Note", "text", { default: false, groupable: true }),
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
  wrap: (node: React.ReactNode) => React.ReactNode = (node) => node,
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
      wrap(
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
    // the filter is asked of the server a moment after the last change
    await until(() => pages.at(-1)?.filter !== undefined);
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

  it("reads several sort keys from a link, drops the ones it cannot honour and writes a Shift-added key joined with a colon", async () => {
    const { container, pages, root } = await mountAt(
      "/w/w/participants?sort_applications=-username:password:status",
    );
    await until(() => pages.length > 0);
    expect(lastQuery(pages).sort).toBe("-username,status"); // password is not sortable
    const headers = () => [
      ...container.querySelectorAll<HTMLButtonElement>("th button"),
    ];
    await until(() =>
      headers().some((b) => b.textContent?.startsWith("Applied")),
    );
    const created = headers().find((b) =>
      b.textContent?.startsWith("Applied"),
    )!;
    await act(async () => {
      created.dispatchEvent(
        new MouseEvent("click", { bubbles: true, shiftKey: true }),
      );
    });
    expect(search()).toBe("?sort_applications=-username%3Astatus%3Acreated_at");
    // a fourth key is refused and said so
    const note = headers().find((b) => b.textContent?.startsWith("Note"));
    if (note)
      await act(async () => {
        note.dispatchEvent(
          new MouseEvent("click", { bubbles: true, shiftKey: true }),
        );
      });
    expect(search()).toBe("?sort_applications=-username%3Astatus%3Acreated_at");
    await act(async () => root.unmount());
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
  // a header reads "Note" or "Note, activate to sort ascending" depending on when it is read
  const headers = (c: HTMLElement) =>
    [...c.querySelectorAll("th")].map(
      (th) => th.textContent?.split(",")[0].trim() ?? "",
    );

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
    await until(() => headers(stale.container).includes("Applicant"));
    await act(async () => stale.root.unmount());
    window.localStorage.clear();
  });
});

describe("live operations", () => {
  it("is off until chosen, then shows the connection and the data's age, refreshes on a hint and holds actions while offline", async () => {
    window.localStorage.clear();
    const feed = manualTransport();
    const hub = new RealtimeHub(feed.transport);
    let reads = 0;
    const { container, root } = await mount(
      () => {
        reads += 1;
        return jsonResponse(200, page(ROWS));
      },
      { actions: () => <button type="button">Approve</button> },
      (node) => <RealtimeProvider hub={hub}>{node}</RealtimeProvider>,
    );
    await until(() => container.querySelector("tbody tr") !== null);
    expect(container.querySelector(".cx-live")).toBeNull();

    const toggle = [...container.querySelectorAll("button")].find(
      (b) => b.textContent === "Live operations",
    )!;
    expect(toggle.getAttribute("aria-pressed")).toBe("false");
    await act(async () => toggle.click());
    await until(() => container.querySelector(".cx-live") !== null);
    expect(
      window.localStorage.getItem("conflux:v1:u1:device:live-operations"),
    ).toBe("on");
    expect(container.querySelector(".cx-live")?.textContent).toContain(
      "Live operations · Connected",
    );
    expect(container.querySelector(".cx-live")?.textContent).toContain(
      "Data as of",
    );

    // a hint asks the server again
    const before = reads;
    await act(async () =>
      feed.emit("workspace:w:event:e:applications:ops", "poll"),
    );
    await until(() => reads > before);

    // offline: the status says so, row actions wait with the reason, the rows stay
    await act(async () =>
      feed.setStatus("workspace:w:event:e:applications:ops", "offline"),
    );
    await until(
      () =>
        container.querySelector(".cx-live")?.getAttribute("data-tone") ===
        "offline",
    );
    const held = container.querySelector("fieldset[disabled]");
    expect(held?.getAttribute("title")).toContain("no connection");
    expect(held?.textContent).toContain("Approve");
    expect(container.querySelectorAll("tbody tr").length).toBe(2);

    // back online: actions are available again
    await act(async () =>
      feed.setStatus("workspace:w:event:e:applications:ops", "polling"),
    );
    await until(() => container.querySelector("fieldset[disabled]") === null);
    expect(container.querySelector(".cx-live")?.textContent).toContain(
      "every 15 s",
    );

    await act(async () => toggle.click());
    expect(container.querySelector(".cx-live")).toBeNull();
    await act(async () => root.unmount());
    window.localStorage.clear();
  });
});

describe("selection commands", () => {
  it("publishes the selected rows with their commands, adds the list's own and withdraws them with the selection", async () => {
    const run: string[][] = [];
    const { container, root } = await mount(
      () => jsonResponse(200, page(ROWS)),
      {
        selectable: true,
        rowLabel: (row) => String(row.username),
        selectionCommands: (ids) => [
          {
            id: "x",
            label: `Archive ${ids.length}`,
            run: () => void run.push(ids),
          },
        ],
      },
    );
    await until(() => container.querySelector("tbody tr") !== null);
    expect(currentSelection()).toBeNull();
    const box = (name: string) =>
      container.querySelector(
        `input[aria-label="Select ${name}"]`,
      ) as HTMLInputElement;
    await act(async () => box("ada").click());
    expect(currentSelection()?.commands.map((c) => c.label)).toEqual([
      "Open details for ada",
      "Archive 1",
      "Copy the names of 1 application",
      "Clear the selection of 1 application",
    ]);
    await act(async () => box("ben").click());
    const two = currentSelection()!;
    expect(two.count).toBe(2);
    expect(two.commands.map((c) => c.label)).toEqual([
      "Archive 2",
      "Copy the names of 2 applications",
      "Clear the selection of 2 applications",
    ]);
    two.commands[0].run();
    expect(run).toEqual([["1", "2"]]);
    await act(async () => two.commands[2].run());
    expect(currentSelection()).toBeNull();
    await act(async () => box("ada").click());
    await act(async () => root.unmount());
    expect(currentSelection()).toBeNull(); // gone with the list
  });
});

describe("search", () => {
  it("asks the server after a pause, needs two characters a word, stays out of the URL and starts again at page one", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      const { container, pages, root } = await mount(() =>
        jsonResponse(200, page(ROWS)),
      );
      await until(() => container.querySelector("tbody tr") !== null);
      const box = container.querySelector(
        'input[type="search"]',
      ) as HTMLInputElement;
      expect(box).not.toBeNull();
      expect(container.textContent).toContain("Looks in applicant, note.");
      const before = pages.length;
      await act(async () => choose(box, "a"));
      await act(async () => void vi.advanceTimersByTime(500));
      expect(container.textContent).toContain("at least 2 characters");
      expect(pages.length).toBe(before); // nothing asked for one letter
      await act(async () => choose(box, "ada lo"));
      await act(async () => void vi.advanceTimersByTime(500));
      await until(() => pages.some((p) => p.search === "ada lo"));
      expect(container.textContent).toContain("for “ada lo”");
      expect(window.location.search).not.toContain("ada"); // typed text never reaches the URL
      expect(JSON.stringify(Object.entries(window.localStorage))).not.toContain(
        "ada",
      );
      await act(async () => choose(box, ""));
      await act(async () => void vi.advanceTimersByTime(500));
      await until(() => pages.at(-1)?.search === undefined);
      await act(async () => root.unmount());
    } finally {
      vi.useRealTimers();
    }
  });

  it("has no box when the list has no search fields", async () => {
    const saved = CATALOGUE[0].search_fields;
    delete (CATALOGUE[0] as { search_fields?: string[] }).search_fields;
    try {
      const { container, root } = await mount(() =>
        jsonResponse(200, page(ROWS)),
      );
      await until(() => container.querySelector("tbody tr") !== null);
      expect(container.querySelector('input[type="search"]')).toBeNull();
      await act(async () => root.unmount());
    } finally {
      CATALOGUE[0].search_fields = saved;
    }
  });
});

describe("filter feedback", () => {
  it("shows the active filter as a sentence with a way to clear it, and the server's message beside the condition it names while keeping the last results", async () => {
    let bad = false;
    const { container, root } = await mount((params) =>
      params.filter && bad
        ? jsonResponse(400, {
            "filter.value": ["Not a valid value for status."],
          })
        : jsonResponse(200, page(ROWS)),
    );
    await until(() => container.querySelector("tbody tr") !== null);
    expect(container.querySelector('[aria-label="Active filter"]')).toBeNull();
    await act(async () => press(container, "Add condition"));
    await act(async () =>
      choose(
        container.querySelector<HTMLSelectElement>(
          '[aria-label="Field of condition 1"]',
        )!,
        "status",
      ),
    );
    bad = true;
    await act(async () =>
      choose(
        container.querySelector<HTMLSelectElement>(
          '[aria-label="Value of condition 1"]',
        )!,
        "pending",
      ),
    );
    await until(
      () =>
        container.textContent?.includes("Filter: Status is pending") ?? false,
    );
    await until(
      () =>
        container.querySelector('[role="alert"].cx-filter-problem') !== null,
    );
    expect(container.textContent).toContain(
      "Condition 1: Not a valid value for status.",
    );
    expect(
      container
        .querySelector('[aria-label="Value of condition 1"]')
        ?.getAttribute("aria-invalid"),
    ).toBe("true");
    expect(container.textContent).toContain("shows the last results");
    expect(container.querySelectorAll("tbody tr").length).toBe(2); // the last rows stay
    bad = false;
    await act(async () => press(container, "Clear filter"));
    await until(
      () => container.querySelector('[aria-label="Active filter"]') === null,
    );
    await act(async () => root.unmount());
  });
});

describe("row selection", () => {
  const box = (c: HTMLElement, name: string) =>
    c.querySelector(`input[aria-label="Select ${name}"]`) as HTMLInputElement;

  it("is of the rows in view: announced, cleared by the button and by another page, and pruned when a row leaves", async () => {
    let rows = ROWS;
    const seen: string[][] = [];
    const { container, root } = await mount(
      () => jsonResponse(200, { ...page(rows), total: 60 }),
      {
        selectable: true,
        rowLabel: (row) => String(row.username),
        onSelect: (ids) => void seen.push([...ids]),
      },
    );
    await until(() => container.querySelector("tbody tr") !== null);
    await act(async () => box(container, "ada").click());
    await act(async () => box(container, "ben").click());
    expect(
      container.querySelector('.cx-datagrid__footer [role="status"]')
        ?.textContent,
    ).toContain("2 selected");
    expect(seen.at(-1)).toEqual(["1", "2"]);

    // another page starts with nothing selected
    await act(async () => press(container, "Next"));
    expect(seen.at(-1)).toEqual([]);
    await act(async () => press(container, "Previous"));
    await until(() => container.querySelector("tbody tr") !== null);
    expect(container.textContent).not.toContain("selected");

    // the button clears
    await act(async () => box(container, "ada").click());
    await act(async () => press(container, "Clear selection"));
    expect(seen.at(-1)).toEqual([]);
    expect(box(container, "ada").checked).toBe(false);

    // a row that leaves the list leaves the selection
    await act(async () => box(container, "ada").click());
    await act(async () => box(container, "ben").click());
    rows = [ROWS[1]];
    await act(async () => press(container, "Next"));
    await act(async () => press(container, "Previous"));
    await until(() => container.querySelectorAll("tbody tr").length === 1);
    expect(seen.at(-1)).toEqual([]);
    await act(async () => root.unmount());
  });
});

describe("column picker", () => {
  it("counts what is shown, keeps one column, can show everything and reset to the defaults, and says what it did", async () => {
    window.localStorage.clear();
    const { container, root } = await mount(() =>
      jsonResponse(200, page(ROWS)),
    );
    await until(() => container.querySelector("tbody tr") !== null);
    const legend = () =>
      container.querySelector("fieldset legend")!.textContent;
    expect(legend()).toContain("3 of 4 shown");
    const box = (name: string) =>
      [...container.querySelectorAll<HTMLInputElement>("fieldset input")].find(
        (i) => i.parentElement?.textContent?.includes(name),
      )!;
    const note: string[] = [];
    window.addEventListener("conflux:shell-notice", (e) =>
      note.push((e as CustomEvent<string>).detail),
    );
    await act(async () => box("Status").click());
    await act(async () => box("Applied").click());
    expect(legend()).toContain("1 of 4 shown");
    expect(box("Applicant").disabled).toBe(true); // the last one cannot be hidden
    expect(container.querySelector("fieldset small")?.textContent).toContain(
      "At least one column",
    );
    expect(note).toContain("Status column hidden.");
    await act(async () => press(container, "Show all"));
    expect(legend()).toContain("4 of 4 shown");
    expect(
      [...container.querySelectorAll("button")].find(
        (b) => b.textContent === "Show all",
      )!.disabled,
    ).toBe(true);
    await act(async () => press(container, "Reset columns"));
    expect(legend()).toContain("3 of 4 shown");
    expect(
      [...container.querySelectorAll("button")].find(
        (b) => b.textContent === "Reset columns",
      )!.disabled,
    ).toBe(true);
    await act(async () => root.unmount());
    window.localStorage.clear();
  });
});

describe("rows per page", () => {
  it("is a panel param that asks the server for that many, starts again at page one, and a page past the end lands on the last", async () => {
    const { container, pages, root } = await mountAt(
      "/w/w/participants?page_applications=2",
    );
    await until(() => pages.length > 0);
    const select = container.querySelector<HTMLSelectElement>(
      ".cx-datagrid__size select",
    )!;
    expect(select.value).toBe("25");
    await act(async () => {
      Object.getOwnPropertyDescriptor(
        HTMLSelectElement.prototype,
        "value",
      )!.set!.call(select, "50");
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    await until(() => pages.at(-1)?.limit === "50");
    expect(search()).toBe("?size_applications=50"); // the page param was cleared with the size
    expect(pages.at(-1)?.offset).toBeUndefined();
    await act(async () => root.unmount());
  });
});

describe("transient view in the address", () => {
  const encode = (node: unknown) =>
    btoa(JSON.stringify(node))
      .replaceAll("+", "-")
      .replaceAll("/", "_")
      .replace(/=+$/, "");
  const status = { field: "status", op: "eq", value: "pending" };

  it("opens a link's structured filter, asks the server for it and shows it as the active filter", async () => {
    const { container, pages, root } = await mountAt(
      `/w/w/participants?f_applications=${encode(status)}`,
    );
    await until(() => pages.some((p) => p.filter !== undefined));
    expect(JSON.parse(pages.at(-1)!.filter)).toEqual(status);
    await until(
      () =>
        container.textContent?.includes("Filter: Status is pending") ?? false,
    );
    expect(search()).toContain("f_applications="); // the link stays as it was
    await act(async () => root.unmount());
  });

  it("refuses a link whole when it holds text or does not fit, says so and shows everything", async () => {
    const note: string[] = [];
    window.addEventListener("conflux:shell-notice", (e) =>
      note.push((e as CustomEvent<string>).detail),
    );
    const { container, pages, root } = await mountAt(
      `/w/w/participants?f_applications=${encode({ field: "username", op: "eq", value: "ada" })}`,
    );
    await until(() => pages.length > 0);
    await until(() => note.some((n) => n.includes("could not be used")));
    expect(pages.every((p) => p.filter === undefined)).toBe(true);
    expect(search()).not.toContain("f_applications");
    expect(container.querySelector('[aria-label="Active filter"]')).toBeNull();
    await act(async () => root.unmount());
  });

  it("writes a structured filter to the address, keeps free text out of it and says how to share that", async () => {
    const { container, root } = await mountAt("/w/w/participants");
    await until(() => container.querySelector("tbody tr") !== null);
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
        "approved",
      ),
    );
    await until(() => search().includes("f_applications="));
    const written = new URLSearchParams(search()).get("f_applications")!;
    expect(
      JSON.parse(atob(written.replaceAll("-", "+").replaceAll("_", "/"))),
    ).toEqual({
      field: "status",
      op: "eq",
      value: "approved",
    });
    // typed text: not in the address, and the person is told
    await act(async () =>
      choose(
        container.querySelector<HTMLSelectElement>(
          '[aria-label="Field of condition 1"]',
        )!,
        "username",
      ),
    );
    await act(async () =>
      choose(
        container.querySelector<HTMLInputElement>(
          '[aria-label="Value of condition 1"]',
        )!,
        "ada",
      ),
    );
    await until(() => !search().includes("f_applications"));
    expect(search()).not.toContain("ada");
    await until(
      () => container.textContent?.includes("not in the link") ?? false,
    );
    expect(container.textContent).toContain("Save it as a view to share it.");
    await act(async () => root.unmount());
  });
});

describe("grouping", () => {
  it("lists buckets with counts from the server, opens one with the bucket as a condition, nests a subgroup and keeps the choice in the address", async () => {
    const asked: Record<string, string>[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: unknown) => {
        const url = new URL(String(input), "http://x");
        if (url.pathname.endsWith("/entities/"))
          return jsonResponse(200, CATALOGUE);
        if (url.pathname.includes("/views/")) return jsonResponse(200, []);
        if (url.pathname.includes("/accounts/me/"))
          return jsonResponse(200, { public_id: "u1", memberships: [] });
        const params = Object.fromEntries(url.searchParams);
        asked.push(params);
        if (params.group)
          return jsonResponse(200, {
            ...page([]),
            total: 3,
            group: "status",
            groups: [
              {
                key: "approved",
                label: "approved",
                null: false,
                count: 1,
                ...(params.subgroup
                  ? {
                      subgroups: [
                        { key: null, label: "(none)", null: true, count: 1 },
                      ],
                    }
                  : {}),
              },
              {
                key: "pending",
                label: "pending",
                null: false,
                count: 2,
                ...(params.subgroup
                  ? {
                      subgroups: [
                        { key: null, label: "(none)", null: true, count: 2 },
                      ],
                    }
                  : {}),
              },
            ],
            truncated: false,
          });
        return jsonResponse(200, { ...page(ROWS), total: 2 });
      }),
    );
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    await act(async () =>
      root.render(
        <QueryClientProvider client={createTestQueryClient()}>
          <MemoryRouter
            initialEntries={["/w/w/participants?group_applications=status"]}
          >
            <Where />
            <EntityGrid
              workspaceId="w"
              eventId="e"
              entity="applications"
              label="Applications"
            />
          </MemoryRouter>
        </QueryClientProvider>,
      ),
    );
    await until(() => container.querySelector(".cx-groups__head") !== null);
    const heads = () => [
      ...container.querySelectorAll<HTMLButtonElement>(".cx-groups__head"),
    ];
    expect(heads().map((h) => h.textContent)).toEqual([
      "Status: approved · 1",
      "Status: pending · 2",
    ]);
    expect(container.querySelector("tbody")).toBeNull(); // no rows until a bucket is opened
    expect(heads()[0].getAttribute("aria-expanded")).toBe("false");

    // opening a bucket asks the ordinary query with the bucket's value as a condition
    await act(async () => heads()[1].click());
    await until(() => asked.some((p) => p.filter && p.group === undefined));
    expect(JSON.parse(asked.find((p) => p.filter && !p.group)!.filter)).toEqual(
      {
        field: "status",
        op: "eq",
        value: "pending",
      },
    );
    await until(() => container.querySelector("tbody tr") !== null);

    // a subgroup nests inside, and its bucket is both conditions together
    const then = [
      ...container.querySelectorAll<HTMLSelectElement>("select"),
    ].find((s) => s.parentElement?.textContent?.startsWith("Then by"))!;
    await act(async () => choose(then, "note"));
    expect(search()).toContain("then_applications=note");
    await until(() => asked.some((p) => p.subgroup === "note"));
    expect(search()).toContain("group_applications=status");
    await act(async () => root.unmount());
  });
});
