// @vitest-environment happy-dom
import { act, useState } from "react";
import { createRoot } from "react-dom/client";
import { useLocation } from "react-router";
import { afterEach, describe, expect, it, vi } from "vitest";
import { jsonResponse } from "../lib/test-http";
import { withRouter } from "../lib/test-router";
import type { SavedView, ViewDefinition } from "../lib/savedViews";
import { togglePinnedView } from "../lib/shellPreferences";
import { ViewBar } from "./ViewBar";
(
  globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }
).IS_REACT_ACT_ENVIRONMENT = true;
afterEach(() => vi.unstubAllGlobals());

const PENDING: ViewDefinition = {
  filter: { field: "status", op: "eq", value: "pending" },
  sort: "-created_at",
  columns: ["username"],
  density: "compact",
};
const view = (over: Partial<SavedView>): SavedView => ({
  public_id: "11111111-1111-4111-8111-111111111111",
  entity: "applications",
  name: "Pending",
  query: PENDING,
  visibility: "private",
  version: 1,
  owner: "ana",
  mine: true,
  updated_at: "2027-03-01T00:00:00Z",
  ...over,
});
const SHARED = view({
  public_id: "22222222-2222-4222-8222-222222222222",
  name: "Waiting",
  owner: "bo",
  mine: false,
  visibility: "organizers",
});

type Call = { url: string; method: string; body: unknown };

async function mount(
  initial: SavedView[],
  options: { url?: string; current?: ViewDefinition; conflict?: boolean } = {},
) {
  let views = initial;
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: unknown, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      const body = init?.body ? JSON.parse(String(init.body)) : undefined;
      calls.push({ url, method, body });
      if (url.includes("/accounts/me/"))
        return jsonResponse(200, { public_id: "u1", memberships: [] });
      if (method === "PATCH" && options.conflict) {
        options.conflict = false;
        views = views.map((v) => ({ ...v, version: v.version + 1 })); // someone else saved
        return jsonResponse(409, {
          code: "view_changed",
          detail:
            "This view changed since you loaded it; reload it and apply again.",
        });
      }
      if (method === "GET") return jsonResponse(200, views);
      if (method === "POST") {
        const created = view({
          public_id: "33333333-3333-4333-8333-333333333333",
          name: body.name,
          query: body.query,
        });
        views = [...views, created];
        return jsonResponse(201, created);
      }
      if (method === "PATCH") {
        const id = url.split("/").filter(Boolean).pop()!;
        views = views.map((v) =>
          v.public_id === id ? { ...v, ...body, version: v.version + 1 } : v,
        );
        return jsonResponse(
          200,
          views.find((v) => v.public_id === id)!,
        );
      }
      const id = url.split("/").filter(Boolean).pop()!;
      views = views.filter((v) => v.public_id !== id);
      return new Response(null, { status: 204 });
    }),
  );
  const applied: (SavedView | null)[] = [];
  const searches: string[] = [];
  function Host() {
    const [current] = useState(options.current ?? PENDING);
    searches.push(useLocation().search);
    return (
      <ViewBar
        workspaceId="w"
        eventId="e"
        entity="applications"
        current={current}
        onApply={(v) => applied.push(v)}
      />
    );
  }
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root = createRoot(container);
  await act(async () =>
    root.render(withRouter(<Host />, options.url ?? "/w/w/setup")),
  );
  await act(async () => new Promise((resolve) => setTimeout(resolve, 0)));
  return { container, calls, applied, searches, root };
}
const button = (c: HTMLElement, text: string) =>
  [...c.querySelectorAll("button")].find((b) => b.textContent === text);
const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));
const type = (el: HTMLInputElement, value: string) => {
  Object.getOwnPropertyDescriptor(
    HTMLInputElement.prototype,
    "value",
  )?.set?.call(el, value);
  el.dispatchEvent(new Event("input", { bubbles: true }));
};

