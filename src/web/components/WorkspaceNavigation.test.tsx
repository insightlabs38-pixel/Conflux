// @vitest-environment happy-dom
import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";
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

describe("workspace destinations", () => {
  it("keeps drafts mounted while navigation updates the URL, active state and visible destination", () => {
    window.history.replaceState({}, "", "/app/?workspace=w&event=e");
    vi.stubGlobal("requestAnimationFrame", (fn: () => void) => {
      fn();
      return 0;
    });
    const container = document.createElement("div");
    document.body.appendChild(container);
    const root = createRoot(container);
    act(() =>
      root.render(
        <WorkspaceNavigationProvider role="participant">
          <AppShell role="participant">
            <Destination id="overview">Overview</Destination>
            <Destination id="project">
              <input aria-label="Draft" defaultValue="" />
            </Destination>
          </AppShell>
        </WorkspaceNavigationProvider>,
      ),
    );
    const project = container.querySelector<HTMLAnchorElement>(
      'nav[aria-label="Primary"] a[href*="view=project"]',
    )!;
    act(() =>
      project.dispatchEvent(
        new MouseEvent("click", { bubbles: true, button: 0 }),
      ),
    );
    const input = container.querySelector<HTMLInputElement>("input")!;
    input.value = "Unsaved project";
    expect(input.closest<HTMLElement>(".cx-destination")!.hidden).toBe(false);
    expect(project.getAttribute("aria-current")).toBe("page");
    expect(window.location.search).toContain("event=e");
    expect(window.location.search).toContain("view=project");
    const overview = container.querySelector<HTMLAnchorElement>(
      'nav[aria-label="Primary"] a[href*="view=overview"]',
    )!;
    act(() =>
      overview.dispatchEvent(
        new MouseEvent("click", { bubbles: true, button: 0 }),
      ),
    );
    expect(input.closest<HTMLElement>(".cx-destination")!.hidden).toBe(true);
    act(() =>
      project.dispatchEvent(
        new MouseEvent("click", { bubbles: true, button: 0 }),
      ),
    );
    expect(container.querySelector("input")).toBe(input);
    expect(input.value).toBe("Unsaved project");
    act(() => root.unmount());
    container.remove();
  });
  it("does not expose organizer destinations to a participant and responds to browser history", () => {
    window.history.replaceState({}, "", "/app/?workspace=w&view=operations");
    const container = document.createElement("div");
    const root = createRoot(container);
    act(() =>
      root.render(
        <WorkspaceNavigationProvider role="participant">
          <AppShell role="participant">
            <Destination id="overview">Overview</Destination>
            <Destination id="team">Team</Destination>
          </AppShell>
        </WorkspaceNavigationProvider>,
      ),
    );
    expect(container.querySelector('a[href*="view=operations"]')).toBeNull();
    expect(
      container.querySelector<HTMLElement>(".cx-destination")!.hidden,
    ).toBe(false);
    act(() => {
      window.history.replaceState({}, "", "/app/?workspace=w&view=team");
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    expect(
      container.querySelectorAll<HTMLElement>(".cx-destination")[1].hidden,
    ).toBe(false);
    act(() => root.unmount());
  });
  it("preserves native modified-link navigation without intercepting open-in-new-tab", () => {
    window.history.replaceState({}, "", "/app/?workspace=w");
    const container = document.createElement("div");
    const root = createRoot(container);
    act(() =>
      root.render(
        <WorkspaceNavigationProvider role="judge">
          <DestinationLink id="queue">Queue</DestinationLink>
        </WorkspaceNavigationProvider>,
      ),
    );
    const click = new MouseEvent("click", {
      bubbles: true,
      cancelable: true,
      ctrlKey: true,
    });
    const push = vi.spyOn(window.history, "pushState");
    act(() => container.querySelector("a")!.dispatchEvent(click));
    expect(click.defaultPrevented).toBe(false);
    expect(push).not.toHaveBeenCalled();
    push.mockRestore();
    act(() => root.unmount());
  });
});

it("loads optional profile content only when visited and retains its draft afterwards", async () => {
  window.history.replaceState({}, "", "/app/?workspace=w");
  vi.stubGlobal("requestAnimationFrame", (fn: () => void) => {
    fn();
    return 0;
  });
  const host = document.createElement("div");
  document.body.appendChild(host);
  const root = createRoot(host);
  await act(async () =>
    root.render(
      <WorkspaceNavigationProvider role="participant">
        <AppShell role="participant">
          <Destination id="profile" lazy>
            <input aria-label="Profile draft" defaultValue="" />
          </Destination>
        </AppShell>
      </WorkspaceNavigationProvider>,
    ),
  );
  expect(host.querySelector("input")).toBeNull();
  const link = host.querySelector<HTMLAnchorElement>(
    'nav[aria-label="Primary"] a[href*="view=profile"]',
  )!;
  await act(async () =>
    link.dispatchEvent(new MouseEvent("click", { bubbles: true, button: 0 })),
  );
  const input = host.querySelector<HTMLInputElement>("input")!;
  input.value = "Unsaved bio";
  await act(async () =>
    host
      .querySelector<HTMLAnchorElement>(
        'nav[aria-label="Primary"] a[href*="view=overview"]',
      )!
      .dispatchEvent(new MouseEvent("click", { bubbles: true, button: 0 })),
  );
  await act(async () =>
    link.dispatchEvent(new MouseEvent("click", { bubbles: true, button: 0 })),
  );
  expect(host.querySelector("input")).toBe(input);
  expect(input.value).toBe("Unsaved bio");
  await act(async () => root.unmount());
  host.remove();
});
