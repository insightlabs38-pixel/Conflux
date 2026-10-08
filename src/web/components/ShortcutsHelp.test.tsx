// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, useLocation } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../lib/test-http";
import { createTestQueryClient } from "../lib/test-router";
import { singleKeyShortcuts } from "../lib/shellPreferences";
import { AppShell } from "./AppShell";
import { WorkspaceNavigationProvider } from "./WorkspaceNavigation";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
beforeEach(() => window.localStorage.clear());
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
  document.body.innerHTML = "";
});

function Where() {
  const location = useLocation();
  return (
    <p data-testid="where">
      {location.pathname + location.search}
      <input aria-label="Note" />
    </p>
  );
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
async function render(role: string, url = "/w/w/overview?event=e1") {
  window.history.replaceState({}, "", url);
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown) => {
      const path = String(input);
      if (path.includes("/accounts/me/"))
        return jsonResponse(200, { public_id: "u1", memberships: [] });
      if (path.endsWith("/events/") || path.includes("-events/"))
        return jsonResponse(200, [{ public_id: "e1", name: "Gauss Hack" }]);
      if (path.endsWith("/entities/")) return jsonResponse(200, []);
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
  return { container, root };
}
const press = (
  key: string,
  target: Element | Document = document,
  extra: KeyboardEventInit = {},
) =>
  act(async () => {
    target.dispatchEvent(
      new KeyboardEvent("keydown", { key, bubbles: true, ...extra }),
    );
  });
const where = () =>
  document.querySelector('[data-testid="where"]')?.firstChild?.textContent;
const dialog = () => document.querySelector('[role="dialog"]');

describe("keyboard shortcuts", () => {
  it("? opens the help listing this role's go-to keys, read from the registry", async () => {
    const { root } = await render("organizer");
    expect(dialog()).toBeNull();
    await press("?");
    expect(dialog()?.getAttribute("aria-labelledby")).toBeTruthy();
    const text = dialog()!.textContent!;
    expect(text).toContain("Keyboard shortcuts");
    expect(text).toContain("G then J");
    expect(text).toContain("Go to Judging");
    expect(text).toContain("G then P");
    expect(text).toContain("Show keyboard shortcuts");
    expect(text).toContain("Search or run a command");
    expect(text).not.toContain("Go to Review queue"); // a judge place
    await act(async () => root.unmount());
  });

  it("G then a letter goes to that place; a lone letter, a wrong second key and a timeout do nothing", async () => {
    const { root } = await render("organizer");
    vi.useFakeTimers(); // after the render, which waits on a real timer
    await press("j");
    expect(where()).toBe("/w/w/overview?event=e1");
    await press("g");
    await press("j");
    expect(where()).toBe("/w/w/judging?event=e1");
    await press("g");
    await press("Escape");
    await press("p");
    expect(where()).toBe("/w/w/judging?event=e1");
    await press("g");
    await act(async () => {
      vi.advanceTimersByTime(2000);
    });
    await press("p");
    expect(where()).toBe("/w/w/judging?event=e1");
    await press("g");
    await press("z"); // no place has z
    expect(where()).toBe("/w/w/judging?event=e1");
    vi.useRealTimers();
    await act(async () => root.unmount());
  });

  it("does nothing while typing, with a modifier or inside a dialog", async () => {
    const { root } = await render("organizer");
    const input = document.querySelector("input")!;
    await press("?", input);
    expect(dialog()).toBeNull();
    await press("g", input);
    await press("j", input);
    expect(where()).toBe("/w/w/overview?event=e1");
    await press("?", document, { ctrlKey: true });
    expect(dialog()).toBeNull();
    await press("?");
    expect(dialog()).not.toBeNull();
    await press("g");
    await press("j"); // a dialog is open: the keys belong to it
    expect(where()).toBe("/w/w/overview?event=e1");
    await act(async () => root.unmount());
  });

  it("can be switched off, and then only the Ctrl and Cmd keys remain", async () => {
    const { root } = await render("judge");
    await press("?");
    const box = dialog()!.querySelector<HTMLInputElement>(
      'input[type="checkbox"]',
    )!;
    expect(box.checked).toBe(true);
    await act(async () => box.click());
    expect(singleKeyShortcuts("u1")).toBe(false);
    expect(dialog()!.textContent).toContain("Single-key shortcuts are off");
    expect(
      [...dialog()!.querySelectorAll(".cx-shortcuts kbd")].map(
        (k) => k.textContent,
      ),
    ).not.toContainEqual(expect.stringContaining("G then")); // the keys are no longer listed
    await act(async () => {
      dialog()!
        .querySelector<HTMLButtonElement>(".cx-consequence__actions button")!
        .click();
    });
    expect(dialog()).toBeNull();
    await press("?");
    expect(dialog()).toBeNull(); // off
    await press("g");
    await press("q");
    expect(where()).toBe("/w/w/overview?event=e1");
    await act(async () => root.unmount());
  });

  it("opens from the account menu", async () => {
    const { root } = await render("participant");
    await act(async () =>
      [
        ...document.querySelectorAll<HTMLButtonElement>(
          ".cx-account__shortcuts",
        ),
      ][0].click(),
    );
    expect(dialog()?.textContent).toContain("G then T"); // the participant's Team
    await act(async () => root.unmount());
  });

  it("keeps a half-typed chord when the shell re-renders (data arriving) between the two keys", async () => {
    const { root } = await render("organizer");
    await press("g");
    // the navigation context changes identity as the page loads: a new location, a new href
    await act(async () => {
      window.history.pushState({}, "", "/w/w/overview?event=e1&x=1");
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    await press("j");
    expect(where()).toBe("/w/w/judging?event=e1");
    await act(async () => root.unmount());
  });
});