describe("ViewBar", () => {
  it("lists my views and shared ones separately and applies the chosen one", async () => {
    const { container, applied, root } = await mount([view({}), SHARED]);
    const select = container.querySelector("select")!;
    expect(
      [...select.querySelectorAll("optgroup")].map((g) =>
        g.getAttribute("label"),
      ),
    ).toEqual(["My views", "Shared by organizers"]);
    expect(select.textContent).toContain("Waiting (bo)");
    await act(async () => {
      select.value = SHARED.public_id;
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    expect(applied.at(-1)?.name).toBe("Waiting");
    // A shared view is not mine: no Save, Rename, share toggle or Delete; Copy link is offered.
    expect(button(container, "Save")).toBeUndefined();
    expect(button(container, "Delete view")).toBeUndefined();
    expect(button(container, "Copy link")).toBeDefined();
    expect(container.textContent).toContain("Shared by bo");
    await act(async () => root.unmount());
  });

  it("lists the pinned views first, only while they still exist", async () => {
    window.localStorage.clear();
    const pinned = view({});
    togglePinnedView("u1", "w", {
      event: "e",
      entity: "applications",
      view: pinned.public_id,
    });
    togglePinnedView("u1", "w", {
      event: "e",
      entity: "applications",
      view: "99999999-9999-4999-8999-999999999999", // deleted since: not shown
    });
    const { container, root } = await mount([pinned, SHARED]);
    const groups = [...container.querySelectorAll("optgroup")].map((g) =>
      g.getAttribute("label"),
    );
    expect(groups).toEqual(["Pinned", "My views", "Shared by organizers"]);
    expect(
      container.querySelector('optgroup[label="Pinned"]')?.textContent,
    ).toBe("Pending");
    await act(async () => root.unmount());
    window.localStorage.clear();
  });

  it("opens the view named in the URL and drops an id that is not in the list", async () => {
    const opened = await mount([view({})], {
      url: `/w/w/setup?view_applications=${view({}).public_id}`,
    });
    expect(opened.applied.at(-1)?.name).toBe("Pending");
    await act(async () => opened.root.unmount());

    const stray = await mount([view({})], {
      url: "/w/w/setup?view_applications=99999999-9999-4999-8999-999999999999",
    });
    expect(stray.applied).toEqual([]);
    expect(stray.container.querySelector("select")!.value).toBe("");
    await act(async () => stray.root.unmount());
  });

  it("says when the list differs from the saved view and saves the change with the version", async () => {
    const { container, calls, root } = await mount([view({})], {
      url: `/w/w/setup?view_applications=${view({}).public_id}`,
      current: { ...PENDING, sort: "username" },
    });
    expect(container.textContent).toContain("Changed since saved");
    await act(async () => button(container, "Save")!.click());
    await settle();
    const patch = calls.find((c) => c.method === "PATCH")!;
    expect(patch.body).toMatchObject({
      version: 1,
      query: { sort: "username" },
    });
    expect(container.textContent).toContain("View saved.");
    await act(async () => root.unmount());
  });

  it("offers Reset only while changed, applies the saved definition again, and says who can see the view", async () => {
    const changed = await mount([view({})], {
      url: `/w/w/setup?view_applications=${view({}).public_id}`,
      current: { ...PENDING, sort: "username" },
    });
    expect(changed.container.textContent).toContain("Private to you.");
    const before = changed.applied.length;
    await act(async () => button(changed.container, "Reset")!.click());
    expect(changed.applied.length).toBe(before + 1);
    expect(changed.applied.at(-1)?.name).toBe("Pending"); // the list goes back to the saved view
    await act(async () => changed.root.unmount());

    const same = await mount([view({ visibility: "organizers" })], {
      url: `/w/w/setup?view_applications=${view({}).public_id}`,
    });
    expect(button(same.container, "Reset")).toBeUndefined();
    expect(same.container.textContent).toContain("Visible to every organizer.");
    await act(async () => same.root.unmount());
  });

  it("reloads a view that changed under the person, says so, and the next save carries the new version", async () => {
    const { container, calls, root } = await mount([view({})], {
      url: `/w/w/setup?view_applications=${view({}).public_id}`,
      current: { ...PENDING, sort: "username" },
      conflict: true,
    });
    await act(async () => button(container, "Save")!.click());
    await settle();
    expect(container.textContent).toContain(
      "This view changed since you loaded it",
    );
    await settle();
    await act(async () => button(container, "Save")!.click());
    await settle();
    const patches = calls.filter((c) => c.method === "PATCH");
    expect(patches.map((c) => (c.body as { version: number }).version)).toEqual(
      [1, 2],
    );
    await act(async () => root.unmount());
  });

  it("saves the current list as a new named view", async () => {
    const { container, calls, applied, searches, root } = await mount([]);
    await act(async () => button(container, "Save as new view")!.click());
    expect(button(container, "Save view")!.disabled).toBe(true);
    await act(async () =>
      type(
        container.querySelector<HTMLInputElement>("form input")!,
        "Pending first",
      ),
    );
    await act(async () => button(container, "Save view")!.click());
    await settle();
    const post = calls.find((c) => c.method === "POST")!;
    expect(post.body).toEqual({
      entity: "applications",
      name: "Pending first",
      query: PENDING,
    });
    expect(container.textContent).toContain("View saved.");
    expect(applied).toEqual([]); // the list already shows this definition; nothing to apply twice
    // The URL names the new view and keeps naming it once the list has reloaded.
    await settle();
    await settle();
    expect(searches.at(-1)).toBe(
      "?view_applications=33333333-3333-4333-8333-333333333333",
    );
    expect(container.querySelector("select")!.value).toBe(
      "33333333-3333-4333-8333-333333333333",
    );
    await act(async () => root.unmount());
  });

  it("shares a view, renames it, and deletes it with the consequence stated", async () => {
    const { container, calls, root } = await mount([view({})], {
      url: `/w/w/setup?view_applications=${view({}).public_id}`,
    });
    await act(async () =>
      container
        .querySelector<HTMLInputElement>("input[type=checkbox]")!
        .click(),
    );
    await settle();
    expect(calls.find((c) => c.method === "PATCH")!.body).toMatchObject({
      visibility: "organizers",
    });
    expect(container.textContent).toContain("Shared with organizers.");

    await act(async () => button(container, "Rename")!.click());
    await act(async () =>
      type(
        container.querySelector<HTMLInputElement>("form input")!,
        "Waiting list",
      ),
    );
    await act(async () => button(container, "Rename view")!.click());
    await settle();
    expect(
      calls.filter((c) => c.method === "PATCH").at(-1)!.body,
    ).toMatchObject({
      name: "Waiting list",
    });

    await act(async () => button(container, "Delete view")!.click());
    const dialog = container.querySelector("[role=alertdialog]")!;
    expect(dialog.textContent).toContain(
      "Organizers it was shared with lose it.",
    );
    expect(dialog.textContent).toContain("The data it shows is not touched.");
    await act(async () => button(container, "Delete “Waiting list”")!.click());
    await settle();
    expect(calls.some((c) => c.method === "DELETE")).toBe(true);
    expect(container.textContent).toContain("View deleted.");
    await act(async () => root.unmount());
  });

  it("shows a server refusal without losing the work, and a failed load with a retry", async () => {
    const { container, root } = await mount([view({})], {
      url: `/w/w/setup?view_applications=${view({}).public_id}`,
      current: { ...PENDING, sort: "username" },
    });
    // only the save is refused; the list of views still loads (the bar reloads it after a 409)
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: unknown, init?: RequestInit) => {
        if (String(input).includes("/accounts/me/"))
          return jsonResponse(200, { public_id: "u1", memberships: [] });
        return (init?.method ?? "GET") === "PATCH"
          ? jsonResponse(409, {
              code: "view_changed",
              detail: "This view changed since you loaded it.",
            })
          : jsonResponse(200, [view({})]);
      }),
    );
    await act(async () => button(container, "Save")!.click());
    await settle();
    expect(container.querySelector("[role=alert]")?.textContent).toContain(
      "changed since you loaded",
    );
    expect(container.textContent).toContain("Changed since saved");
    await act(async () => root.unmount());

    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse(500, { detail: "Boom" })),
    );
    const failed = document.createElement("div");
    document.body.appendChild(failed);
    const failedRoot = createRoot(failed);
    await act(async () =>
      failedRoot.render(
        withRouter(
          <ViewBar
            workspaceId="w"
            eventId="e"
            entity="applications"
            current={PENDING}
            onApply={() => {}}
          />,
        ),
      ),
    );
    await settle();
    expect(failed.textContent).toContain("Try again");
    await act(async () => failedRoot.unmount());
  });
});
