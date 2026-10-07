// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../lib/test-http";
import { createTestQueryClient } from "../lib/test-router";
import { favoriteEvents, recentEvents } from "../lib/shellPreferences";
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
  { public_id: "e3", name: "Turing Jam" },
];
const ME = {
  public_id: "u1",
  username: "org",
  memberships: [
    { workspace: "w", workspace_name: "Lab", role: "organizer" },
    { workspace: "w2", workspace_name: "Other lab", role: "judge" },
  ],
};

function Harness() {
  const [client] = useState(createTestQueryClient);
  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <Routes>
          <Route
            path="/w/:workspaceId/:view"
            element={
              <WorkspaceNavigationProvider role="organizer" workspaceId="w">
                <AppShell role="organizer" username="org">
                  content
                </AppShell>
              </WorkspaceNavigationProvider>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

async function render(url: string, events: unknown = EVENTS) {
  window.history.replaceState({}, "", url);
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown) => {
      const path = String(input);
      if (path.includes("/accounts/me/")) return jsonResponse(200, ME);
      if (path.endsWith("/events/"))
        return events instanceof Error
          ? jsonResponse(503, { detail: "down" })
          : jsonResponse(200, events);
      return jsonResponse(200, { modules: [] });
    }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => root.render(<Harness />));
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 10));
  });
  return { container, root };
}
const summary = (c: HTMLElement) =>
  c.querySelector<HTMLElement>(".cx-switcher summary")!;
const rows = (c: HTMLElement, section: string) =>
  [
    ...c.querySelectorAll(`.cx-switcher section[aria-label="${section}"] li`),
  ].map((li) => li.querySelector(".cx-switcher__choice")?.textContent);

describe("event switcher", () => {
  it("shows the event in the URL, remembers it as recent and lists the others", async () => {
    const { container, root } = await render("/w/w/overview?event=e2");
    expect(summary(container).textContent).toContain("Noether Night");
    expect(recentEvents("u1", "w")).toEqual(["e2"]);
    expect(rows(container, "All events")).toEqual([
      "Gauss Hack",
      "Noether Night",
      "Turing Jam",
    ]);
    await act(async () => root.unmount());
  });

  it("asks to choose when none is selected and does not trust an unlisted id", async () => {
    const { container, root } = await render("/w/w/overview?event=ghost");
    expect(summary(container).textContent).toContain("Choose an event");
    expect(recentEvents("u1", "w")).toEqual([]);
    await act(async () => root.unmount());
  });

  it("stars an event, then lists it under Favorites and keeps it out of Other events", async () => {
    const { container, root } = await render("/w/w/overview");
    const star = container.querySelector<HTMLButtonElement>(
      'button[aria-label="Favorite Turing Jam"]',
    )!;
    expect(star.getAttribute("aria-pressed")).toBe("false");
    await act(async () => star.click());
    expect(favoriteEvents("u1", "w")).toEqual(["e3"]);
    expect(rows(container, "Favorite events")).toEqual(["Turing Jam"]);
    expect(rows(container, "All events")).toEqual([
      "Gauss Hack",
      "Noether Night",
    ]);
    await act(async () => root.unmount());
  });

  it("ignores a stored favorite that the server no longer lists", async () => {
    window.localStorage.setItem(
      "conflux:v1:u1:w:favorite-events",
      JSON.stringify(["gone", "e1"]),
    );
    const { container, root } = await render("/w/w/overview");
    expect(rows(container, "Favorite events")).toEqual(["Gauss Hack"]);
    await act(async () => root.unmount());
  });

  it("links an event to the same view with the event param and no dependent context", async () => {
    const { container, root } = await render(
      "/w/w/judging?event=e1&stage=s1&plan=p1",
    );
    const link = [
      ...container.querySelectorAll<HTMLAnchorElement>(".cx-switcher__choice"),
    ].find((a) => a.textContent === "Turing Jam")!;
    expect(link.getAttribute("href")).toBe("/w/w/judging?event=e3");
    await act(async () => root.unmount());
  });

  it("offers the person's other workspaces", async () => {
    const { container, root } = await render("/w/w/overview");
    expect(rows(container, "Workspaces")).toEqual(["Lab", "Other lab"]);
    await act(async () => root.unmount());
  });

  it("says so, with a retry, when the events cannot load, and when there are none", async () => {
    const down = await render("/w/w/overview", new Error("down"));
    expect(
      down.container.querySelector(".cx-switcher [role=alert]")?.textContent,
    ).toContain("Could not load events");
    await act(async () => down.root.unmount());
    const none = await render("/w/w/overview", []);
    expect(summary(none.container).textContent).toContain("No events");
    expect(none.container.textContent).toContain(
      "No events in this workspace yet.",
    );
    await act(async () => none.root.unmount());
  });

  it("closes on Escape and returns focus to its button", async () => {
    const { container, root } = await render("/w/w/overview");
    const details =
      container.querySelector<HTMLDetailsElement>(".cx-switcher")!;
    details.open = true;
    await act(async () => {
      container
        .querySelector(".cx-switcher__choice")!
        .dispatchEvent(
          new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
        );
    });
    expect(details.open).toBe(false);
    await act(async () => root.unmount());
  });
});
