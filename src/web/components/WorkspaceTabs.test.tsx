// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot } from "react-dom/client";
import { QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Link, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDraft } from "../hooks/useDraft";
import { discardDrafts, hasDrafts } from "../lib/drafts";
import { jsonResponse } from "../lib/test-http";
import { createTestQueryClient } from "../lib/test-router";
import { workspaceTabs } from "../lib/shellPreferences";
import { AppShell } from "./AppShell";
import {
  useWorkspaceNavigation,
  WorkspaceNavigationProvider,
} from "./WorkspaceNavigation";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
beforeEach(() => {
  window.localStorage.clear();
  discardDrafts();
});
afterEach(() => vi.unstubAllGlobals());

function Form() {
  const [text, setText, state] = useDraft("note", "", "Event note");
  return (
    <form>
      <input
        aria-label="Note"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <button type="button" onClick={state.saved}>
        Save
      </button>
    </form>
  );
}

function Page() {
  const view = useWorkspaceNavigation()!.view;
  return (
    <div>
      <Link to="/w/w/overview?event=e1">to overview</Link>
      <Link to="/w/w/participants?event=e1">to participants</Link>
      {view === "participants" ? <Form /> : <p>Overview page</p>}
    </div>
  );
}

function Harness({ onSignOut }: { onSignOut?: () => void }) {
  const [client] = useState(createTestQueryClient);
  return (
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <Routes>
          <Route
            path="/w/:workspaceId/:view"
            element={
              <WorkspaceNavigationProvider role="organizer" workspaceId="w">
                <AppShell role="organizer" onSignOut={onSignOut}>
                  <Page />
                </AppShell>
              </WorkspaceNavigationProvider>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

async function mount(onSignOut?: () => void) {
  window.history.replaceState({}, "", "/w/w/overview?event=e1");
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown) => {
      const path = String(input);
      if (path.includes("/accounts/me/"))
        return jsonResponse(200, { public_id: "u1", memberships: [] });
      if (path.endsWith("/events/") || path.includes("-events/"))
        return jsonResponse(200, [{ public_id: "e1", name: "Gauss Hack" }]);
      return jsonResponse(200, { modules: [] });
    }),
  );
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () => root.render(<Harness onSignOut={onSignOut} />));
  await act(async () => new Promise((resolve) => setTimeout(resolve, 20)));
  return { container, root };
}
const link = (text: string) =>
  [...document.querySelectorAll("a")].find((a) => a.textContent === text)!;
const click = (el: Element) =>
  act(async () => {
    (el as HTMLElement).click();
    await new Promise((resolve) => setTimeout(resolve, 5));
  });
const note = () =>
  document.querySelector<HTMLInputElement>('input[aria-label="Note"]')!;
const type = (value: string) =>
  act(async () => {
    Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype,
      "value",
    )!.set!.call(note(), value);
    note().dispatchEvent(new Event("input", { bubbles: true }));
  });
const tabs = () => document.querySelector('nav[aria-label="Open places"]');
const button = (text: string) =>
  [...document.querySelectorAll("button")].find((b) => b.textContent === text)!;

describe("workspace tabs and drafts", () => {
  it("shows no tabs until there is something to show", async () => {
    const { root } = await mount();
    expect(tabs()).toBeNull();
    await act(async () => root.unmount());
  });

  it("keeps an edit when the person goes elsewhere and back, marks the place, and a save clears it", async () => {
    const { root } = await mount();
    await click(link("to participants"));
    await type("remember me");
    expect(hasDrafts()).toBe(true);
    expect(tabs()?.textContent).toContain("Participants & teams · Gauss Hack");
    expect(tabs()?.textContent).toContain("unsaved changes");

    await click(link("to overview"));
    expect(document.body.textContent).toContain("Overview page");
    expect(tabs()?.textContent).toContain("unsaved changes"); // the tab remains while away

    await click(link("to participants"));
    expect(note().value).toBe("remember me");

    await click(button("Save"));
    expect(hasDrafts()).toBe(false);
    expect(note().value).toBe("remember me"); // saved value stays
    expect(tabs()).toBeNull();
    await act(async () => root.unmount());
  });

  it("asks before closing a place that holds a draft, and says what is lost", async () => {
    const { root } = await mount();
    await click(link("to participants"));
    await type("keep");
    await click(button("×"));
    expect(document.querySelector('[role="dialog"]')?.textContent).toContain(
      "Event note",
    );
    await click(button("Keep editing"));
    expect(hasDrafts()).toBe(true);
    await click(button("×"));
    await click(button("Discard and close"));
    expect(hasDrafts()).toBe(false);
    expect(tabs()).toBeNull();
    await act(async () => root.unmount());
  });

  it("asks before signing out with a draft and discards it only on yes; nothing typed reaches storage", async () => {
    const signOut = vi.fn();
    const { root } = await mount(signOut);
    await click(link("to participants"));
    await type("secret text");
    expect(JSON.stringify(Object.entries(window.localStorage))).not.toContain(
      "secret",
    );
    await click(document.querySelector("details.cx-account summary")!);
    await click(button("Sign out"));
    expect(signOut).not.toHaveBeenCalled();
    await click(button("Keep editing"));
    await click(button("Sign out"));
    await click(button("Discard and sign out"));
    expect(signOut).toHaveBeenCalledOnce();
    expect(hasDrafts()).toBe(false);
    await act(async () => root.unmount());
  });

  it("keeps only well-formed router targets in the stored tab list", () => {
    window.localStorage.setItem(
      "conflux:v1:u1:w:tabs",
      JSON.stringify([
        "/w/w/participants?event=e1",
        "https://evil.example/",
        "/w/w/<script>",
        42,
        "/w/w/judging?event=e1&stage=s1",
      ]),
    );
    expect(workspaceTabs("u1", "w")).toEqual([
      "/w/w/participants?event=e1",
      "/w/w/judging?event=e1&stage=s1",
    ]);
  });
});
