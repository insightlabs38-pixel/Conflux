// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, useLocation } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../lib/test-http";
import { createTestQueryClient } from "../lib/test-router";
import { recentCommands, themePreference } from "../lib/shellPreferences";
import { AppShell } from "./AppShell";
import { WorkspaceNavigationProvider } from "./WorkspaceNavigation";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
beforeEach(() => window.localStorage.clear());
afterEach(() => {
  vi.unstubAllGlobals();
  document.body.innerHTML = "";
});

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
  return (
    <p data-testid="where">
      {location.pathname + location.search + location.hash}
    </p>
  );
}
function Harness({
  role,
  onSignOut,
}: {
  role: string;
  onSignOut?: () => void;
}) {
  const [client] = useState(createTestQueryClient);
  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <Routes>
          <Route
            path="/w/:workspaceId/:view"
            element={
              <WorkspaceNavigationProvider role={role} workspaceId="w">
                <AppShell role={role} onSignOut={onSignOut}>
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
async function render(
  role: string,
  url: string,
  handlers: Handlers = {},
  onSignOut?: () => void,
) {
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
      if (path.includes("/audit/"))
        return jsonResponse(200, [
          {
            public_id: "a1",
            action: "event.status_changed",
            target_type: "event",
            created_at: new Date().toISOString(),
          },
          {
            public_id: "a2",
            action: "membership.granted",
            target_type: "membership",
            created_at: new Date().toISOString(),
          },
        ]);
      if (path.includes("/views/"))
        return jsonResponse(200, [
          {
            public_id: "v1",
            name: "Late projects",
            entity: "projects",
            mine: true,
          },
        ]);
      if (path.endsWith("/events/") || path.includes("-events/"))
        return jsonResponse(200, EVENTS);
      return jsonResponse(200, { modules: [] });
    }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(<Harness role={role} onSignOut={onSignOut} />),
  );
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 10));
  });
  return { container, root, calls };
}
const open = async () =>
  act(async () =>
    document.querySelector<HTMLButtonElement>(".cx-search-open")!.click(),
  );
const input = () =>
  document.querySelector<HTMLInputElement>(".cx-search input")!;
const type = async (value: string) => {
  await act(async () => {
    Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    )!.set!.call(input(), value);
    input().dispatchEvent(new Event("input", { bubbles: true }));
  });
  // debounced, then the catalogue and each entity: wait until it has answered
  for (let waited = 0; waited < 2000; waited += 50) {
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
    });
    const status = document.querySelector(".cx-search__status")?.textContent;
    if (waited >= 250 && !status?.includes("Searching")) break;
  }
};
const key = async (name: string) =>
  act(async () => {
    input().dispatchEvent(
      new KeyboardEvent("keydown", { key: name, bubbles: true }),
    );
  });
const options = () =>
  [...document.querySelectorAll('[role="option"]')].map((o) => o.textContent);
/** The words of each option, without a shortcut shown beside it. */
const labels = () =>
  [...document.querySelectorAll('[role="option"] > span:first-child')].map(
    (o) => o.textContent,
  );
const groups = () =>
  [...document.querySelectorAll(".cx-search__group")].map((g) => g.textContent);
const where = () =>
  document.querySelector('[data-testid="where"]')?.textContent;
const status = () =>
  document.querySelector(".cx-search__status")?.textContent ?? "";

