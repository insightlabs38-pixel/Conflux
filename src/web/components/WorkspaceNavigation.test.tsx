// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { createTestQueryClient } from "../lib/test-router";
import { AppShell } from "./AppShell";
import {
  Destination,
  DestinationLink,
  WorkspaceNavigationProvider,
} from "./WorkspaceNavigation";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

// The real history API (happy-dom), so URL changes and popstate behave as in a browser.
function Harness({
  role,
  children,
}: {
  role: string;
  children: React.ReactNode;
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
                {children}
              </WorkspaceNavigationProvider>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
const click = (element: Element) =>
  element.dispatchEvent(
    new MouseEvent("click", { bubbles: true, cancelable: true, button: 0 }),
  );

describe("workspace destinations", () => {
  it("keeps drafts mounted while navigation updates the URL, active state and visible destination", () => {
    window.history.replaceState({}, "", "/w/w/overview?event=e");
    vi.stubGlobal("requestAnimationFrame", (fn: () => void) => {
      fn();
      return 0;
    });
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    act(() =>
      root.render(
        <Harness role="participant">
          <AppShell role="participant">
            <Destination id="overview">Overview</Destination>
            <Destination id="project">
              <input aria-label="Draft" defaultValue="" />
            </Destination>
          </AppShell>
        </Harness>,
      ),
    );
    const project = container.querySelector<HTMLAnchorElement>(
      'nav[aria-label="Primary"] a[href="/w/w/project?event=e"]',
    )!;
    act(() => click(project));
    const input = container.querySelector<HTMLInputElement>("input")!;
    input.value = "Unsaved project";
    expect(input.closest<HTMLElement>(".cx-destination")!.hidden).toBe(false);
    expect(project.getAttribute("aria-current")).toBe("page");
    expect(window.location.pathname).toBe("/w/w/project");
    expect(window.location.search).toBe("?event=e");
    const overview = container.querySelector<HTMLAnchorElement>(
      'nav[aria-label="Primary"] a[href="/w/w/overview?event=e"]',
    )!;
    act(() => click(overview));
    expect(input.closest<HTMLElement>(".cx-destination")!.hidden).toBe(true);
    act(() => click(project));
    expect(container.querySelector("input")).toBe(input);
    expect(input.value).toBe("Unsaved project");
    act(() => root.unmount());
    container.remove();
  });
  it("carries the context params to other views but not panel state", () => {
    window.history.replaceState(
      {},
      "",
      "/w/w/overview?event=e&stage=s&plan=p&invite=t&project=x&q=ada&page=2",
    );
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    act(() =>
      root.render(
        <Harness role="participant">
          <AppShell role="participant">
            <Destination id="overview">Overview</Destination>
          </AppShell>
        </Harness>,
      ),
    );
    const link = container.querySelector<HTMLAnchorElement>(
      'nav[aria-label="Primary"] a[href^="/w/w/project"]',
    )!;
    expect(link.getAttribute("href")).toBe(
      "/w/w/project?event=e&stage=s&plan=p&invite=t",
    );
    act(() => root.unmount());
    container.remove();
  });
  it("does not expose organizer destinations to a participant and responds to browser history", () => {
    window.history.replaceState({}, "", "/w/w/overview");
    const container = document.createElement("div");
    const root = createRoot(container);
    act(() =>
      root.render(
        <Harness role="participant">
          <AppShell role="participant">
            <Destination id="overview">Overview</Destination>
            <Destination id="team">Team</Destination>
          </AppShell>
        </Harness>,
      ),
    );
    expect(container.querySelector('a[href*="/operations"]')).toBeNull();
    expect(
      container.querySelector<HTMLElement>(".cx-destination")!.hidden,
    ).toBe(false);
    // Back/forward: the URL is the state, so history navigation changes the visible destination.
    act(() => {
      window.history.pushState({}, "", "/w/w/team");
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    expect(
      container.querySelectorAll<HTMLElement>(".cx-destination")[1].hidden,
    ).toBe(false);
    act(() => {
      window.history.back();
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    act(() => root.unmount());
  });
  it("preserves native modified-link navigation without intercepting open-in-new-tab", () => {
    window.history.replaceState({}, "", "/w/w/overview");
    const container = document.createElement("div");
    const root = createRoot(container);
    act(() =>
      root.render(
        <Harness role="judge">
          <DestinationLink id="queue">Queue</DestinationLink>
        </Harness>,
      ),
    );
    const modified = new MouseEvent("click", {
      bubbles: true,
      cancelable: true,
      ctrlKey: true,
    });
    const push = vi.spyOn(window.history, "pushState");
    act(() => container.querySelector("a")!.dispatchEvent(modified));
    expect(modified.defaultPrevented).toBe(false);
    expect(push).not.toHaveBeenCalled();
    expect(container.querySelector("a")!.getAttribute("href")).toBe(
      "/w/w/queue",
    );
    // A plain click is handled in-app.
    act(() => click(container.querySelector("a")!));
    expect(window.location.pathname).toBe("/w/w/queue");
    push.mockRestore();
    act(() => root.unmount());
  });
  it("resolves a view the role does not have to the overview", () => {
    window.history.replaceState({}, "", "/w/w/operations");
    const container = document.createElement("div");
    const root = createRoot(container);
    act(() =>
      root.render(
        <Harness role="participant">
          <AppShell role="participant">
            <Destination id="overview">Overview</Destination>
            <Destination id="operations">Operations</Destination>
          </AppShell>
        </Harness>,
      ),
    );
    const visible = [
      ...container.querySelectorAll<HTMLElement>(".cx-destination"),
    ].filter((el) => !el.hidden);
    expect(visible.map((el) => el.textContent)).toEqual(["Overview"]);
    act(() => root.unmount());
  });
});

it("loads optional profile content only when visited and retains its draft afterwards", async () => {
  window.history.replaceState({}, "", "/w/w/overview");
  vi.stubGlobal("requestAnimationFrame", (fn: () => void) => {
    fn();
    return 0;
  });
  const host = document.createElement("div");
  document.body.appendChild(host);
  const root = createRoot(host);
  await act(async () =>
    root.render(
      <Harness role="participant">
        <AppShell role="participant">
          <Destination id="profile" lazy>
            <input aria-label="Profile draft" defaultValue="" />
          </Destination>
        </AppShell>
      </Harness>,
    ),
  );
  expect(host.querySelector("input")).toBeNull();
  const link = host.querySelector<HTMLAnchorElement>(
    'nav[aria-label="Primary"] a[href="/w/w/profile"]',
  )!;
  await act(async () => click(link));
  const input = host.querySelector<HTMLInputElement>("input")!;
  input.value = "Unsaved bio";
  await act(async () =>
    click(
      host.querySelector<HTMLAnchorElement>(
        'nav[aria-label="Primary"] a[href="/w/w/overview"]',
      )!,
    ),
  );
  await act(async () => click(link));
  expect(host.querySelector("input")).toBe(input);
  expect(input.value).toBe("Unsaved bio");
  await act(async () => root.unmount());
  host.remove();
});

describe("the phone's bottom bar", () => {
  it("shows every place when there are at most five", async () => {
    const { barDestinations, roleDestinations } =
      await import("./WorkspaceNavigation");
    for (const role of ["judge", "mentor", "volunteer"]) {
      const { bar, more } = barDestinations(roleDestinations[role]);
      expect(more).toBe(false);
      expect(bar.map((item) => item.id)).toEqual(
        roleDestinations[role].map((item) => item.id),
      );
    }
  });

  it("keeps four places and More when there are more than five", async () => {
    const { barDestinations, roleDestinations } =
      await import("./WorkspaceNavigation");
    const organizer = barDestinations(roleDestinations.organizer);
    expect(organizer.more).toBe(true);
    expect(organizer.bar.map((item) => item.short ?? item.label)).toEqual([
      "Overview",
      "People",
      "Judging",
      "On-site",
    ]);
    const participant = barDestinations(roleDestinations.participant);
    expect(participant.bar).toHaveLength(4);
    expect(participant.more).toBe(true);
  });

  it("never offers more than four places plus More, and only places the role has", async () => {
    const { barDestinations, roleDestinations } =
      await import("./WorkspaceNavigation");
    for (const [role, places] of Object.entries(roleDestinations)) {
      const { bar, more } = barDestinations(places);
      expect(bar.length + (more ? 1 : 0)).toBeLessThanOrEqual(5);
      for (const item of bar)
        expect(places.some((p) => p.id === item.id)).toBe(true);
      expect(role).toBeTruthy();
    }
  });
});
