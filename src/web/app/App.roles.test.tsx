// @vitest-environment happy-dom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import { createTestQueryClient } from "../lib/test-router";
import { jsonResponse } from "../lib/test-http";

(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;

let container: HTMLDivElement;
let root: Root;
beforeEach(() => {
  window.localStorage.clear();
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});
afterEach(() => {
  act(() => root.unmount());
  container.remove();
  vi.unstubAllGlobals();
});

const me = (roles: string[]) => ({
  public_id: "u1",
  username: "pat",
  memberships: roles.map((role) => ({
    workspace: "w",
    workspace_name: "Lab",
    workspace_slug: "lab",
    role,
  })),
});

async function render(url: string, roles: string[]) {
  window.history.replaceState({}, "", url);
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown) =>
      String(input).includes("/accounts/me/")
        ? jsonResponse(200, me(roles))
        : jsonResponse(200, []),
    ),
  );
  await act(async () =>
    root.render(<App queryClient={createTestQueryClient()} />),
  );
  for (
    let i = 0;
    i < 100 && !container.querySelector(".cx-shell--workspace");
    i++
  )
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
    });
}
const context = () =>
  container.querySelector(".cx-shell__context")?.textContent;
const railLabels = () =>
  [
    ...container.querySelectorAll("#workspace-navigation .cx-sidebar__link"),
  ].map((a) => a.textContent);
const roleLinks = () =>
  [...container.querySelectorAll(".cx-account__roles a")].map((a) => [
    a.textContent,
    a.getAttribute("href"),
    a.getAttribute("aria-current"),
  ]);

describe("viewing a workspace as one of several roles", () => {
  it("shows the most privileged role by default and says so", async () => {
    await render("/w/w/overview", ["participant", "judge"]);
    expect(context()).toBe("Lab · viewing as judge");
    expect(railLabels()).toContain("Review queue"); // the judge's screen
    expect(roleLinks()).toEqual([
      ["Judge", "/w/w/overview?as=judge", "true"],
      ["Participant", "/w/w/overview?as=participant", null],
    ]);
  });

  it("views as another role the person holds when `as` asks for it, and keeps it between views", async () => {
    await render("/w/w/overview?event=e1&as=participant", [
      "participant",
      "judge",
    ]);
    expect(context()).toBe("Lab · viewing as participant");
    expect(railLabels()).toContain("Team");
    expect(railLabels()).not.toContain("Review queue");
    const links = [
      ...container.querySelectorAll<HTMLAnchorElement>(
        "#workspace-navigation a",
      ),
    ];
    expect(
      links.every((a) => a.getAttribute("href")!.includes("as=participant")),
    ).toBe(true);
    // choosing the other role keeps the event
    expect(roleLinks()[0][1]).toBe("/w/w/overview?event=e1&as=judge");
  });

  it("drops a role the person does not hold from the URL instead of showing it", async () => {
    await render("/w/w/judging?as=organizer", ["participant", "judge"]);
    expect(window.location.search).toBe("");
    expect(railLabels()).toContain("Review queue");
    expect(window.location.pathname).toBe("/w/w/overview"); // judging is not a judge place
  });

  it("says nothing special for a person with one role, and a hand-edited value never breaks a link", async () => {
    await render("/w/w/overview?event=%3Cb%3E&as=judge", ["judge"]);
    expect(context()).toBe("Lab · judge");
    expect(container.querySelector(".cx-account__roles")).toBeNull();
    const first = container.querySelector<HTMLAnchorElement>(
      "#workspace-navigation a",
    )!;
    expect(first.getAttribute("href")).not.toContain("%3C"); // the unsafe event is dropped, not carried
  });
});