describe("command palette", () => {
  it("opens with Ctrl+K and closes with it again or with Escape", async () => {
    const { root } = await render("organizer", "/w/w/overview?event=e1");
    expect(document.querySelector(".cx-search")).toBeNull();
    const press = (extra: KeyboardEventInit = {}) =>
      act(async () => {
        document.dispatchEvent(
          new KeyboardEvent("keydown", {
            key: "k",
            ctrlKey: true,
            bubbles: true,
            ...extra,
          }),
        );
      });
    await press();
    expect(document.querySelector(".cx-search")).not.toBeNull();
    expect(document.activeElement).toBe(input());
    await press();
    expect(document.querySelector(".cx-search")).toBeNull();
    await press();
    await act(async () => {
      document.dispatchEvent(
        new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
      );
    });
    expect(document.querySelector(".cx-search")).toBeNull();
    await press({ ctrlKey: false, metaKey: true }); // Cmd+K as well
    expect(document.querySelector(".cx-search")).not.toBeNull();
    await act(async () => root.unmount());
  });

  it("lists the commands by group when nothing is typed, only those this role has", async () => {
    const { root } = await render(
      "participant",
      "/w/w/overview?event=e1",
      {
        catalogue: [],
      },
      () => {},
    );
    await open();
    expect(groups()).toEqual([
      "Go to",
      "Events",
      "Appearance",
      "Help",
      "Account",
    ]);
    expect(labels()).toContain("Go to Team");
    expect(labels()).not.toContain("Go to Event setup"); // an organizer place
    expect(labels()).toContain("Switch to Noether Night");
    expect(labels()).not.toContain("Switch to Gauss Hack"); // already selected
    expect(labels()).toContain("Sign out");
    await act(async () => root.unmount());
  });

  it("goes to a place, switches event and opens preferences through routes.target", async () => {
    const { root } = await render("judge", "/w/w/overview?event=e1&stage=s1", {
      catalogue: [],
    });
    await open();
    await type("review q");
    expect(labels()).toEqual(["Go to Review queue"]);
    expect(options()).toEqual(["Go to Review queueG then Q"]); // the shortcut is shown beside it
    await key("Enter");
    expect(where()).toBe("/w/w/queue?event=e1&stage=s1");
    expect(document.querySelector(".cx-search")).toBeNull();
    await open();
    await type("noether");
    await key("Enter");
    expect(where()).toBe("/w/w/queue?event=e2");
    await open();
    await type("notification pref");
    await key("Enter");
    expect(where()).toBe("/w/w/profile?event=e2#notification-preferences");
    await act(async () => root.unmount());
  });

  it("remembers what was run and offers it first next time", async () => {
    const { root } = await render("judge", "/w/w/overview", { catalogue: [] });
    await open();
    await type("schedule");
    await key("Enter");
    expect(recentCommands("u1", "w")).toEqual(["go.schedule"]);
    await open();
    expect(groups()[0]).toBe("Recent");
    expect(options()[0]).toBe("Go to Schedule & route");
    await act(async () => root.unmount());
  });

  it("changes the theme and signs out through the same canonical paths", async () => {
    const signOut = vi.fn();
    const { root } = await render(
      "judge",
      "/w/w/overview",
      { catalogue: [] },
      signOut,
    );
    await open();
    await type("dark");
    expect(options()).toEqual(["Use the dark theme"]);
    await key("Enter");
    expect(themePreference("u1")).toBe("dark");
    await open();
    await type("sign out");
    await key("Enter");
    expect(signOut).toHaveBeenCalledTimes(1);
    await act(async () => root.unmount());
  });
});

describe("palette record search", () => {
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
      calls.find((p) => p.includes("/entities/projects/"))!,
    );
    expect(projectsCall).toContain('"field":"name"');
    expect(projectsCall).toContain('"op":"contains"');
    expect(projectsCall).toContain("limit=5");
    expect(calls.some((p) => p.includes("/entities/unmapped/"))).toBe(false);
    expect(status()).toContain("Showing the first few");
    await act(async () => root.unmount());
  });

  it("opens a hit at its view and section with the event, keeping typed text out of the URL", async () => {
    const { root } = await render("organizer", "/w/w/overview?event=e1", {
      projects: {
        total: 1,
        rows: [{ id: "p1", name: "Axyl", track: "Hardware" }],
      },
    });
    await open();
    await type("axy");
    await key("ArrowDown");
    await key("ArrowUp");
    await key("Enter");
    expect(where()).toBe("/w/w/participants?event=e1&section=ProjectsGrid");
    await act(async () => root.unmount());
  });

  it("asks no record question of a role whose catalogue is empty", async () => {
    const { root, calls } = await render("judge", "/w/w/overview?event=e1", {
      catalogue: [],
    });
    await open();
    await type("que");
    expect(
      calls.filter(
        (p) => p.includes("/entities/") && !p.endsWith("/entities/"),
      ),
    ).toEqual([]);
    await act(async () => root.unmount());
  });

  it("says when nothing matches, when one entity cannot be searched and when no event is chosen", async () => {
    const none = await render("organizer", "/w/w/overview?event=e1");
    await open();
    await type("qzq");
    expect(status()).toContain("No results for “qzq”.");
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
    expect(status()).toContain("Projects could not be searched.");
    expect(options()).toEqual(["xylapending"]);
    await act(async () => failing.root.unmount());
    document.body.innerHTML = "";
    const noEvent = await render("organizer", "/w/w/overview");
    await open();
    await type("xy");
    expect(status()).toContain("Choose an event to search its records.");
    await act(async () => noEvent.root.unmount());
  });

  it("asks for two characters before searching records", async () => {
    const { root, calls } = await render("organizer", "/w/w/overview?event=e1");
    await open();
    await type("x");
    expect(status()).toContain("at least 2 characters");
    expect(
      calls.some((p) => p.includes("/entities/") && !p.endsWith("/entities/")),
    ).toBe(false);
    await act(async () => root.unmount());
  });
});

