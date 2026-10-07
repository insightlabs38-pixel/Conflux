// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, useLocation } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../lib/test-http";
import { createTestQueryClient } from "../lib/test-router";
import { AppShell } from "./AppShell";
import { WorkspaceNavigationProvider } from "./WorkspaceNavigation";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
beforeEach(() => window.localStorage.clear());
afterEach(() => vi.unstubAllGlobals());

const EVENTS = [
  { public_id: "e1", name: "Gauss Hack" },
  { public_id: "e2", name: "Noether Night" },
];
const CATALOGUE = [
  { key: "projects", label: "Projects", fields: [], default_sort: [] },
  { key: "applications", label: "Applications", fields: [], default_sort: [] },
  { key: "unmapped", label: "Unmapped", fields: [], default_sort: [] },
];

function Where() {
  const location = useLocation();
  return <p data-testid="where">{location.pathname + location.search}</p>;
}
function Harness({ role }: { role: string }) {
  const [client] = useState(createTestQueryClient);
  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <Routes>
          <Route
            path="/w/:workspaceId/:view"
            element={
              <WorkspaceNavigationProvider role={role} workspaceId="w">
                <AppShell role={role}>
                  <Where />
                </AppShell>
              </WorkspaceNavigationProvider>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

type Handlers = {
  catalogue?: unknown;
  projects?: unknown;
  applications?: unknown;
};
async function render(role: string, url: string, handlers: Handlers = {}) {
  window.history.replaceState({}, "", url);
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown) => {
      const path = String(input);
      calls.push(path);
      if (path.includes("/accounts/me/"))
        return jsonResponse(200, { public_id: "u1", memberships: [] });
      if (path.endsWith("/entities/"))
        return jsonResponse(200, handlers.catalogue ?? CATALOGUE);
      if (path.includes("/entities/projects/"))
        return handlers.projects instanceof Error
          ? jsonResponse(500, { detail: "boom" })
          : jsonResponse(200, handlers.projects ?? { total: 0, rows: [] });
      if (path.includes("/entities/applications/"))
        return jsonResponse(
          200,
          handlers.applications ?? { total: 0, rows: [] },
        );
      if (path.endsWith("/events/") || path.includes("-events/"))
        return jsonResponse(200, EVENTS);
      return jsonResponse(200, { modules: [] });
    }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => root.render(<Harness role={role} />));
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 10));
  });
  return { container, root, calls };
}
const open = async () => {
  await act(async () =>
    document.querySelector<HTMLButtonElement>(".cx-search-open")!.click(),
  );
};
const type = async (value: string) => {
  const input = document.querySelector<HTMLInputElement>(".cx-search input")!;
  await act(async () => {
    Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    )!.set!.call(input, value);
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
  // the search is debounced, then reads the catalogue and each entity: wait until it has answered
  for (let waited = 0; waited < 2000; waited += 50) {
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
    });
    const status = document.querySelector(".cx-search__status")?.textContent;
    if (waited >= 250 && !status?.includes("Searching")) break;
  }
};
const options = () =>
  [...document.querySelectorAll('[role="option"]')].map((o) => o.textContent);
const groups = () =>
  [...document.querySelectorAll(".cx-search__group")].map((g) => g.textContent);