describe("pinned views", () => {
  it("offers a pinned view first, opens it at its list with the view selected, and hides a stale pin", async () => {
    window.localStorage.setItem(
      "conflux:v1:u1:w:pinned-views",
      JSON.stringify(["e1:projects:v1", "e1:projects:gone", "e2:projects:v1"]),
    );
    const { root } = await render("organizer", "/w/w/overview?event=e1");
    await open();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50)); // the views are listed by the server
    });
    expect(groups()[0]).toBe("Pinned views");
    expect(labels().filter((label) => label?.startsWith("Open view"))).toEqual([
      "Open view Late projects", // gone no longer exists, and e2's pin is for another event
    ]);
    await type("late");
    await key("Enter");
    expect(where()).toBe(
      "/w/w/participants?event=e1&view_projects=v1&section=ProjectsGrid",
    );
    await act(async () => root.unmount());
  });

  it("offers no pinned group when nothing is pinned", async () => {
    const { root } = await render("organizer", "/w/w/overview?event=e1");
    await open();
    expect(groups()).not.toContain("Pinned views");
    await act(async () => root.unmount());
  });
});

describe("recent actions and recent views", () => {
  it("lists the organizer's own latest audit actions, filters them by what is typed and opens the audit place", async () => {
    const { root, calls } = await render("organizer", "/w/w/overview?event=e1");
    await open();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
    });
    expect(groups()).toContain("Recent actions");
    expect(
      options().filter((o) => o?.startsWith("Event status changed")),
    ).toHaveLength(1);
    expect(
      calls.some((c) => c.includes("/api/v1/audit/w/?mine=1&limit=8")),
    ).toBe(true);
    await type("membership");
    expect(options().some((o) => o?.startsWith("Membership granted"))).toBe(
      true,
    );
    expect(options().some((o) => o?.startsWith("Event status changed"))).toBe(
      false,
    );
    await key("Enter");
    expect(where()).toBe("/w/w/operations?event=e1");
    await act(async () => root.unmount());
  });

  it("asks the audit log nothing for a role that may not read it", async () => {
    const { root, calls } = await render("judge", "/w/w/overview?event=e1", {
      catalogue: [],
    });
    await open();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
    });
    expect(groups()).not.toContain("Recent actions");
    expect(calls.some((c) => c.includes("/audit/"))).toBe(false);
    await act(async () => root.unmount());
  });

  it("offers recently opened views that still exist and are not pinned", async () => {
    window.localStorage.setItem(
      "conflux:v1:u1:w:recent-views",
      JSON.stringify(["e1:projects:v1", "e1:projects:gone"]),
    );
    const { root } = await render("organizer", "/w/w/overview?event=e1");
    await open();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
    });
    expect(groups()).toContain("Recent views");
    expect(labels().filter((l) => l?.startsWith("Open view"))).toEqual([
      "Open view Late projects",
    ]);
    window.localStorage.setItem(
      "conflux:v1:u1:w:pinned-views",
      JSON.stringify(["e1:projects:v1"]),
    );
    await act(async () => root.unmount());
    document.body.innerHTML = "";
    const pinned = await render("organizer", "/w/w/overview?event=e1");
    await open();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
    });
    expect(groups()).toContain("Pinned views");
    expect(groups()).not.toContain("Recent views"); // already pinned, shown once
    await act(async () => pinned.root.unmount());
  });
});