describe("global search", () => {
  it("finds places and events by name for any role, with no record search", async () => {
    const { root, calls } = await render("judge", "/w/w/overview?event=e1", {
      catalogue: [], // what the server returns to a role that may query nothing
    });
    await open();
    await type("ga");
    expect(groups()).toEqual(["Events"]);
    expect(options()).toEqual(["Gauss Hack"]);
    await type("que");
    expect(groups()).toEqual(["Places"]);
    expect(options()).toEqual(["Review queue"]);
    // the judge's catalogue is not asked for records they may not see
    expect(
      calls.filter(
        (path) => path.includes("/entities/") && !path.endsWith("/entities/"),
      ),
    ).toEqual([]);
    await act(async () => root.unmount());
  });

  it("finds records of the selected event through the entity query, by group", async () => {
    const { root, calls } = await render(
      "organizer",
      "/w/w/overview?event=e1",
      {
        projects: {
          total: 7,
          rows: [{ id: "p1", name: "Axyl", track: "Hardware" }],
        },
        applications: {
          total: 1,
          rows: [{ id: "a1", username: "xyla", status: "pending" }],
        },
      },
    );
    await open();
    await type("xy");
    expect(groups()).toEqual(["Projects", "Applications"]);
    expect(options()).toEqual(["AxylHardware", "xylapending"]);
    const projectsCall = decodeURIComponent(
      calls.find((path) => path.includes("/entities/projects/"))!,
    );
    expect(projectsCall).toContain('"field":"name"');
    expect(projectsCall).toContain('"op":"contains"');
    expect(projectsCall).toContain('"value":"xy"');
    expect(projectsCall).toContain("limit=5");
    // an entity without a search target is never asked
    expect(calls.some((path) => path.includes("/entities/unmapped/"))).toBe(
      false,
    );
    expect(document.querySelector(".cx-search__status")?.textContent).toContain(
      "Showing the first few",
    );
    await act(async () => root.unmount());
  });

  it("opens a hit at its view and section with the event, keeping the typed text out of the URL", async () => {
    const { root } = await render("organizer", "/w/w/overview?event=e1", {
      projects: {
        total: 1,
        rows: [{ id: "p1", name: "Axyl", track: "Hardware" }],
      },
    });
    await open();
    await type("axy");
    await act(async () => {
      document
        .querySelector(".cx-search input")!
        .dispatchEvent(
          new KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }),
        );
    });
    await act(async () => {
      document
        .querySelector(".cx-search input")!
        .dispatchEvent(
          new KeyboardEvent("keydown", { key: "ArrowUp", bubbles: true }),
        );
      document
        .querySelector(".cx-search input")!
        .dispatchEvent(
          new KeyboardEvent("keydown", { key: "Enter", bubbles: true }),
        );
    });
    expect(document.querySelector('[data-testid="where"]')?.textContent).toBe(
      "/w/w/participants?event=e1&section=ProjectsGrid",
    );
    expect(document.querySelector(".cx-search")).toBeNull(); // closed
    await act(async () => root.unmount());
  });

  it("says when nothing matches, when one entity cannot be searched and when no event is chosen", async () => {
    const none = await render("organizer", "/w/w/overview?event=e1");
    await open();
    await type("zzz");
    expect(document.querySelector(".cx-search__status")?.textContent).toContain(
      "No results for “zzz”.",
    );
    await act(async () => none.root.unmount());
    document.body.innerHTML = "";
    const failing = await render("organizer", "/w/w/overview?event=e1", {
      projects: new Error("boom"),
      applications: {
        total: 1,
        rows: [{ id: "a1", username: "xyla", status: "pending" }],
      },
    });
    await open();
    await type("xy");
    expect(document.querySelector(".cx-search__status")?.textContent).toContain(
      "Projects could not be searched.",
    );
    expect(options()).toEqual(["xylapending"]); // the other entity still answers
    await act(async () => failing.root.unmount());
    document.body.innerHTML = "";
    const noEvent = await render("organizer", "/w/w/overview");
    await open();
    await type("xy");
    expect(document.querySelector(".cx-search__status")?.textContent).toContain(
      "Choose an event to search its records.",
    );
    await act(async () => noEvent.root.unmount());
  });

  it("asks for two characters before searching records", async () => {
    const { root, calls } = await render("organizer", "/w/w/overview?event=e1");
    await open();
    await type("a");
    expect(document.querySelector(".cx-search__status")?.textContent).toContain(
      "at least 2 characters",
    );
    expect(calls.some((path) => path.includes("/entities/"))).toBe(false);
    await act(async () => root.unmount());
  });
});
